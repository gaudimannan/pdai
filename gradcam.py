import torch
from pathlib import Path
import numpy as np
import cv2
from torchvision import transforms
from PIL import Image

def generate_gradcam(model, image_input, class_names, target_layer_name=None):
    """
    Generate a Grad-CAM heatmap for an input image and a PyTorch model.
    Args:
        model: Trained PyTorch model (EfficientNet)
        image_input: Path to input image OR PIL Image object
        class_names: List of class names
        target_layer_name: Name of the layer to use for Grad-CAM (default: last conv layer)
    Returns:
        heatmap_on_image (PIL Image): The original image with heatmap overlay
        pred_class (str): Predicted class name
    """
    model.eval()
    device = next(model.parameters()).device
    # Preprocess image
    preprocess = transforms.Compose([
        transforms.Resize((224, 224)),
        transforms.ToTensor(),
        transforms.Normalize([0.485, 0.456, 0.406], [0.229, 0.224, 0.225])
    ])
    
    if isinstance(image_input, str) or isinstance(image_input, Path):
        img = Image.open(image_input).convert('RGB')
    else:
        img = image_input.convert('RGB')
        
    input_tensor = preprocess(img).unsqueeze(0).to(device)
    # Forward pass
    outputs = model(input_tensor)
    pred_idx = outputs.argmax(dim=1).item()
    pred_class = class_names[pred_idx]
    # Find target layer
    if target_layer_name is None:
        # EfficientNet last conv layer
        target_layer = model.features[-1][0]
    else:
        target_layer = dict([*model.named_modules()])[target_layer_name]
    # Register hooks
    activations = []
    gradients = []
    def forward_hook(module, input, output):
        activations.append(output)
    def backward_hook(module, grad_in, grad_out):
        gradients.append(grad_out[0])
    fh = target_layer.register_forward_hook(forward_hook)
    bh = target_layer.register_backward_hook(backward_hook)
    # Backward pass for predicted class
    model.zero_grad()
    class_score = outputs[0, pred_idx]
    class_score.backward()
    # Get activations and gradients
    acts = activations[0].detach().cpu().numpy()[0]
    grads = gradients[0].detach().cpu().numpy()[0]
    # Compute weights and Grad-CAM
    weights = grads.mean(axis=(1, 2))
    cam = np.zeros(acts.shape[1:], dtype=np.float32)
    for i, w in enumerate(weights):
        cam += w * acts[i]
    cam = np.maximum(cam, 0)
    cam = cv2.resize(cam, (224, 224))
    cam -= cam.min()
    cam /= cam.max() if cam.max() != 0 else 1
    # Overlay heatmap on image
    img_np = np.array(img.resize((224, 224)))
    heatmap = (cam * 255).astype(np.uint8)
    heatmap = cv2.applyColorMap(heatmap, cv2.COLORMAP_JET)
    overlay = cv2.addWeighted(img_np, 0.6, heatmap, 0.4, 0)
    heatmap_on_image = Image.fromarray(overlay)
    # Remove hooks
    fh.remove()
    bh.remove()
    return heatmap_on_image, pred_class
