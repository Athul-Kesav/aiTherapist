import assemblyai as aai
from dotenv import load_dotenv
import os

load_dotenv()
API_KEY = os.getenv("ASSEMBLYAI_API_KEY")

aai.settings.api_key = API_KEY
transcriber = aai.Transcriber()

transcript = transcriber.transcribe("./test.wav")
# transcript = transcriber.transcribe("./my-local-audio-file.wav")

print(transcript.text)