"use client";

import React, { useState, useRef } from "react";
import { RefreshCcw, Loader2 } from "lucide-react";

// Main application component
const TTS = () => {
  const [textInput, setTextInput] = useState(
    "Now let's make my mum's favourite. So three mars bars into the pan."
  );
  const [audioPromptFile, setAudioPromptFile] = useState<File | null>(null);
  const [audioUrl, setAudioUrl] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const audioRef = useRef<HTMLAudioElement>(null);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError(null);
    setAudioUrl(null);

    if (!textInput.trim() || !audioPromptFile) {
      setError("Please provide both text and an audio prompt file.");
      return;
    }

    setLoading(true);

    try {
      const formData = new FormData();
      formData.append("text_input", textInput);
      formData.append("audio_prompt_file", audioPromptFile);

      // Make the call to our local Next.js API route
      const response = await fetch("/api/test-tts", {
        method: "POST",
        body: formData,
      });

      if (!response.ok) {
        const errorData = await response.json();
        throw new Error(
          errorData.error || `HTTP error! Status: ${response.status}`
        );
      }

      const data = await response.json();

      if (data.audioDataUrl) {
        setAudioUrl(data.audioDataUrl);
      } else {
        setError("Generation failed: No audio data returned.");
      }
    } catch (err: any) {
      console.error(err);
      setError(`Error generating audio: ${err.message}`);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="min-h-screen bg-gray-50 flex items-center justify-center p-4 sm:p-6 font-inter">
      <div className="w-full max-w-xl bg-white shadow-xl rounded-xl p-6 md:p-10 border border-gray-200">
        <h1 className="text-3xl font-bold text-gray-800 mb-6 flex items-center">
          Voice Cloning TTS Demo{" "}
          <RefreshCcw className="ml-3 h-5 w-5 text-indigo-500" />
        </h1>
        <p className="text-gray-500 mb-8">
          This application uses a backend proxy to securely communicate with the
          Hugging Face Gradio Space.
        </p>

        <form onSubmit={handleSubmit} className="space-y-6">
          <div>
            <label
              htmlFor="textInput"
              className="block text-sm font-medium text-gray-700 mb-1"
            >
              Text to Speak (Max 200 chars)
            </label>
            <textarea
              id="textInput"
              rows={3}
              className="mt-1 block text-black w-full rounded-lg border border-gray-300 shadow-sm p-3 focus:border-indigo-500 focus:ring-indigo-500 transition duration-150"
              value={textInput}
              onChange={(e) => setTextInput(e.target.value)}
              maxLength={200}
              placeholder="Enter your script here..."
              disabled={loading}
            />
          </div>

          <div>
            <label
              htmlFor="audioPrompt"
              className="block text-sm font-medium text-gray-700 mb-1"
            >
              Voice Prompt File (.mpeg, .mp3, .wav)
            </label>
            <input
              id="audioPrompt"
              type="file"
              accept="audio/*"
              className="mt-1 block w-full text-sm text-gray-600 file:mr-4 file:py-2 file:px-4 file:rounded-full file:border-0 file:text-sm file:font-semibold file:bg-indigo-50 file:text-indigo-600 hover:file:bg-indigo-100 transition duration-150"
              onChange={(e) =>
                setAudioPromptFile(e.target.files ? e.target.files[0] : null)
              }
              required
              disabled={loading}
            />
            {audioPromptFile && (
              <p className="mt-2 text-xs text-gray-500">
                Selected file: {audioPromptFile.name}
              </p>
            )}
          </div>

          <button
            type="submit"
            className="w-full flex justify-center items-center py-3 px-4 border border-transparent rounded-lg shadow-sm text-base font-medium text-white bg-indigo-600 hover:bg-indigo-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-indigo-500 transition duration-150 disabled:bg-indigo-400"
            disabled={loading || !textInput.trim() || !audioPromptFile}
          >
            {loading ? (
              <>
                <Loader2 className="mr-2 h-5 w-5 animate-spin" />
                Generating Audio...
              </>
            ) : (
              "Generate Voice Clone"
            )}
          </button>
        </form>

        {error && (
          <div className="mt-6 p-4 bg-red-100 text-red-700 border border-red-300 rounded-lg">
            <strong>Error:</strong> {error}
          </div>
        )}

        {audioUrl && (
          <div className="mt-6 pt-6 border-t border-gray-200">
            <h2 className="text-xl font-semibold text-gray-800 mb-3">
              Playback Result
            </h2>
            <audio
              ref={audioRef}
              controls
              src={audioUrl}
              className="w-full rounded-lg shadow-md"
              autoPlay
            >
              Your browser does not support the audio element.
            </audio>
          </div>
        )}
      </div>
    </div>
  );
};

export default TTS;
