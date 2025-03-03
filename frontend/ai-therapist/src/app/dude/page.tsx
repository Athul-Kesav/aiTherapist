"use client";

import { useState, useRef } from "react";

export default function RecordVideo() {
  const videoRef = useRef<HTMLVideoElement>(null);
  const mediaRecorderRef = useRef<MediaRecorder | null>(null);
  const [recording, setRecording] = useState(false);
  const [videoUrl, setVideoUrl] = useState<string | null>(null);
  // Use a ref to store chunks for a more synchronous update
  const chunksRef = useRef<Blob[]>([]);

  // Start recording: request media, set up recorder, and start recording.
  async function startRecording() {
    try {
      const stream = await navigator.mediaDevices.getUserMedia({
        video: true,
        audio: true,
      });
      if (videoRef.current) {
        videoRef.current.srcObject = stream;
        videoRef.current.play();
      }

      // Reset chunks before starting
      chunksRef.current = [];
      const options = { mimeType: "video/webm" };
      const mediaRecorder = new MediaRecorder(stream, options);
      mediaRecorderRef.current = mediaRecorder;

      mediaRecorder.ondataavailable = (event) => {
        if (event.data && event.data.size > 0) {
          chunksRef.current.push(event.data);
        }
      };

      // Wait for the recorder to fully stop before processing the data
      mediaRecorder.onstop = async () => {
        // Combine all chunks into a single Blob
        const blob = new Blob(chunksRef.current, { type: "video/webm" });
        const url = URL.createObjectURL(blob);
        setVideoUrl(url);

        // Send video blob to backend
        await sendVideo(blob);

        // Optionally clear the chunks
        chunksRef.current = [];
      };

      mediaRecorder.start();
      setRecording(true);
    } catch (error) {
      console.error("Error accessing media devices.", error);
    }
  }

  // Stop recording: stop the recorder and all media tracks.
  async function stopRecording() {
    if (mediaRecorderRef.current) {
      mediaRecorderRef.current.stop();
    }
    setRecording(false);

    // Stop all tracks to turn off the camera
    if (videoRef.current && videoRef.current.srcObject) {
      const stream = videoRef.current.srcObject as MediaStream;
      stream.getTracks().forEach((track) => track.stop());
    }
  }

  // Send the recorded video using a POST request.
  async function sendVideo(blob: Blob): Promise<void> {
    const formData = new FormData();
    formData.append("video", blob, "recorded-video.webm");

    try {
      const res = await fetch("/api/get-video", {
        method: "POST",
        body: formData,
      });
      const data = await res.json();
      console.log("Upload response:", data);
    } catch (error) {
      console.error("Error uploading video:", error);
    }
  }

  return (
    <div className="p-4 max-w-full">
      <h1 className="text-2xl font-bold text-center mb-4">Record Video</h1>
      <video
        ref={videoRef}
        className="w-full h-auto rounded-md"
        autoPlay
        muted
      />
      <div className="mt-4 flex justify-center gap-2">
        {!recording ? (
          <button
            onClick={startRecording}
            className="flex-1 py-2 px-4 bg-green-500 hover:bg-green-600 text-white rounded-md"
          >
            Start Recording
          </button>
        ) : (
          <button
            onClick={stopRecording}
            className="flex-1 py-2 px-4 bg-red-500 hover:bg-red-600 text-white rounded-md"
          >
            Stop Recording
          </button>
        )}
      </div>
      {videoUrl && (
        <div className="mt-6">
          <h2 className="text-xl text-center mb-4">Recorded Video:</h2>
          <video
            src={videoUrl}
            controls
            className="w-full h-auto rounded-md"
          />
        </div>
      )}
    </div>
  );
}
