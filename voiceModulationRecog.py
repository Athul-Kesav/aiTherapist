import librosa
import numpy as np
import speech_recognition as sr

def get_transcript(audio_file):
    """
    Convert an audio file to text using Google's speech recognition.
    Returns the transcript, or "unknown" if the audio is not clear.
    """
    recognizer = sr.Recognizer()
    try:
        with sr.AudioFile(audio_file) as source:
            audio_data = recognizer.record(source)
        # Using Google Web Speech API for recognition.
        # You can change this to another recognizer if desired.
        transcript = recognizer.recognize_google(audio_data)
    except (sr.UnknownValueError, sr.RequestError):
        transcript = "unknown"
    return transcript

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
    """
    # Load the audio file using librosa
    audio, sr = librosa.load(audio_file, sr=sr_target)
    
    # Create a time axis for the full waveform
    time_wave = np.linspace(0, len(audio) / sr, num=len(audio))
    
    # Estimate pitch using librosa.yin in the desired range (50-3000 Hz)
    pitches = librosa.yin(audio, fmin=50, fmax=3000, sr=sr, hop_length=hop_length)
    time_pitch = librosa.frames_to_time(np.arange(len(pitches)), sr=sr, hop_length=hop_length)
    
    # Remove NaN values from pitch estimates (unvoiced frames)
    valid_pitches = pitches[~np.isnan(pitches)]
    if valid_pitches.size == 0:
        average_pitch = 0
        min_pitch = 0
        max_pitch = 0
    else:
        # Clip the values to enforce the desired range
        valid_pitches = np.clip(valid_pitches, 50, 3000)
        average_pitch = np.mean(valid_pitches)
        min_pitch = np.min(valid_pitches)
        max_pitch = np.percentile(valid_pitches, 95)
    
    # Compute RMS intensity over time
    rms = librosa.feature.rms(y=audio, hop_length=hop_length)[0]
    time_intensity = librosa.frames_to_time(np.arange(len(rms)), sr=sr, hop_length=hop_length)
    average_intensity = np.mean(rms)
    
    # Get the transcript using speech recognition
    # transcript = get_transcript(audio_file)
    
    # Package all the results into a dictionary
    results = {
        "audio": audio,
        "time_wave": time_wave,
        "pitch": pitches,
        "time_pitch": time_pitch,
        "intensity": rms,
        "time_intensity": time_intensity,
        "average_pitch": average_pitch,
        "min_pitch": min_pitch,
        "max_pitch": max_pitch,
        "average_intensity": average_intensity,
    }
    return results

# Example usage
if __name__ == "__main__":
    # Replace 'path/to/audio.wav' with your actual audio file path.
    audio_file = "./test.wav"
    data = process_audio_file(audio_file)
    
    # Print analysis summary
    print("Voice Analysis Summary:")
    print("Average Pitch: {:.2f} Hz".format(data["average_pitch"]))
    print("Min Pitch: {:.2f} Hz".format(data["min_pitch"]))
    print("Max Pitch: {:.2f} Hz".format(data["max_pitch"]))
    print("Average Intensity: {:.4f}".format(data["average_intensity"]))
