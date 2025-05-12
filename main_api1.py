from fastapi import FastAPI, File, UploadFile, HTTPException
from moviepy.editor import VideoFileClip
from pathlib import Path
import shutil
import uuid

from inference_vit import predict_emotion_vit
from inference_wav2vec2 import predict_emotion_and_text_wav2vec2
from frame_utils import extract_frames

app = FastAPI()

# Fixed temp directory and filenames
TEMP_DIR = Path("temp")
VIDEO_FILE = TEMP_DIR / "video.mp4"
AUDIO_FILE = TEMP_DIR / "audio.wav"
FRAME_PATTERN = "frame_*.jpg"  # matches extract_frames outputs

@app.on_event("startup")
def ensure_temp():
    # Create the temp folder if it doesn't exist
    TEMP_DIR.mkdir(exist_ok=True)

@app.get("/")
async def root():
    return {"message": "Welcome to the Emotion Analysis API!"}

@app.post("/analyze")
async def analyze_video(file: UploadFile = File(...)):
    # 1) Clean out any old files in temp/
    for p in TEMP_DIR.glob("*"):
        p.unlink()

    # 2) Save the incoming video (always to video.mp4)
    if not file.filename.lower().endswith((".mp4", ".mov", ".mkv", ".avi")):
        raise HTTPException(status_code=400, detail="Please upload a video file (.mp4, .mov, .mkv, .avi)")
    with VIDEO_FILE.open("wb") as f:
        f.write(await file.read())

    # 3) Extract audio → audio.wav
    clip = VideoFileClip(str(VIDEO_FILE))
    clip.audio.write_audiofile(str(AUDIO_FILE), logger=None)
    clip.reader.close(); clip.audio.reader.close_proc()

    # 4) Extract frames at 1 FPS → temp/frame_0.jpg, frame_1.jpg, ...
    frame_paths = extract_frames(str(VIDEO_FILE), temp_id=None)

    # 5) Face Emotion across frames
    face_results = [predict_emotion_vit(fp) for fp in frame_paths]
    face_emotions    = [res["emotion"]    for res in face_results]
    face_confidences = [res["confidence"] for res in face_results]

    # 6) Voice Emotion + Transcription
    voice_result = predict_emotion_and_text_wav2vec2(str(AUDIO_FILE))

    # 7) Aggregate face emotions (mode) & average confidence
    from collections import Counter
    final_face_emotion = Counter(face_emotions).most_common(1)[0][0]
    avg_face_conf     = sum(face_confidences) / len(face_confidences) if face_confidences else 0.0

    return {
        "face_emotion": final_face_emotion,
        "avg_confidence": round(avg_face_conf, 2),
        "voice_emotion": voice_result["emotion"],
        "transcription": voice_result["transcript"]
    }
