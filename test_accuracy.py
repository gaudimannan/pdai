import torch
import torch.nn as nn
from torchvision import datasets, transforms, models
from torchvision.models import efficientnet_b0, EfficientNet_B0_Weights
from torch.utils.data import DataLoader
import os
import argparse

# Configuration (defaults)
DATA_DIR = 'data/'
DEFAULT_BATCH_SIZE = 32
NUM_WORKERS = 0
IMG_SIZE = 224
MODEL_PATH = 'best_model.pth'

def main():
    parser = argparse.ArgumentParser(description='Test model accuracy.')
    parser.add_argument('--limit', type=int, default=None, help='Limit number of samples to test')
    parser.add_argument('--batch-size', type=int, default=DEFAULT_BATCH_SIZE, help='Batch size')
    args = parser.parse_args()

    device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')
    print(f"Using device: {device}")
    if device.type == 'cuda':
        print(f"GPU: {torch.cuda.get_device_name(0)}")

    # Data transforms
    test_transforms = transforms.Compose([
        transforms.Resize((IMG_SIZE, IMG_SIZE)),
        transforms.ToTensor(),
        transforms.Normalize([0.485, 0.456, 0.406], [0.229, 0.224, 0.225])
    ])

    print("Loading dataset...")
    dataset = datasets.ImageFolder(DATA_DIR, transform=test_transforms)
    
    # Apply limit if specified
    if args.limit:
        indices = torch.arange(args.limit)
        dataset = torch.utils.data.Subset(dataset, indices)
        print(f"Limiting to first {args.limit} samples.")

    dataloader = DataLoader(dataset, batch_size=args.batch_size, shuffle=False, num_workers=NUM_WORKERS)
    print(f"Dataset loaded. Found {len(dataset)} images.")

    print(f"Loading model from {MODEL_PATH}...")
    if not os.path.exists(MODEL_PATH):
        print(f"Error: Model file {MODEL_PATH} not found.")
        return

    checkpoint = torch.load(MODEL_PATH, map_location=device)
    
    if isinstance(checkpoint, dict) and 'class_names' in checkpoint:
        class_names = checkpoint['class_names']
        state_dict = checkpoint['model_state_dict']
    else:
        print("Warning: Could not find 'class_names' in checkpoint. Inferring from dataset.")
        # If we are using a Subset, we need to get classes from the underlying dataset
        full_dataset = dataset.dataset if isinstance(dataset, torch.utils.data.Subset) else dataset
        class_names = full_dataset.classes
        state_dict = checkpoint if not 'model_state_dict' in checkpoint else checkpoint['model_state_dict']

    num_classes = len(class_names)
    print(f"Model has {num_classes} classes: {class_names}")

    model = efficientnet_b0(weights=None)
    model.classifier[1] = nn.Linear(model.classifier[1].in_features, num_classes)
    
    model.load_state_dict(state_dict)
    model.to(device)
    model.eval()

    print("Starting evaluation...")
    running_corrects = 0
    total_samples = 0
    
    class_correct = dict.fromkeys(range(num_classes), 0)
    class_total = dict.fromkeys(range(num_classes), 0)

    with torch.no_grad():
        for i, (inputs, labels) in enumerate(dataloader):
            if i % 10 == 0:
                print(f"Processing batch {i+1}/{len(dataloader)}")
            
            inputs = inputs.to(device)
            labels = labels.to(device)

            outputs = model(inputs)
            _, preds = torch.max(outputs, 1)

            running_corrects += torch.sum(preds == labels.data)
            total_samples += labels.size(0)
            
            for label, pred in zip(labels, preds):
                if label == pred:
                    class_correct[label.item()] += 1
                class_total[label.item()] += 1

    overall_acc = running_corrects.double() / total_samples
    print(f"\nEvaluation Complete.")
    print(f"Overall Accuracy: {overall_acc:.4f} ({running_corrects}/{total_samples})")
    
    print("\nPer-class Accuracy:")
    for i in range(num_classes):
        if class_total[i] > 0:
            acc = 100 * class_correct[i] / class_total[i]
            print(f"{class_names[i]}: {acc:.2f}% ({class_correct[i]}/{class_total[i]})")
        else:
            # Only print N/A if verbose, or just skip
             pass # keeping it clean


if __name__ == '__main__':
    main()
