# app.py
# Minimal Flask frontend that sends text to the Chatterbox HF Space and streams back audio.
# Uses a public sample audio (no uploads). Edit TEXT only if you want to default text.
#
# Requirements:
#   pip install flask gradio_client requests

from flask import Flask, render_template_string, request, Response, jsonify
from gradio_client import Client, handle_file
from pathlib import Path
import base64, requests, mimetypes, os

app = Flask(__name__)

# ---------- CONFIG: change only if needed ----------
HF_SPACE = "ResembleAI/Chatterbox"   # Hugging Face Space used
SAMPLE_PROMPT_URL = "https://github.com/gradio-app/gradio/raw/main/test/test_files/audio_sample.wav"
# Fixed parameters for every request:
PARAM_EXAGGERATION = 0.6
PARAM_TEMPERATURE = 0.75
PARAM_SEED = 0
PARAM_CFGW =0.35
PARAM_VAD_TRIM = False
API_NAME = "/generate_tts_audio"
DOWNLOAD_DIR = "./downloads"  # where gradio_client will place downloaded files
# ---------------------------------------------------

INDEX_HTML = """
<!doctype html>
<html>
  <head>
    <meta charset="utf-8"/>
    <title>Simple Chatterbox TTS</title>
    <style>
      body { font-family: Arial, sans-serif; margin: 2rem; }
      textarea { width: 100%; height: 120px; font-size: 1rem; }
      button { padding: 0.6rem 1rem; font-size: 1rem; margin-top: 0.5rem; }
      audio { display:block; margin-top:1rem; width: 100%; }
      .status { margin-top: 0.6rem; color: #555; }
    </style>
  </head>
  <body>
    <h2>Chatterbox TTS — simple frontend</h2>
    <p>Type the text you want spoken below and click <b>Synthesize</b>.</p>
    <textarea id="text">Hello — this is a quick test.</textarea>
    <br/>
    <button id="synth">Synthesize</button>
    <div class="status" id="status"></div>
    <audio id="player" controls></audio>

    <script>
      document.getElementById("synth").onclick = async () => {
        const text = document.getElementById("text").value.trim();
        if (!text) return alert("Enter some text first.");
        const status = document.getElementById("status");
        const player = document.getElementById("player");
        status.textContent = "Requesting synthesis...";
        player.src = "";

        try {
          const resp = await fetch("/synthesize", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ text })
          });
          if (!resp.ok) {
            const txt = await resp.text();
            status.textContent = "Error: " + resp.status + " — " + txt;
            return;
          }
          // Response is an audio blob. Play it.
          const blob = await resp.blob();
          const url = URL.createObjectURL(blob);
          player.src = url;
          player.play().catch(()=>{/* autoplay may be blocked */});
          status.textContent = "Playing generated audio.";
          player.onended = () => { URL.revokeObjectURL(url); status.textContent = "Done."; };
        } catch (err) {
          console.error(err);
          status.textContent = "Request failed: " + err.message;
        }
      };
    </script>
  </body>
</html>
"""

def ensure_download_dir():
    Path(DOWNLOAD_DIR).mkdir(parents=True, exist_ok=True)

def result_to_bytes_and_mime(result, download_dir=DOWNLOAD_DIR):
    """
    Accepts raw result from client.predict and returns (bytes, mime_type).
    Handles:
      - bytes / bytearray
      - data:audio/...;base64,...
      - http(s) URL pointing to audio (downloads it)
      - server-local path string (client may have downloaded it to download_dir)
      - list/tuple (unwraps first element)
    """
    # unwrap list/tuple
    if isinstance(result, (list, tuple)) and result:
        result = result[0]

    # raw bytes
    if isinstance(result, (bytes, bytearray)):
        return bytes(result), "application/octet-stream"

    # string cases
    if isinstance(result, str):
        s = result.strip()

        # 1) data URI
        if s.startswith("data:audio"):
            header, b64 = s.split(",", 1)
            mime = header.split(";")[0].split(":")[1] if ":" in header else "audio/wav"
            return base64.b64decode(b64), mime

        # 2) http(s) URL -> download
        if s.startswith("http://") or s.startswith("https://"):
            r = requests.get(s, stream=True, timeout=30)
            r.raise_for_status()
            mime = r.headers.get("Content-Type", "audio/mpeg")
            return r.content, mime or "audio/mpeg"

        # 3) server-local path string returned by the Space.
        p = Path(s)
        if p.exists():
            raw = p.read_bytes()
            mime, _ = mimetypes.guess_type(str(p))
            return raw, mime or "application/octet-stream"

        # 4) check downloads folder for a basename match
        maybe = Path(download_dir) / Path(s).name
        if maybe.exists():
            raw = maybe.read_bytes()
            mime, _ = mimetypes.guess_type(str(maybe))
            return raw, mime or "application/octet-stream"

    raise RuntimeError(f"Unhandled model result type: {type(result)} | value: {str(result)[:300]}")

@app.route("/")
def index():
    return render_template_string(INDEX_HTML)

@app.route("/synthesize", methods=["POST"])
def synth():
    data = request.get_json() or {}
    text = data.get("text", "").strip()
    if not text:
        return jsonify({"error": "text required"}), 400

    ensure_download_dir()

    # Create client with download_files so any server-local paths are downloaded into DOWNLOAD_DIR
    client = Client(HF_SPACE, download_files=DOWNLOAD_DIR)

    try:
        result = client.predict(
            text_input=text,
            audio_prompt_path_input=handle_file(SAMPLE_PROMPT_URL),
            exaggeration_input=PARAM_EXAGGERATION,
            temperature_input=PARAM_TEMPERATURE,
            seed_num_input=PARAM_SEED,
            cfgw_input=PARAM_CFGW,
            vad_trim_input=PARAM_VAD_TRIM,
            api_name=API_NAME,
        )
    except Exception as e:
        # return exception message for debugging (could be quota or timeout)
        return str(e), 500

    try:
        audio_bytes, mime = result_to_bytes_and_mime(result, download_dir=DOWNLOAD_DIR)
    except Exception as e:
        return f"Could not convert model result: {e}", 500

    # Return audio bytes (stream) with MIME
    return Response(audio_bytes, mimetype=(mime or "audio/mpeg"))

if __name__ == "__main__":
    app.run(debug=True, port=5000)
