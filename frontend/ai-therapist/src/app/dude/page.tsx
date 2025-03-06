"use client";

// components/VideoRecorder.tsx
import React, { useRef, useState } from "react";
import Image from "next/image";

type AudioResponse = {
  average_intensity: number;
  average_pitch: number;
  max_pitch: number;
  min_pitch: number;
  transcript: string;
};

type VideoResponse = {
  mood: string;
};

type ResponseMessage =
  | {
      message: string;
      audioResponse: AudioResponse;
      videoResponse: VideoResponse;
    }
  | string
  | null;

const VideoRecorder: React.FC = () => {
  const videoRef = useRef<HTMLVideoElement | null>(null);
  const mediaRecorderRef = useRef<MediaRecorder | null>(null);
  const [recording, setRecording] = useState<boolean>(false);
  const [videoBlob, setVideoBlob] = useState<Blob | null>(null);
  const [responseMessage, setResponseMessage] = useState<ResponseMessage>(null);
  const [showUploadVideoBtn, setShowUploadVideoBtn] = useState(true);

  const startRecording = async () => {
    try {
      const stream = await navigator.mediaDevices.getUserMedia({
        video: true,
        audio: true,
      });
      if (videoRef.current) {
        videoRef.current.srcObject = stream;
      }

      mediaRecorderRef.current = new MediaRecorder(stream);
      mediaRecorderRef.current.ondataavailable = (event) => {
        setVideoBlob(event.data);
      };

      mediaRecorderRef.current.start();
      setRecording(true);
    } catch (error) {
      console.error("Error accessing media devices.", error);
      alert("Could not access camera and microphone.");
    }
  };

  const stopRecording = () => {
    mediaRecorderRef.current?.stop();
    setRecording(false);
  };

  const uploadVideo = async () => {
    setShowUploadVideoBtn(false);
    if (!videoBlob) return;

    const formData = new FormData();
    formData.append("file", videoBlob, "recorded-video.webm");

    try {
      const response = await fetch("/api/get-video", {
        method: "POST",
        body: formData,
      });

      if (response.ok) {
        const data = await response.json();
        setResponseMessage(
          data.videoResponse.mood || "Video uploaded successfully!"
        );
        console.log(responseMessage);
      } else {
        setResponseMessage("Failed to upload video.");
      }
    } catch (error) {
      console.error("Error uploading video:", error);
      setResponseMessage("Error uploading video.");
    }
  };

  return (
    <div className="relative flex flex-col items-center">
      <div className="h-screen w-screen flex justify-center items-center overflow-hidden relative">
        {showUploadVideoBtn && (
          <video
            ref={videoRef}
            autoPlay
            muted
            style={{ width: "100%", maxWidth: "400px" }}
            className="z-10 absolute  object-cover"
          />
        )}
        <Image
          src="/background.jpg"
          alt="background"
          layout="fill"
          objectFit="cover"
          className="object-right -z-10"
        />
        {!recording ? (
          <button
            onClick={startRecording}
            className="absolute bottom-20 origin-center hover:scale-110 transition-all active:scale-95 p-4 bg-[#D7C5F9] active:bg-[#c3a5fc] hover:bg-[#b58efd] m-5 text-black cursor-pointer rounded-full z-20"
          >
            <svg
              xmlns="http://www.w3.org/2000/svg"
              width="50"
              height="50"
              viewBox="0 0 24 24"
              fill="none"
              stroke="currentColor"
              strokeWidth="1"
              strokeLinecap="round"
              strokeLinejoin="round"
              className="lucide lucide-mic"
            >
              <path d="M12 2a3 3 0 0 0-3 3v7a3 3 0 0 0 6 0V5a3 3 0 0 0-3-3Z" />
              <path d="M19 10v2a7 7 0 0 1-14 0v-2" />
              <line x1="12" x2="12" y1="19" y2="22" />
            </svg>
          </button>
        ) : (
          <button
            onClick={() => {
              stopRecording();
            }}
            className="absolute bottom-20 origin-center hover:scale-110 transition-all active:scale-95 p-4 bg-[#D7C5F9] active:bg-[#c3a5fc] hover:bg-[#b58efd] m-5 text-black cursor-pointer rounded-full z-20"
          >
            <svg
              xmlns="http://www.w3.org/2000/svg"
              width="50"
              height="50"
              viewBox="0 0 24 24"
              fill="currentColor"
              stroke="currentColor"
              strokeWidth="1"
              strokeLinecap="round"
              strokeLinejoin="round"
              className="lucide lucide-pause"
            >
              <rect x="14" y="4" width="4" height="16" rx="1" />
              <rect x="6" y="4" width="4" height="16" rx="1" />
            </svg>
          </button>
        )}
      </div>
      {videoBlob && showUploadVideoBtn && (
        <div className="flex flex-col items-center">
          <button
            onClick={uploadVideo}
            className="bottom-36 p-4 bg-blue-300 z-20 active:bg-blue-500 absolute hover:bg-blue-400 m-5 text-black cursor-pointer rounded-lg"
          >
            Upload Video
          </button>
        </div>
      )}

      {responseMessage && typeof responseMessage !== "string" && (
        <div className="absolute bottom-64 p-4 bg-gray-200 m-5 text-black rounded-lg ">
          {responseMessage.audioResponse ? (
            <div>
              <h2>Audio Analysis</h2>
              <p>
                Average Intensity:{" "}
                {responseMessage.audioResponse.average_intensity}
              </p>
              <p>
                Average Pitch: {responseMessage.audioResponse.average_pitch}
              </p>
              <p>Max Pitch: {responseMessage.audioResponse.max_pitch}</p>
              <p>Min Pitch: {responseMessage.audioResponse.min_pitch}</p>
              <p>Transcript: {responseMessage.audioResponse.transcript}</p>
            </div>
          ) : (
            ""
          )}
          <h2>Video Analysis</h2>
          <p>Mood: {responseMessage.videoResponse.mood}</p>
        </div>
      )}
    </div>
  );
};

export default VideoRecorder;
