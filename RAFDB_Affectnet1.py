import os
import torch
import torch.nn as nn
import torch.optim as optim
import pandas as pd
from torch.utils.data import Dataset, DataLoader, random_split
from torchvision import transforms
from PIL import Image
import timm

# Correct mapping: RAF-DB label (1–7) → 0-indexed class
label_map = {
    1: 0,  # Surprise
    2: 1,  # Fear
    3: 2,  # Disgust
    4: 3,  # Happy
    5: 4,  # Sad
    6: 5,  # Angry
    7: 6   # Neutral
}

class RAFDBDataset(Dataset):
    def __init__(self, csv_file, root_dir, transform=None):
        self.df = pd.read_csv(csv_file)
        self.root_dir = root_dir
        self.transform = transform

    def __len__(self):
        return len(self.df)

    def __getitem__(self, idx):
        rel_path = self.df.iloc[idx]['image_path'].strip()
        img_path = os.path.normpath(os.path.join(self.root_dir, rel_path)).replace("\\", "/")
        image = Image.open(img_path).convert("RGB")
        if self.transform:
            image = self.transform(image)
        original_label = int(self.df.iloc[idx]['emotion'])
        label = label_map[original_label]  # Corrected label
        return image, label

def main():
    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    batch_size = 32
    num_epochs = 30

    train_transforms = transforms.Compose([
        transforms.Resize((96, 96)),
        transforms.RandomHorizontalFlip(),
        transforms.RandomRotation(15),
        transforms.ColorJitter(brightness=0.2, contrast=0.2, saturation=0.2, hue=0.1),
        transforms.RandomResizedCrop(96, scale=(0.8, 1.0)),
        transforms.ToTensor(),
        transforms.Normalize(mean=[0.485, 0.456, 0.406],
                             std=[0.229, 0.224, 0.225])
    ])

    eval_transforms = transforms.Compose([
        transforms.Resize((96, 96)),
        transforms.ToTensor(),
        transforms.Normalize(mean=[0.485, 0.456, 0.406],
                             std=[0.229, 0.224, 0.225])
    ])

    train_csv = "rafdb_train_labels.csv"
    images_root = os.path.join("DATASET", "train")

    full_dataset = RAFDBDataset(csv_file=train_csv, root_dir=images_root, transform=train_transforms)
    train_size = int(0.8 * len(full_dataset))
    val_size = len(full_dataset) - train_size
    train_dataset, val_dataset = random_split(full_dataset, [train_size, val_size])

    train_loader = DataLoader(train_dataset, batch_size=batch_size, shuffle=True, num_workers=4)
    val_loader = DataLoader(val_dataset, batch_size=batch_size, shuffle=False, num_workers=4)

    model = timm.create_model('vit_base_patch16_224', pretrained=False, img_size=96, drop_rate=0.1)
    model.head = nn.Sequential(
        nn.Dropout(0.1),
        nn.Linear(model.head.in_features, 7)  # 7 emotion classes
    )
    model = model.to(device)

    state_dict = torch.load("best_vit_affectnet.pth", map_location=device)
    for key in list(state_dict.keys()):
        if key.startswith("head.1."):
            state_dict.pop(key)
    model.load_state_dict(state_dict, strict=False)

    criterion = nn.CrossEntropyLoss()
    optimizer = optim.AdamW(model.parameters(), lr=1e-4, weight_decay=1e-5)
    scheduler = torch.optim.lr_scheduler.CosineAnnealingWarmRestarts(optimizer, T_0=10, T_mult=2)

    best_val_acc = 0.0

    for epoch in range(num_epochs):
        model.train()
        running_loss = 0.0
        correct_train = 0
        total_train = 0

        for images, labels in train_loader:
            images, labels = images.to(device), labels.to(device)
            optimizer.zero_grad()
            outputs = model(images)
            loss = criterion(outputs, labels)
            loss.backward()
            optimizer.step()
            scheduler.step(epoch + len(images) / len(train_loader))

            running_loss += loss.item() * images.size(0)
            _, predicted = torch.max(outputs, 1)
            total_train += labels.size(0)
            correct_train += (predicted == labels).sum().item()

        train_loss = running_loss / total_train
        train_acc = 100 * correct_train / total_train

        # Validation
        model.eval()
        val_loss = 0.0
        correct_val = 0
        total_val = 0
        with torch.no_grad():
            for images, labels in val_loader:
                images, labels = images.to(device), labels.to(device)
                outputs = model(images)
                loss = criterion(outputs, labels)
                val_loss += loss.item() * images.size(0)
                _, predicted = torch.max(outputs, 1)
                total_val += labels.size(0)
                correct_val += (predicted == labels).sum().item()

        val_loss /= total_val
        val_acc = 100 * correct_val / total_val

        print(f"Epoch {epoch+1}/{num_epochs} -- "
              f"Train Loss: {train_loss:.4f}, Train Acc: {train_acc:.2f}% -- "
              f"Val Loss: {val_loss:.4f}, Val Acc: {val_acc:.2f}%")

        if val_acc > best_val_acc:
            best_val_acc = val_acc
            torch.save(model.state_dict(), "best_vit_rafdb_corrected.pth")

    print("✅ Stage 2 retraining complete with corrected labels!")

if __name__ == '__main__':
    main()
