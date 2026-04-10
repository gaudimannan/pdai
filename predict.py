import torch
from torchvision import transforms, models
from PIL import Image

# MODEL_PATH = 'best_model.pth'
IMG_SIZE = 224

class_names = []

def load_model(model_path):
    checkpoint = torch.load(model_path, map_location='cpu')
    global class_names
    class_names = checkpoint['class_names']
    num_classes = len(class_names)
    model = models.efficientnet_b0(weights=None)
    model.classifier[1] = torch.nn.Linear(model.classifier[1].in_features, num_classes)
    model.load_state_dict(checkpoint['model_state_dict'])
    model.eval()
    return model

def predict(image_path, model):
    transform = transforms.Compose([
        transforms.Resize((IMG_SIZE, IMG_SIZE)),
        transforms.ToTensor(),
        transforms.Normalize([0.485, 0.456, 0.406], [0.229, 0.224, 0.225])
    ])
    img = Image.open(image_path).convert('RGB')
    img_tensor = transform(img).unsqueeze(0)
    with torch.no_grad():
        outputs = model(img_tensor)
        _, pred = torch.max(outputs, 1)
    return class_names[pred.item()]

if __name__ == '__main__':
    import sys
    if len(sys.argv) != 2:
        print('Usage: python predict.py <image_path>')
        exit(1)
    image_path = sys.argv[1]
    model = load_model('best_model.pth')
    prediction = predict(image_path, model)
    print()
    print()
    print(f'Predicted Class: {prediction}')