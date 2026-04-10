import pandas as pd
import pickle
from sklearn.model_selection import train_test_split
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import accuracy_score

# Load the dataset
data = pd.read_csv("data/Crop_recommendation.csv")

# Feature Selection: Use ONLY Weather data (Temperature, Humidity, Rainfall)
# This allows us to make predictions without asking the user for complex soil data.
X = data[['temperature', 'humidity', 'rainfall']]
y = data['label']

# Split Data
X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)

# Train Model (Random Forest is robust for this)
print("Training Random Forest Model...")
model = RandomForestClassifier(n_estimators=100, random_state=42)
model.fit(X_train, y_train)

# Evaluate
y_pred = model.predict(X_test)
accuracy = accuracy_score(y_test, y_pred)
print(f"Model Accuracy: {accuracy:.4f}")

# Save Model
with open("crop_recommender.pkl", "wb") as f:
    pickle.dump(model, f)
print("Model saved to crop_recommender.pkl")
