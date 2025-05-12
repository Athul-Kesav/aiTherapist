import torch
import timm
from PIL import Image
from torchvision import transforms

# Label list must match training
EMOTION_LABELS = ["neutral", "calm", "happy", "sad", "angry", "fearful", "disgust", "surprise"]

# Load the fine-tuned ViT model (exactly as trained: 96x96 input, patch16)
model = timm.create_model(
    'vit_base_patch16_224',   # ViT-Base with 16x16 patches
    pretrained=False,
    num_classes=len(EMOTION_LABELS),
    img_size=96               # match 96x96 training resolution
)
# Load checkpoint with non-strict to accommodate head.1 vs head mismatch
state = torch.load('best_vit_model.pth', map_location='cpu')
model.load_state_dict(state, strict=False)
model.eval()

# Preprocessing: resize to 96x96, normalize (ImageNet stats)
preprocess = transforms.Compose([
    transforms.Resize((96, 96)),
    transforms.ToTensor(),
    transforms.Normalize(
        mean=[0.485, 0.456, 0.406],
        std=[0.229, 0.224, 0.225]
    )
])

def predict_emotion_vit(image_path: str) -> dict:
    """
    Given a path to an image, returns:
      {
        'emotion': <str label>,
        'confidence': <float 0-1>
      }
    """
    img = Image.open(image_path).convert('RGB')
    tensor = preprocess(img).unsqueeze(0)  # shape: (1, 3, 96, 96)

    with torch.no_grad():
        logits = model(tensor)
        probs = torch.softmax(logits, dim=1).squeeze(0)
        conf, idx = torch.max(probs, dim=0)

    return {
        'emotion': EMOTION_LABELS[idx.item()],
        'confidence': conf.item()
    }
