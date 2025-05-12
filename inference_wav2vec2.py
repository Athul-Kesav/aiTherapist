import torch
import librosa
import numpy as np
from transformers import (
    Wav2Vec2Processor,
    Wav2Vec2ForSequenceClassification,
    WhisperProcessor,
    WhisperForConditionalGeneration
)

# Set device
DEVICE = torch.device("cuda" if torch.cuda.is_available() else "cpu")

# Emotion labels (update this list based on your training labels)
emotion_labels = [
    "neutral", "calm", "happy", "sad", "angry", "fearful", "disgust", "surprise"
]

# Load Wav2Vec2 Emotion Model
EMO_MODEL_PATH = "best_wav2vec2_ravdess/best.pth"
emo_model = Wav2Vec2ForSequenceClassification.from_pretrained(
    "facebook/wav2vec2-base", num_labels=len(emotion_labels)
).to(DEVICE)
emo_processor = Wav2Vec2Processor.from_pretrained("facebook/wav2vec2-base")

# Load trained weights
state = torch.load(EMO_MODEL_PATH, map_location=DEVICE)
emo_model.load_state_dict(state)
emo_model.eval()

# Load Whisper for Speech-to-Text
stt_processor = WhisperProcessor.from_pretrained("openai/whisper-small")
stt_model = WhisperForConditionalGeneration.from_pretrained("openai/whisper-small").to(DEVICE)
stt_model.eval()

# Inference function
def predict_emotion_and_text_wav2vec2(wav_path: str) -> dict:
    """
    Given a path to a WAV file, returns:
      {
        'transcript': <str>,
        'emotion': <str>
      }
    """

    # Load & resample to 16kHz
    audio, sr = librosa.load(wav_path, sr=16000)

    # --- 1. Speech-to-Text using Whisper ---
    stt_inputs = stt_processor(audio, sampling_rate=sr, return_tensors='pt').to(DEVICE)
    with torch.no_grad():
        generated_ids = stt_model.generate(**stt_inputs)
        transcription = stt_processor.batch_decode(generated_ids, skip_special_tokens=True)[0]

    # --- 2. Emotion Classification using Wav2Vec2 ---
    emo_inputs = emo_processor(audio, sampling_rate=sr, return_tensors='pt', padding=True).to(DEVICE)
    with torch.no_grad():
        logits = emo_model(**emo_inputs).logits
        predicted_id = torch.argmax(logits, dim=-1).item()
        emotion = emotion_labels[predicted_id]

    return {
        "transcript": transcription,
        "emotion": emotion
    }
