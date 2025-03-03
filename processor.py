import librosa
import numpy as np
from flask import Flask, request, jsonify
import assemblyai as aai
from dotenv import load_dotenv
import os
import cv2
import time
from deepface import DeepFace



# import speech_recognition as sr

""" def get_transcript(audio_file):
    
    # Convert an audio file to text using Google's speech recognition.
    # Returns the transcript, or "unknown" if the audio is not clear.
    
    recognizer = sr.Recognizer()
    try:
        with sr.AudioFile(audio_file) as source:
            audio_data = recognizer.record(source)
        # Using Google Web Speech API for recognition.
        # You can change this to another recognizer if desired.
        transcript = recognizer.recognize_google(audio_data)
    except (sr.UnknownValueError, sr.RequestError):
        transcript = "unknown"
    return transcript """
    
app = Flask(__name__)

def process_audio_file(audio_file, sr_target=22050, hop_length=512):
    
    """
    Process an audio file to extract waveform, pitch, intensity
    
    Parameters:
      audio_file (str): Path to the input audio file.
      sr_target (int): Sample rate to use for loading audio. Default is 22050 Hz.
      hop_length (int): Hop length for frame-based features. Default is 512.
      
    Returns:
      dict: A dictionary containing:
            - 'audio': The raw audio signal (1D numpy array).
            - 'time_wave': Time axis for the waveform (seconds).
            - 'pitch': The estimated pitch (Hz) per frame (numpy array).
            - 'time_pitch': Time axis for the pitch values (seconds).
            - 'intensity': RMS intensity values per frame (numpy array).
            - 'time_intensity': Time axis for the RMS values (seconds).
            - 'average_pitch': The average pitch (Hz) computed over valid frames.
            - 'min_pitch': The minimum pitch (Hz) among valid frames.
            - 'max_pitch': The robust maximum pitch (95th percentile, Hz) among valid frames.
            - 'average_intensity': The average RMS intensity.
            - 'transcript': The transcript of the audio file.
    """
    
    
    # Load the audio file using librosa
    audio, sr = librosa.load(audio_file, sr=sr_target)
    
    # Estimate pitch using librosa.yin in the desired range (50-3000 Hz)
    pitches = librosa.yin(audio, fmin=50, fmax=3000, sr=sr, hop_length=hop_length)
    # time_pitch = librosa.frames_to_time(np.arange(len(pitches)), sr=sr, hop_length=hop_length)
    
    # Remove NaN values from pitch estimates (unvoiced frames)
    valid_pitches = pitches[~np.isnan(pitches)]
    if valid_pitches.size == 0:
        average_pitch = 0
        min_pitch = 0
        max_pitch = 0
    else:
        # Clip the values to enforce the desired range
        valid_pitches = np.clip(valid_pitches, 100, 3000)
        average_pitch = np.mean(valid_pitches)
        min_pitch = np.min(valid_pitches)
        max_pitch = np.percentile(valid_pitches, 95)
    
    # Compute RMS intensity over time
    rms = librosa.feature.rms(y=audio, hop_length=hop_length)[0]
    # time_intensity = librosa.frames_to_time(np.arange(len(rms)), sr=sr, hop_length=hop_length)
    average_intensity = np.mean(rms)
    
    # Get the transcript using speech recognition
    # transcript = get_transcript(audio_file)
    load_dotenv()
    API_KEY = os.getenv("ASSEMBLYAI_API_KEY")

    aai.settings.api_key = API_KEY
    transcriber = aai.Transcriber()

    transcript = transcriber.transcribe(audio_file)
    
    # Package all the results into a dictionary
    results = {
    # "audio": audio.tolist(),
    # "time_wave": time_wave.tolist(),
    # "pitch": pitches.tolist(),
    # "time_pitch": time_pitch.tolist(),
    # "intensity": rms.tolist(),
    # "time_intensity": time_intensity.tolist(),
    "average_pitch": round(float(average_pitch), 2),
    "min_pitch": round(float(min_pitch), 2),
    "max_pitch": round(float(max_pitch), 2),
    "average_intensity": round(float(average_intensity), 2),
    "transcript": transcript.text
}
    return results

# hosting

@app.route('/analyze-audio', methods=['POST'])

def analyze_audio():
    """ Endpoint to receive an audio file and return analysis. """
    if 'file' not in request.files:
        return jsonify({"error": "No file uploaded"}), 400

    file = request.files['file']
    filepath = "temp_audio.wav"
    file.save(filepath)

    # Process the uploaded audio file
    results = process_audio_file(filepath)

    return jsonify(results)

@app.route('/analyze-video', methods=['POST'])

def analyze_video():
    if 'file' not in request.files:
        return jsonify({"error": "No file uploaded"}), 400

    file = request.files['file']
    
    # Ensure the "temp" directory exists
    os.makedirs("temp", exist_ok=True)
    filepath = "temp/temp_video.mp4"
    file.save(filepath)

    cap = cv2.VideoCapture(filepath)
    if not cap.isOpened():
        return jsonify({"error": "Failed to open video file"}), 400

    frame_count = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
    if frame_count <= 0:
        cap.release()
        return jsonify({"error": "Video file has no frames"}), 400

    # Randomly sample frames (ensure we sample only when frames are available)
    frame_indices = np.random.choice(frame_count, size=min(10, frame_count), replace=False)
    emotions = []

    for idx in frame_indices:
        cap.set(cv2.CAP_PROP_POS_FRAMES, idx)
        ret, frame = cap.read()
        if not ret:
            continue
        try:
            result = DeepFace.analyze(frame, actions=['emotion'], enforce_detection=False)
            # DeepFace.analyze might return a dict or list depending on the version.
            # Adjust accordingly if needed.
            emotions.append(result[0]['dominant_emotion'] if isinstance(result, list) else result['dominant_emotion'])
        except Exception as e:
            print("Error analyzing frame:", e)
            continue

    cap.release()

    if not emotions:
        return jsonify({"error": "Could not detect emotions"}), 500

    # Determine the dominant mood by taking the most frequent emotion
    mood = max(set(emotions), key=emotions.count)
    return jsonify({"mood": mood})

# Example usage
if __name__ == "__main__":
    # Replace 'path/to/audio.wav' with your actual audio file path.
    # audio_file = "./test.wav"
    # data = process_audio_file(audio_file)
    
    # Print analysis summary
    # print("Voice Analysis Summary:")
    # print("Average Pitch: {:.2f} Hz".format(data["average_pitch"]))
    # print("Min Pitch: {:.2f} Hz".format(data["min_pitch"]))
    # print("Max Pitch: {:.2f} Hz".format(data["max_pitch"]))
    # print("Average Intensity: {:.4f}".format(data["average_intensity"]))
    
    app.run(host='0.0.0.0', port=5000, debug=True)
