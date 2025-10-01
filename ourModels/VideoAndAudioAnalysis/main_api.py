from flask import Flask, request, jsonify
import os
import uuid
from pathlib import Path
from moviepy import VideoFileClip
from inference_vit import predict_emotion_vit
from inference_wav2vec2 import predict_emotion_and_text_wav2vec2
from frame_utils import extract_frames
from collections import Counter
import shutil

# Initialize Flask app
app = Flask(__name__)
PORT = 5173

def analyze_video_sync(video_path):
    """
    Perform the video emotion analysis synchronously.
    """
    temp_id = Path(video_path).stem
    audio_path = f"temp/{temp_id}.wav"

    try:
        # Extract audio from video
        clip = VideoFileClip(video_path)
        clip.audio.write_audiofile(audio_path, logger=None)
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
        avg_face_conf = sum(face_confidences) / len(face_confidences) if face_confidences else 0

        return {
            "face_emotion": final_face_emotion,
            "avg_confidence": round(avg_face_conf, 2),
            "voice_emotion": voice_result.get("emotion", "unknown"),
            "transcription": voice_result.get("transcript", "")
        }

    except Exception as e:
        return {'status': 'FAILURE', 'error': str(e)}

    finally:
        # Clean up entire temp folder after every run
        if os.path.exists("temp"):
            shutil.rmtree("temp")

# Flask API endpoints
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

    try:
        # Save video file
        file.save(video_path)
        
        # Run analysis synchronously
        result = analyze_video_sync(video_path)
        
        return jsonify({
            "message": "Video analysis complete",
            "result": result
        }), 200

    except Exception as e:
        return jsonify({"error": f"Failed to process video file: {str(e)}"}), 500

if __name__ == "__main__":
    print("App running on port", PORT)
    app.run(host="0.0.0.0", port=PORT, debug=False)
