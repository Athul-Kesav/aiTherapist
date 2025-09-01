from flask import Flask, request, jsonify
import os
import uuid
from pathlib import Path
from moviepy import VideoFileClip
from inference_vit import predict_emotion_vit
from inference_wav2vec2 import predict_emotion_and_text_wav2vec2
from frame_utils import extract_frames
from collections import Counter

app = Flask(__name__)
PORT = 5173

@app.route("/", methods=["GET"])
def root():
    return jsonify({"message": "Welcome to the Emotion Analysis API!"})

@app.route("/analyze", methods=["POST"])
def analyze_video():
    if "file" not in request.files:
        return jsonify({"error": "No file uploaded"}), 400
    
    file = request.files["file"]
    if file.filename == "":
        return jsonify({"error": "Empty filename"}), 400

    temp_id = str(uuid.uuid4())
    os.makedirs("temp", exist_ok=True)
    video_path = f"temp/{temp_id}.mp4"
    audio_path = f"temp/{temp_id}.wav"

    try:
        # Save video file
        file.save(video_path)

        # Extract audio from video
        clip = VideoFileClip(video_path)
        clip.audio.write_audiofile(audio_path, logger=None)  # disable verbose logs
        clip.close() 

        # Extract frames
        frame_paths = extract_frames(video_path, temp_id)

        # Face Emotion
        face_results = [predict_emotion_vit(fp) for fp in frame_paths]
        face_emotions = [res['emotion'] for res in face_results]
        face_confidences = [res['confidence'] for res in face_results]

        # Voice Emotion + Transcription
        voice_result = predict_emotion_and_text_wav2vec2(audio_path)

        # Aggregate (most common emotion)
        final_face_emotion = Counter(face_emotions).most_common(1)[0][0] if face_emotions else "unknown"
        avg_face_conf = sum(face_confidences)/len(face_confidences) if face_confidences else 0

        return jsonify({
            "face_emotion": final_face_emotion,
            "avg_confidence": round(avg_face_conf, 2),
            "voice_emotion": voice_result.get("emotion", "unknown"),
            "transcription": voice_result.get("transcript", "")
        })

    finally:
        # 🔥 Cleanup temp files
        if os.path.exists(video_path):
            os.remove(video_path)
        if os.path.exists(audio_path):
            os.remove(audio_path)
        for fp in Path("temp").glob(f"{temp_id}_frame_*.jpg"):
            os.remove(fp)

if __name__ == "__main__":
    print("App running on port ", PORT)
    app.run(host="0.0.0.0", port=PORT, debug=False)
    
