"use client";

import { useState, useRef, useEffect } from "react";
import { motion } from "framer-motion";

export default function Dude() {
  // State for toggling button icons / recording status
  const [vdoBtnClicked, setVdoBtnClicked] = useState(false);
  // State for holding the live video stream (when recording)
  const [videoStream, setVideoStream] = useState<MediaStream | null>(null);
  // State for the MediaRecorder instance
  const [mediaRecorder, setMediaRecorder] = useState<MediaRecorder | null>(
    null
  );
  // State for storing the recorded video preview URL
  const [recordedVideo, setRecordedVideo] = useState<string | null>(null);
  // State for storing the actual recorded video blob (to send to backend)
  const [videoBlob, setVideoBlob] = useState<Blob | null>(null);
  const [voiceBtnClicked, setVoiceBtnClicked] = useState(false);
  const [chatStarted, setChatStarted] = useState(false);

  const [aiResponse, setAiResponse] = useState<string | null>(null);

  const videoRef = useRef<HTMLVideoElement>(null);

  // When a live stream is available, assign it to the video element.
  useEffect(() => {
    if (videoRef.current && videoStream) {
      videoRef.current.srcObject = videoStream;
    }
  }, [videoStream]);

  // Handle video button click: start recording or stop (pause) recording.
  async function handleVideoCall() {
    // If there's no recording in progress and no recorded video exists, start recording.
    if (!vdoBtnClicked && !recordedVideo) {
      try {
        const stream = await navigator.mediaDevices.getUserMedia({
          video: true,
          audio: true,
        });
        setVideoStream(stream);

        const recorder = new MediaRecorder(stream, { mimeType: "video/webm" });
        const chunks: BlobPart[] = [];

        recorder.ondataavailable = (event) => {
          if (event.data.size > 0) {
            chunks.push(event.data);
          }
        };

        recorder.onstop = () => {
          // Create a blob and an object URL from the recorded chunks.
          const blob = new Blob(chunks, { type: "video/webm" });
          const videoURL = URL.createObjectURL(blob);
          setRecordedVideo(videoURL);
          setVideoBlob(blob);
          // Stop all tracks to release the camera.
          stream.getTracks().forEach((track) => track.stop());
          setVideoStream(null);
          setMediaRecorder(null);
        };

        setMediaRecorder(recorder);
        recorder.start();
        setVdoBtnClicked(true);
      } catch (error) {
        console.error("Error accessing camera", error);
      }
    } else if (vdoBtnClicked) {
      // If recording is in progress, stop the recording.
      if (mediaRecorder && mediaRecorder.state === "recording") {
        mediaRecorder.stop();
      }
      setVdoBtnClicked(false);
      setChatStarted(true);
    }
  }

  // New handler to delete the recorded video.
  function handleDeleteVideo() {
    setRecordedVideo(null);
    setVideoBlob(null);
    // Optionally, allow the user to start a new recording after deletion.
  }

  // Handle voice call (dummy behavior).
  function handleVoiceCall() {
    console.log("Voice Call");
    setVoiceBtnClicked(!voiceBtnClicked);
    setChatStarted(true);
  }

  // Send the recorded video blob to a dummy backend.
  async function handleSend() {

    // Reset recorded video on clicking send.
    setRecordedVideo(null);
    setVideoBlob(null);

    setAiResponse("Analyzing...");
    if (videoBlob) {
      const formData = new FormData();
      formData.append("file", videoBlob, "recorded_video.webm");

      try {
        const response = await fetch("http://localhost:3000/api/analyze", {
          method: "POST",
          body: formData,
        });
        console.log("Video sent to backend", response);
        const data = await response.json();
        setAiResponse(data.response);
      } catch (error) {
        console.error("Error sending video:", error);
      }

      
    } else {
      console.log("No video to send");
    }
  }

  return (
    <div
      className={
        !chatStarted
          ? "flex flex-col items-center justify-center h-screen w-screen"
          : "grid grid-cols-1 grid-rows-7 gap-4 h-screen w-screen"
      }
    >
      <motion.h1
        className={`font-alohaMagazine tracking-wider transition-all duration-500 flex items-center ${
          !chatStarted
            ? "text-5xl"
            : "text-4xl p-4 row-span-1 shadow-xl shadow-black/40 border-b border-white/25"
        }`}
        initial={{ opacity: 0 }}
        animate={{ opacity: 1 }}
        transition={{
          type: "spring",
          stiffness: 300,
          damping: 30,
          duration: 1.5,
        }}
      >
        Hello, Athul
      </motion.h1>

      {/* Background blobs */}
      <div className="h-screen w-screen absolute -z-10 overflow-hidden">
        <div className="blob1 z-10 opacity-50"></div>
        <div className="blob2 z-10 opacity-50"></div>
        <div className="blob3 z-10 opacity-50"></div>
        <div className="blob4 z-10 opacity-50"></div>
      </div>

      {/* Video recording interface (live preview or recorded preview) */}
      {(vdoBtnClicked || recordedVideo) && (
        <div className="absolute bottom-36 sm:bottom-32 left-1/2 transform -translate-x-1/2 w-[90%] max-w-md bg-black/20 border border-white/25 backdrop-blur-xl p-2 rounded-xl shadow-2xl shadow-black/70">
          {vdoBtnClicked && videoStream ? (
            // Live preview while recording.
            <video
              ref={videoRef}
              autoPlay
              muted
              className="w-full rounded-lg"
            />
          ) : recordedVideo ? (
            // Recorded video preview with controls.
            <video src={recordedVideo} controls className="w-full rounded-lg" />
          ) : null}
        </div>
      )}

      {chatStarted && (
        <div className="row-span-5 flex flex-col items-center">
          {/* This middle section can be used for your chat window */}
          <div className="overflow-y-auto h-full w-full md:max-w-2/3 flex flex-col items-center justify-start font-montserrat text-lg sm:text-2xl p-5 text-white font-light">
            {aiResponse ? (
              <motion.h1
                initial={{ opacity: 0 }}
                animate={{ opacity: 1 }}
                transition={{
                  type: "spring",
                  stiffness: 200,
                  damping: 30,
                  duration: 1.5,
                }}
              >
                {aiResponse}
              </motion.h1>
            ) : (
              <motion.h1
                initial={{ opacity: 0 }}
                animate={{ opacity: 1 }}
                transition={{
                  type: "spring",
                  stiffness: 200,
                  damping: 30,
                  duration: 1.5,
                }}
              >
                What&apos;s on your mind?
              </motion.h1>
            )}
          </div>
        </div>
      )}

      {/* Bottom bar */}
      <div
        className={`z-20 absolute -bottom-10 sm:bottom-10 items-center left-1/2 transform -translate-x-1/2 w-full p-3 sm:max-w-3/5 md:max-w-3/5 bg-black/20 border border-white/25 backdrop-blur-xl px-4 py-2 rounded-lg flex justify-center gap-2 shadow-2xl shadow-black/70 ${
          chatStarted ? "row-span-1" : ""
        }`}
      >
        <input
          type="text"
          className="w-full bg-transparent text-white/75 text-2xl sm:text-lg outline-none font-montserrat placeholder:font-montserrat"
          placeholder="confide in"
        />

        {/* Voice Button */}
        <div
          className="bg-black/5 w-[90px] h-16 sm:w-14 sm:h-12 flex items-center justify-center border border-white/25 hover:rounded-md transition-all duration-300 p-[10px] rounded-4xl group cursor-pointer backdrop-blur-3xl active:rounded-sm shadow-lg shadow-black/30"
          onClick={handleVoiceCall}
        >
          {!voiceBtnClicked ? (
            <svg
              xmlns="http://www.w3.org/2000/svg"
              width="25"
              height="25"
              viewBox="0 0 24 24"
              fill="none"
              stroke="currentColor"
              strokeWidth="1.7"
              strokeLinecap="round"
              strokeLinejoin="round"
              className="lucide lucide-mic group-hover:scale-[110%] transition-all duration-300 rounded-full group-active:scale-90 group-hover:rounded-md"
            >
              <path d="M12 2a3 3 0 0 0-3 3v7a3 3 0 0 0 6 0V5a3 3 0 0 0-3-3Z" />
              <path d="M19 10v2a7 7 0 0 1-14 0v-2" />
              <line x1="12" x2="12" y1="19" y2="22" />
            </svg>
          ) : (
            <svg
              xmlns="http://www.w3.org/2000/svg"
              width="25"
              height="25"
              viewBox="0 0 24 24"
              fill="currentColor"
              stroke="currentColor"
              strokeWidth="0.75"
              strokeLinecap="round"
              strokeLinejoin="round"
              className="lucide lucide-pause group-hover:scale-[110%] transition-all duration-300 rounded-full group-active:scale-90 group-hover:rounded-md"
            >
              <rect x="14" y="4" width="4" height="16" rx="1" />
              <rect x="6" y="4" width="4" height="16" rx="1" />
            </svg>
          )}
        </div>

        {/* Video Button:
            - If recording is in progress (vdoBtnClicked is true): show pause icon.
            - If a recorded video exists (and not recording): show delete icon.
            - Otherwise: show video icon to start recording.
         */}
        <div
          className="bg-black/5 w-[90px] h-16 sm:w-14 sm:h-12 flex items-center justify-center border border-white/25 hover:rounded-md transition-all duration-300 p-[10px] rounded-4xl group cursor-pointer backdrop-blur-3xl active:rounded-sm shadow-lg shadow-black/30"
          onClick={recordedVideo ? handleDeleteVideo : handleVideoCall}
        >
          {vdoBtnClicked ? (
            // Recording in progress: show pause icon.
            <svg
              xmlns="http://www.w3.org/2000/svg"
              width="25"
              height="25"
              viewBox="0 0 24 24"
              fill="currentColor"
              stroke="currentColor"
              strokeWidth="0.75"
              strokeLinecap="round"
              strokeLinejoin="round"
              className="lucide lucide-pause group-hover:scale-[110%] transition-all duration-300 rounded-full group-active:scale-90 group-hover:rounded-md"
            >
              <rect x="14" y="4" width="4" height="16" rx="1" />
              <rect x="6" y="4" width="4" height="16" rx="1" />
            </svg>
          ) : recordedVideo ? (
            // Recorded video exists: show delete icon.
            <svg
              xmlns="http://www.w3.org/2000/svg"
              width="25"
              height="25"
              fill="none"
              stroke="currentColor"
              strokeWidth="1"
              strokeLinecap="round"
              strokeLinejoin="round"
              className="lucide lucide-trash-2  group-hover:scale-[110%] transition-all duration-300 rounded-full group-active:scale-90 group-hover:rounded-md"
            >
              <path d="M3 6h18" />
              <path d="M19 6v14c0 1-1 2-2 2H7c-1 0-2-1-2-2V6" />
              <path d="M8 6V4c0-1 1-2 2-2h4c1 0 2 1 2 2v2" />
              <line x1="10" x2="10" y1="11" y2="17" />
              <line x1="14" x2="14" y1="11" y2="17" />
            </svg>
          ) : (
            // No recording: show video icon.
            <svg
              xmlns="http://www.w3.org/2000/svg"
              width="25"
              height="25"
              viewBox="0 0 24 24"
              fill="currentColor"
              stroke="currentColor"
              strokeWidth="0.75"
              strokeLinecap="round"
              strokeLinejoin="round"
              className="lucide lucide-video group-hover:scale-[110%] transition-all duration-300 rounded-full group-active:scale-90 group-hover:rounded-md"
            >
              <path d="m16 13 5.223 3.482a.5.5 0 0 0 .777-.416V7.87a.5.5 0 0 0-.752-.432L16 10.5" />
              <rect x="2" y="6" width="14" height="12" rx="2" />
            </svg>
          )}
        </div>

        {/* Send Button */}
        <div
          className="bg-black/5 w-22 h-16 sm:w-14 sm:h-12 flex items-center justify-center border border-white/25 hover:rounded-2xl transition-all duration-300 p-[10px] rounded-md group cursor-pointer backdrop-blur-3xl active:rounded-4xl shadow-lg shadow-black/30"
          onClick={handleSend}
        >
          <svg
            xmlns="http://www.w3.org/2000/svg"
            width="25"
            height="25"
            fill="#ffffff"
            stroke="transparent"
            strokeWidth="2"
            strokeLinecap="round"
            strokeLinejoin="round"
            className="lucide lucide-send group-hover:scale-[105%] transition-all duration-300 group-active:scale-90"
          >
            <path d="M14.536 21.686a.5.5 0 0 0 .937-.024l6.5-19a.496.496 0 0 0-.635-.635l-19 6.5a.5.5 0 0 0-.024.937l7.93 3.18a2 2 0 0 1 1.112 1.11z" />
            <path d="m21.854 2.147-10.94 10.939" />
          </svg>
        </div>
      </div>

    </div>
  );
}