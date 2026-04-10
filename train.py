import os
import copy
import torch
import torch.nn as nn
import torch.optim as optim
from torch.utils.data import DataLoader, random_split
from torchvision import datasets, transforms, models
from torchvision.models import efficientnet_b0, EfficientNet_B0_Weights

DATA_DIR = 'data/'
BATCH_SIZE = 32
NUM_WORKERS = 0
IMG_SIZE = 224
NUM_EPOCHS = 20
LEARNING_RATE = 1e-4
MODEL_PATH = 'best_model.pth'

train_transforms = transforms.Compose([
    transforms.Resize((IMG_SIZE, IMG_SIZE)),
    transforms.RandomHorizontalFlip(),
    transforms.RandomRotation(20),
    transforms.ColorJitter(brightness=0.1, contrast=0.1, saturation=0.1, hue=0.05),
    transforms.ToTensor(),
    transforms.Normalize([0.485, 0.456, 0.406], [0.229, 0.224, 0.225])
])
val_transforms = transforms.Compose([
    transforms.Resize((IMG_SIZE, IMG_SIZE)),
    transforms.ToTensor(),
    transforms.Normalize([0.485, 0.456, 0.406], [0.229, 0.224, 0.225])
])

if __name__ == '__main__':
    print('Preparing datasets and dataloaders...')
    # Load dataset
    full_dataset = datasets.ImageFolder(DATA_DIR, transform=train_transforms)
    class_names = full_dataset.classes  # <-- Edit class names by changing folder names
    num_classes = len(class_names)

    # Train/val split
    val_pct = 0.2
    val_size = int(len(full_dataset) * val_pct)
    train_size = len(full_dataset) - val_size
    train_dataset, val_dataset = random_split(full_dataset, [train_size, val_size])
    # Apply val transforms to validation set
    val_dataset.dataset.transform = val_transforms

    train_loader = DataLoader(train_dataset, batch_size=BATCH_SIZE, shuffle=True, num_workers=NUM_WORKERS)
    val_loader = DataLoader(val_dataset, batch_size=BATCH_SIZE, shuffle=False, num_workers=NUM_WORKERS)
    print('Dataloaders ready. Starting training...')

    # Debug: Test all samples in full_dataset for corrupt images
    print('Testing all images in the dataset for corruption...')
    for i in range(len(full_dataset)):
        img_path, _ = full_dataset.samples[i]
        if i % 100 == 0:
            print(f'Testing image {i+1}/{len(full_dataset)}: {img_path}')
        try:
            full_dataset[i]
        except Exception as e:
            print(f'Error at index {i} (file: {img_path}): {e}')
            break
    print('Sample test complete.')

    # Model
    model = efficientnet_b0(weights=EfficientNet_B0_Weights.IMAGENET1K_V1)
    model.classifier[1] = nn.Linear(model.classifier[1].in_features, num_classes)

    # Device
    device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')
    print(f"Using device: {device}")
    model = model.to(device)

    # Loss and optimizer
    criterion = nn.CrossEntropyLoss()
    optimizer = optim.Adam(model.parameters(), lr=LEARNING_RATE)

    # Training loop
    best_acc = 0.0
    print('Starting training loop...')
    for epoch in range(NUM_EPOCHS):
        print(f'Starting epoch {epoch+1}/{NUM_EPOCHS}')
        model.train()
        running_loss = 0.0
        running_corrects = 0
        total_train = 0
        batch_idx = 0
        for inputs, labels in train_loader:
            print(f'Processing batch {batch_idx+1}')
            batch_idx += 1
            inputs, labels = inputs.to(device), labels.to(device)
            optimizer.zero_grad()
            outputs = model(inputs)
            _, preds = torch.max(outputs, 1)
            loss = criterion(outputs, labels)
            loss.backward()
            optimizer.step()
            running_loss += loss.item() * inputs.size(0)
            running_corrects += torch.sum(preds == labels.data)
            total_train += labels.size(0)
        epoch_loss = running_loss / total_train
        epoch_acc = running_corrects.double() / total_train

        # Validation
        model.eval()
        val_loss = 0.0
        val_corrects = 0
        total_val = 0
        with torch.no_grad():
            for inputs, labels in val_loader:
                inputs, labels = inputs.to(device), labels.to(device)
                outputs = model(inputs)
                _, preds = torch.max(outputs, 1)
                loss = criterion(outputs, labels)
                val_loss += loss.item() * inputs.size(0)
                val_corrects += torch.sum(preds == labels.data)
                total_val += labels.size(0)
        val_loss /= total_val
        val_acc = val_corrects.double() / total_val

        print(f"Epoch {epoch+1}/{NUM_EPOCHS} | Train Loss: {epoch_loss:.4f} | Train Acc: {epoch_acc:.4f} | Val Loss: {val_loss:.4f} | Val Acc: {val_acc:.4f}")

        # Save best model
        if val_acc > best_acc:
            best_acc = val_acc
            torch.save({
                'model_state_dict': model.state_dict(),
                'class_names': class_names
            }, MODEL_PATH)

    print('Training complete. Best Val Acc: {:.4f}'.format(best_acc))
