import sys
import wave
import vosk
import json


model = vosk.Model("vosk-model-en-us-0.22")  # Load the Vosk model
wf = wave.open("test.wav", "rb")  # Open the WAV file

rec = vosk.KaldiRecognizer(model, wf.getframerate())  # Create recognizer

while True:
    data = wf.readframes(2500)  # Read a small chunk
    if len(data) == 0:
        break
    if rec.AcceptWaveform(data):  # Process the chunk
        print(json.loads(rec.Result()))  # Print result for this chunk

print(json.loads(rec.FinalResult()))  # Final result after all chunks
