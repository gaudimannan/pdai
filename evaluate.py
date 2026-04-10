from pathlib import Path
from collections import defaultdict

import torch
import torch.nn as nn
from torch.utils.data import DataLoader
from torchvision import datasets, transforms
from torchvision.models import efficientnet_b0

MODEL_PATH = Path("best_model.pth")
DATA_DIR = Path("data")
BATCH_SIZE = 32
IMG_SIZE = 224
NUM_WORKERS = 0
DEVICE = torch.device("cuda" if torch.cuda.is_available() else "cpu")


def load_model(model_path: Path, class_names):
    model = efficientnet_b0(weights=None)
    model.classifier[1] = nn.Linear(model.classifier[1].in_features, len(class_names))
    checkpoint = torch.load(model_path, map_location="cpu")
    model.load_state_dict(checkpoint["model_state_dict"])
    model.to(DEVICE)
    model.eval()
    return model


def evaluate(model_path: Path = MODEL_PATH, data_dir: Path = DATA_DIR):
    if not model_path.exists():
        raise FileNotFoundError(f"Model checkpoint not found at: {model_path.resolve()}")
    if not data_dir.exists():
        raise FileNotFoundError(f"Dataset directory not found at: {data_dir.resolve()}")

    checkpoint = torch.load(model_path, map_location="cpu")
    class_names = checkpoint["class_names"]

    dataset = datasets.ImageFolder(
        root=str(data_dir),
        transform=transforms.Compose([
            transforms.Resize((IMG_SIZE, IMG_SIZE)),
            transforms.ToTensor(),
            transforms.Normalize([0.485, 0.456, 0.406], [0.229, 0.224, 0.225]),
        ]),
    )

    dataloader = DataLoader(dataset, batch_size=BATCH_SIZE, shuffle=False, num_workers=NUM_WORKERS)
    total_batches = len(dataloader)
    dataset_size = len(dataset)

    model = load_model(model_path, class_names)

    correct = 0
    total = 0
    class_correct = defaultdict(int)
    class_total = defaultdict(int)

    print(f"Evaluating {dataset_size} images across {total_batches} batches...")
    progress_interval = max(1, total_batches // 10)

    with torch.no_grad():
        for batch_idx, (inputs, labels) in enumerate(dataloader, start=1):
            inputs = inputs.to(DEVICE)
            labels = labels.to(DEVICE)

            outputs = model(inputs)
            _, preds = torch.max(outputs, 1)

            correct_batch = preds.eq(labels)
            correct += correct_batch.sum().item()
            total += labels.size(0)

            for label, is_correct in zip(labels.cpu(), correct_batch.cpu()):
                class_total[label.item()] += 1
                if is_correct:
                    class_correct[label.item()] += 1

            if batch_idx % progress_interval == 0 or batch_idx == total_batches:
                pct = (batch_idx / total_batches) * 100
                print(f"Progress: {batch_idx}/{total_batches} batches ({pct:.1f}%)", flush=True)

    overall_acc = correct / total if total else 0.0
    print(f"Overall accuracy on {total} samples: {overall_acc * 100:.2f}%")

    print("\nPer-class accuracy:")
    for idx, class_name in enumerate(class_names):
        total_count = class_total[idx]
        acc = (class_correct[idx] / total_count) * 100 if total_count else 0.0
        print(f"- {class_name}: {acc:.2f}% ({class_correct[idx]} / {total_count})")


if __name__ == "__main__":
    evaluate()
