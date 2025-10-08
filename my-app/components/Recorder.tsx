"use client";
import React, { useRef, useState } from "react";

export default function Recorder({
  onFinish,
}: {
  onFinish: (blob: Blob, url: string) => void;
}) {
  const liveVideoRef = useRef<HTMLVideoElement | null>(null);
  const mediaRecorderRef = useRef<MediaRecorder | null>(null);
  const recordedChunksRef = useRef<Blob[]>([]);
  const [isRecording, setIsRecording] = useState(false);
  const [recordedURL, setRecordedURL] = useState<string | null>(null);

  async function startRecording() {
    const stream = await navigator.mediaDevices.getUserMedia({
      video: true,
      audio: true,
    });
    const videoEl = liveVideoRef.current;
    if (videoEl) {
      videoEl.srcObject = stream;
      videoEl.play().catch(() => {});
    }

    const recorder = new MediaRecorder(stream);
    recordedChunksRef.current = [];

    recorder.ondataavailable = (e) => {
      if (e.data.size > 0) recordedChunksRef.current.push(e.data);
    };

    recorder.onstop = () => {
      const blob = new Blob(recordedChunksRef.current, { type: "video/webm" });
      const url = URL.createObjectURL(blob);
      setRecordedURL(url);
      onFinish(blob, url);
      stream.getTracks().forEach((t) => t.stop());
      setIsRecording(false);
    };

    recorder.start();
    mediaRecorderRef.current = recorder;
    setIsRecording(true);
  }

  function stopRecording() {
    if (mediaRecorderRef.current?.state === "recording")
      mediaRecorderRef.current.stop();
  }

  return (
    <div className="fixed left-1/2 transform -translate-x-1/2 bottom-28 z-40 w-[90%] max-w-md p-2 rounded-xl bg-black/30 border border-white/10 backdrop-blur">
      {isRecording ? (
        <div className="relative">
          <video
            ref={liveVideoRef}
            autoPlay
            muted
            playsInline
            className="w-full rounded-lg"
          />
          <div className="absolute top-2 left-2 bg-red-600 text-white text-xs px-2 py-1 rounded-md">
            ● Recording...
          </div>
        </div>
      ) : recordedURL ? (
        <video src={recordedURL} controls className="w-full rounded-lg" />
      ) : null}

      <div className="flex justify-center gap-2 mt-2">
        <button
          onClick={isRecording ? stopRecording : startRecording}
          className={`px-4 py-2 rounded ${
            isRecording ? "bg-red-600" : "bg-indigo-600"
          }`}
        >
          {isRecording ? "Stop" : "Record"}
        </button>
      </div>
    </div>
  );
}
