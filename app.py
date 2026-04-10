from pathlib import Path
import base64
import io

from flask import Flask, flash, redirect, render_template, request, url_for, jsonify
from flask_cors import CORS
from PIL import Image, UnidentifiedImageError
import torch
import torch.nn as nn
import torch.nn.functional as F
from torchvision import transforms
from torchvision.models import efficientnet_b0
import pickle
import requests

MODEL_PATH = Path("best_model.pth")
IMG_SIZE = 224
ALLOWED_EXTENSIONS = {"png", "jpg", "jpeg", "bmp"}

app = Flask(__name__)
app.config["SECRET_KEY"] = "leaf-disease-secret"
CORS(app)


def load_model(model_path: Path):
    if not model_path.exists():
        raise FileNotFoundError(f"Model file not found at {model_path.resolve()}")
    checkpoint = torch.load(model_path, map_location="cpu")
    class_names = checkpoint["class_names"]
    model = efficientnet_b0(weights=None)
    model.classifier[1] = nn.Linear(model.classifier[1].in_features, len(class_names))
    model.load_state_dict(checkpoint["model_state_dict"])
    model.eval()
    return model, class_names


model, class_names = load_model(MODEL_PATH)

transform = transforms.Compose([
    transforms.Resize((IMG_SIZE, IMG_SIZE)),
    transforms.ToTensor(),
    transforms.Normalize([0.485, 0.456, 0.406], [0.229, 0.224, 0.225]),
])


def allowed_file(filename: str) -> bool:
    return "." in filename and filename.rsplit(".", 1)[1].lower() in ALLOWED_EXTENSIONS


def parse_label(label: str):
    parts = label.split("___")
    plant_type = parts[0].replace("__", " ")
    disease = parts[1].replace("__", " ") if len(parts) > 1 else "Unknown"
    is_healthy = disease.strip().lower() in {"healthy", "healthy leaf"}
    return plant_type, disease if not is_healthy else "Healthy", is_healthy


def predict_image(image: Image.Image):
    tensor = transform(image).unsqueeze(0)
    with torch.no_grad():
        outputs = model(tensor)
        probs = F.softmax(outputs, dim=1)
        confidence, pred_idx = torch.max(probs, 1)
    label = class_names[pred_idx.item()]
    return label, float(confidence.item())

# Load Crop Recommendation Model
try:
    with open("crop_recommender.pkl", "rb") as f:
        crop_model = pickle.load(f)
except FileNotFoundError:
    crop_model = None
    print("Warning: crop_recommender.pkl not found. Crop recommendation will fail.")


def get_coordinates(city_name):
    """Fetch lat, lon for a city using Nominatim API."""
    try:
        url = "https://nominatim.openstreetmap.org/search"
        # Using a more browser-like User-Agent as proven in debug script
        headers = {'User-Agent': 'Mozilla/5.0 (compatible; CropRecommender/1.0; +http://localhost)'}
        params = {'q': city_name, 'format': 'json', 'limit': 1}
        response = requests.get(url, headers=headers, params=params, timeout=5)
        response.raise_for_status()
        data = response.json()
        if data:
            return float(data[0]['lat']), float(data[0]['lon'])
    except Exception as e:
        print(f"Error fetching coordinates: {e}")
    return None, None


def get_weather(lat, lon):
    """Fetch Temp, Humidity, Rainfall from OpenMeteo."""
    try:
        url = "https://api.open-meteo.com/v1/forecast"
        params = {
            "latitude": lat,
            "longitude": lon,
            "current": "temperature_2m,relative_humidity_2m,rain",
            "timezone": "auto" # Use local timezone
        }
        response = requests.get(url, params=params, timeout=5)
        response.raise_for_status()
        data = response.json()
        current = data.get('current', {})
        print(f"Weather Data: {current}")
        return {
            'temperature': current.get('temperature_2m', 25.0), # Fallback defaults
            'humidity': current.get('relative_humidity_2m', 70),
            'rainfall': current.get('rain', 0.0) * 100 # Approx conversion if needed, but model might need annual. 
            # NOTE: OpenMeteo gives current rain. Crop model assumes annual/seasonal averages usually.
            # For this demo, we'll try using what we get, but rainfall might be 0 most days.
            # A better approach for rainfall: use historical average or just specific large value if raining.
            # OPTION: Just accept that for a real app we need seasonal weather API.
            # For this MVP: If rain is 0, we might want to assume some irrigation or use a simplistic fallback?
            # actually, let's just pass what we get.
        }
    except Exception as e:
        print(f"Error fetching weather: {e}")
        return {'temperature': 25.0, 'humidity': 70, 'rainfall': 100.0} # Fallback reasonable avg

def get_location_name(lat, lon):
    """Reverse geocode lat/lon to get a readable address."""
    try:
        url = "https://nominatim.openstreetmap.org/reverse"
        headers = {'User-Agent': 'Mozilla/5.0 (compatible; PDD_App/1.0; +http://localhost)'}
        params = {'lat': lat, 'lon': lon, 'format': 'json', 'zoom': 10}
        response = requests.get(url, headers=headers, params=params, timeout=5)
        response.raise_for_status()
        data = response.json()
        address = data.get('address', {})
        # Try to construct a readable location string
        parts = [
            address.get('city') or address.get('town') or address.get('village'),
            address.get('state'),
            address.get('country')
        ]
        return ", ".join([p for p in parts if p]) or f"{lat:.2f}, {lon:.2f}"
    except Exception as e:
        print(f"Error reverse geocoding: {e}")
        return f"{lat:.2f}, {lon:.2f}"

from gradcam import generate_gradcam

# ... (existing imports and setup)

@app.route("/", methods=["GET", "POST"])
def index():
    if request.method == "POST":
        file = request.files.get("image")
        if not file or file.filename == "":
            flash("Please choose an image to upload.")
            return redirect(url_for("index"))
        if not allowed_file(file.filename):
            flash("Unsupported file type. Please upload PNG, JPG, or BMP images.")
            return redirect(url_for("index"))
        try:
            image_bytes = file.read()
            image = Image.open(io.BytesIO(image_bytes)).convert("RGB")
            
            # Encode for display - ORIGINAL
            image_b64 = base64.b64encode(image_bytes).decode('utf-8')
            image_src = f"data:{file.content_type};base64,{image_b64}"
            
        except (UnidentifiedImageError, OSError):
            flash("Unable to open the uploaded file as an image. Try another file.")
            return redirect(url_for("index"))

        label, confidence = predict_image(image)
        plant_type, disease, is_healthy = parse_label(label)
        
        # Generate Grad-CAM Heatmap
        heatmap_src = None
        if not is_healthy: # Only generate heatmap if diseased
            try:
                heatmap_img, _ = generate_gradcam(model, image, class_names)
                # Convert heatmap to base64
                buf = io.BytesIO()
                heatmap_img.save(buf, format="JPEG")
                heatmap_b64 = base64.b64encode(buf.getvalue()).decode('utf-8')
                heatmap_src = f"data:image/jpeg;base64,{heatmap_b64}"
            except Exception as e:
                print(f"Error generating Grad-CAM: {e}")

        result = {
            "plant_type": plant_type,
            "status": "Healthy" if is_healthy else "Diseased",
            "disease": None if is_healthy else disease,
            "confidence": f"{confidence * 100:.2f}%",
            "image_src": image_src,
            "heatmap_src": heatmap_src
        }
        return render_template("index.html", result=result, type="disease")

    return render_template("index.html", result=None, type="disease")

@app.route("/api/predict", methods=["POST"])
def api_predict():
    file = request.files.get("image")
    if not file or file.filename == "":
        return jsonify({"error": "No image uploaded"}), 400
    
    try:
        image_bytes = file.read()
        image = Image.open(io.BytesIO(image_bytes)).convert("RGB")
        
        label, confidence = predict_image(image)
        plant_type, disease, is_healthy = parse_label(label)
        
        # Treatment logic (extracted from original template logic or simplified)
        # In a real app, these should be in a database or a mapping file
        organic = "Continue regular maintenance. Ensure proper watering and sunlight. No treatments needed." if is_healthy else "Remove infected leaves immediately. Apply a copper-based fungicide or use a baking soda solution."
        chemical = "No chemical pesticides required. Maintain soil health with organic compost." if is_healthy else "Apply fungicides containing chlorothalonil or mancozeb. Ensure thorough coverage of foliage."
        
        return jsonify({
            "type": "healthy" if is_healthy else "diseased",
            "issue": f"{plant_type} - {disease}" if not is_healthy else "Healthy Leaf",
            "confidence": f"{confidence * 100:.1f}%",
            "severity": "High" if not is_healthy and confidence > 0.8 else ("Medium" if not is_healthy else "None"),
            "statusText": "HEALTHY" if is_healthy else ("SEVERE" if confidence > 0.8 else "CAUTION"),
            "organic": organic,
            "chemical": chemical
        })
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route("/api/recommend", methods=["POST"])
def api_recommend():
    if not crop_model:
        return jsonify({"error": "Model not loaded"}), 500
    
    data = request.json
    try:
        # Example features: [temperature, humidity, rainfall]
        # These would ideally come from the request or be derived from location as in the original app
        # For simplicity, if they aren't provided, use defaults
        temp = data.get('temperature', 25.0)
        humidity = data.get('humidity', 70.0)
        rainfall = data.get('rainfall', 100.0)
        
        features = [[temp, humidity, rainfall]]
        
        probs = crop_model.predict_proba(features)[0]
        top_3_indices = probs.argsort()[-3:][::-1]
        top_crops = []
        
        for idx in top_3_indices:
            crop_name = crop_model.classes_[idx]
            probability = probs[idx]
            if probability > 0.05:
                top_crops.append({
                    "name": crop_name,
                    "scientificName": "Scientific Name Placeholder", # Add mapping if available
                    "score": f"{probability*100:.1f}%",
                    "description": f"{crop_name} is recommended based on your soil profile.",
                    "suitability": "Kharif/Rabi",
                    "yield": "TBD"
                })
        
        return jsonify({"crops": top_crops})
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route("/recommend", methods=["POST"])
def recommend():
    if not crop_model:
        flash("Crop recommendation model is not loaded.")
        return redirect(url_for("index"))

    city = request.form.get("city")
    lat_str = request.form.get("lat")
    lon_str = request.form.get("lon")

    lat, lon = None, None
    location_display = city

    # Prioritize Geolocated Lat/Lon
    if lat_str and lon_str:
        try:
            lat, lon = float(lat_str), float(lon_str)
            if not city or "My Location" in city:
                 location_display = get_location_name(lat, lon)
        except ValueError:
            pass
    
    if (lat is None or lon is None) and city:
        lat, lon = get_coordinates(city)
        if not location_display:
            location_display = city

    if lat is None or lon is None:
        flash("Could not determine location. Please try again.")
        return redirect(url_for("index"))

    weather = get_weather(lat, lon)
    
    features = [[
        weather['temperature'],
        weather['humidity'],
        weather['rainfall'] if weather['rainfall'] > 0 else 100.0 
    ]]
    
    # Get Top 3 Predictions
    probs = crop_model.predict_proba(features)[0]
    top_3_indices = probs.argsort()[-3:][::-1]
    top_crops = []
    
    for idx in top_3_indices:
        crop_name = crop_model.classes_[idx]
        probability = probs[idx]
        if probability > 0.05: # Only show relevant ones
            top_crops.append({"name": crop_name, "prob": f"{probability*100:.1f}%"})

    if not top_crops:
         # Fallback if probability is weirdly low (shouldn't happen with softmax)
         top_crops.append({"name": crop_model.predict(features)[0], "prob": "High"})

    result = {
        "crops": top_crops, # List of dicts
        "weather": weather,
        "location": location_display
    }
    
    return render_template("index.html", result=result, type="crop")

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=False)
