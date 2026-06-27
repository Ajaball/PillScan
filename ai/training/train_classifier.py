"""
PillScan — EfficientNet-V2-S Classification Training Script

Trains a pill classifier using transfer learning from ImageNet weights.
Supports: Training, validation, model export (ONNX, TFLite).

Usage:
    python train_classifier.py --data_dir ./data/processed --epochs 50 --batch_size 32
"""

import os
import argparse
import json
from datetime import datetime

# These imports require PyTorch and torchvision installed
# pip install torch torchvision timm albumentations

def get_args():
    parser = argparse.ArgumentParser(description="Train PillScan Classifier")
    parser.add_argument("--data_dir", type=str, required=True, help="Path to processed dataset")
    parser.add_argument("--output_dir", type=str, default="../models/classification", help="Output directory for trained model")
    parser.add_argument("--epochs", type=int, default=50, help="Number of training epochs")
    parser.add_argument("--batch_size", type=int, default=32, help="Batch size")
    parser.add_argument("--learning_rate", type=float, default=1e-4, help="Initial learning rate")
    parser.add_argument("--img_size", type=int, default=224, help="Input image size")
    parser.add_argument("--num_workers", type=int, default=4, help="Data loading workers")
    parser.add_argument("--pretrained", action="store_true", default=True, help="Use ImageNet pretrained weights")
    parser.add_argument("--freeze_backbone", action="store_true", default=False, help="Freeze backbone layers (feature extraction only)")
    return parser.parse_args()


def main():
    args = get_args()

    print("=" * 60)
    print("PillScan Classifier Training")
    print("=" * 60)
    print(f"  Model:          EfficientNet-V2-S")
    print(f"  Data:           {args.data_dir}")
    print(f"  Epochs:         {args.epochs}")
    print(f"  Batch Size:     {args.batch_size}")
    print(f"  Learning Rate:  {args.learning_rate}")
    print(f"  Image Size:     {args.img_size}x{args.img_size}")
    print(f"  Pretrained:     {args.pretrained}")
    print("=" * 60)

    try:
        import torch
        import torch.nn as nn
        import torch.optim as optim
        from torch.utils.data import DataLoader
        from torchvision import datasets, transforms
        import timm
    except ImportError as e:
        print(f"\n❌ Missing dependencies: {e}")
        print("Install with: pip install torch torchvision timm")
        print("\nFor Google Colab, the dependencies are pre-installed.")
        return

    # ── Device Setup ─────────────────────────────────────────────────
    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    print(f"\n🖥️  Device: {device}")
    if device.type == "cuda":
        print(f"   GPU: {torch.cuda.get_device_name(0)}")
        print(f"   Memory: {torch.cuda.get_device_properties(0).total_mem / 1e9:.1f} GB")

    # ── Data Transforms ──────────────────────────────────────────────
    train_transform = transforms.Compose([
        transforms.Resize((args.img_size + 32, args.img_size + 32)),
        transforms.RandomCrop(args.img_size),
        transforms.RandomHorizontalFlip(),
        transforms.RandomVerticalFlip(),
        transforms.RandomRotation(30),
        transforms.ColorJitter(brightness=0.3, contrast=0.3, saturation=0.2, hue=0.1),
        transforms.RandomAffine(degrees=0, translate=(0.1, 0.1)),
        transforms.ToTensor(),
        transforms.Normalize(mean=[0.485, 0.456, 0.406], std=[0.229, 0.224, 0.225]),
    ])

    val_transform = transforms.Compose([
        transforms.Resize((args.img_size, args.img_size)),
        transforms.ToTensor(),
        transforms.Normalize(mean=[0.485, 0.456, 0.406], std=[0.229, 0.224, 0.225]),
    ])

    # ── Dataset Loading ──────────────────────────────────────────────
    train_dir = os.path.join(args.data_dir, "train")
    val_dir = os.path.join(args.data_dir, "val")

    if not os.path.exists(train_dir):
        print(f"\n❌ Training data not found at {train_dir}")
        print("Expected structure:")
        print("  data/processed/")
        print("    train/")
        print("      class_0_panadol/")
        print("      class_1_amoxil/")
        print("      ...")
        print("    val/")
        print("      class_0_panadol/")
        print("      ...")
        return

    train_dataset = datasets.ImageFolder(train_dir, transform=train_transform)
    val_dataset = datasets.ImageFolder(val_dir, transform=val_transform)

    num_classes = len(train_dataset.classes)
    print(f"\n📊 Dataset:")
    print(f"   Classes:    {num_classes}")
    print(f"   Training:   {len(train_dataset)} images")
    print(f"   Validation: {len(val_dataset)} images")
    print(f"   Classes:    {train_dataset.classes}")

    train_loader = DataLoader(
        train_dataset, batch_size=args.batch_size,
        shuffle=True, num_workers=args.num_workers, pin_memory=True
    )
    val_loader = DataLoader(
        val_dataset, batch_size=args.batch_size,
        shuffle=False, num_workers=args.num_workers, pin_memory=True
    )

    # ── Model Setup ──────────────────────────────────────────────────
    model = timm.create_model(
        "tf_efficientnetv2_s",
        pretrained=args.pretrained,
        num_classes=num_classes,
    )

    if args.freeze_backbone:
        # Freeze all layers except the classifier head
        for param in model.parameters():
            param.requires_grad = False
        for param in model.classifier.parameters():
            param.requires_grad = True
        print("   🧊 Backbone frozen — training classifier head only")

    model = model.to(device)
    total_params = sum(p.numel() for p in model.parameters())
    trainable_params = sum(p.numel() for p in model.parameters() if p.requires_grad)
    print(f"\n🧠 Model: EfficientNet-V2-S")
    print(f"   Total params:     {total_params:,}")
    print(f"   Trainable params: {trainable_params:,}")

    # ── Training Setup ───────────────────────────────────────────────
    criterion = nn.CrossEntropyLoss(label_smoothing=0.1)
    optimizer = optim.AdamW(
        filter(lambda p: p.requires_grad, model.parameters()),
        lr=args.learning_rate,
        weight_decay=0.01,
    )
    scheduler = optim.lr_scheduler.CosineAnnealingLR(optimizer, T_max=args.epochs)

    # ── Training Loop ────────────────────────────────────────────────
    best_val_acc = 0.0
    history = {"train_loss": [], "train_acc": [], "val_loss": [], "val_acc": []}

    os.makedirs(args.output_dir, exist_ok=True)

    print(f"\n🚀 Starting training...\n")

    for epoch in range(args.epochs):
        # Training phase
        model.train()
        train_loss = 0.0
        train_correct = 0
        train_total = 0

        for batch_idx, (images, labels) in enumerate(train_loader):
            images, labels = images.to(device), labels.to(device)

            optimizer.zero_grad()
            outputs = model(images)
            loss = criterion(outputs, labels)
            loss.backward()
            optimizer.step()

            train_loss += loss.item()
            _, predicted = outputs.max(1)
            train_total += labels.size(0)
            train_correct += predicted.eq(labels).sum().item()

        scheduler.step()

        train_loss /= len(train_loader)
        train_acc = 100.0 * train_correct / train_total

        # Validation phase
        model.eval()
        val_loss = 0.0
        val_correct = 0
        val_total = 0

        with torch.no_grad():
            for images, labels in val_loader:
                images, labels = images.to(device), labels.to(device)
                outputs = model(images)
                loss = criterion(outputs, labels)

                val_loss += loss.item()
                _, predicted = outputs.max(1)
                val_total += labels.size(0)
                val_correct += predicted.eq(labels).sum().item()

        val_loss /= len(val_loader)
        val_acc = 100.0 * val_correct / val_total

        # Record history
        history["train_loss"].append(train_loss)
        history["train_acc"].append(train_acc)
        history["val_loss"].append(val_loss)
        history["val_acc"].append(val_acc)

        # Print progress
        lr = optimizer.param_groups[0]["lr"]
        print(
            f"Epoch [{epoch+1}/{args.epochs}]  "
            f"Train Loss: {train_loss:.4f}  Train Acc: {train_acc:.2f}%  "
            f"Val Loss: {val_loss:.4f}  Val Acc: {val_acc:.2f}%  "
            f"LR: {lr:.6f}"
        )

        # Save best model
        if val_acc > best_val_acc:
            best_val_acc = val_acc
            best_model_path = os.path.join(args.output_dir, "best_model.pth")
            torch.save({
                "epoch": epoch + 1,
                "model_state_dict": model.state_dict(),
                "optimizer_state_dict": optimizer.state_dict(),
                "val_acc": val_acc,
                "num_classes": num_classes,
                "class_names": train_dataset.classes,
            }, best_model_path)
            print(f"   ✅ New best model saved! Val Acc: {val_acc:.2f}%")

    # ── Save Final Results ───────────────────────────────────────────
    print(f"\n{'=' * 60}")
    print(f"Training Complete!")
    print(f"  Best Validation Accuracy: {best_val_acc:.2f}%")
    print(f"  Model saved to: {args.output_dir}")
    print(f"{'=' * 60}")

    # Save training history
    with open(os.path.join(args.output_dir, "training_history.json"), "w") as f:
        json.dump(history, f, indent=2)

    # Save class mapping
    with open(os.path.join(args.output_dir, "class_names.json"), "w") as f:
        json.dump(train_dataset.classes, f, indent=2)


if __name__ == "__main__":
    main()
