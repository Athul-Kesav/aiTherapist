"use client";

// components/VideoRecorder.tsx
import React, { useRef, useState } from 'react';

const VideoRecorder: React.FC = () => {
  const videoRef = useRef<HTMLVideoElement | null>(null);
  const mediaRecorderRef = useRef<MediaRecorder | null>(null);
  const [recording, setRecording] = useState<boolean>(false);
  const [videoBlob, setVideoBlob] = useState<Blob | null>(null);
  const [responseMessage, setResponseMessage] = useState<string | null>(null);

  const startRecording = async () => {
    try {
      const stream = await navigator.mediaDevices.getUserMedia({ video: true, audio: true });
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
      console.error('Error accessing media devices.', error);
      alert('Could not access camera and microphone.');
    }
  };

  const stopRecording = () => {
    mediaRecorderRef.current?.stop();
    setRecording(false);
  };

  const uploadVideo = async () => {
    if (!videoBlob) return;

    const formData = new FormData();
    formData.append('file', videoBlob, 'recorded-video.webm');

    try {
      const response = await fetch('/api/get-video', {
        method: 'POST',
        body: formData,
      });

      if (response.ok) {
        const data = await response.json();
        setResponseMessage(data.message || 'Video uploaded successfully!');
      } else {
        setResponseMessage('Failed to upload video.');
      }
    } catch (error) {
      console.error('Error uploading video:', error);
      setResponseMessage('Error uploading video.');
    }
  };

  return (
    <div style={{ display: 'flex', flexDirection: 'column', alignItems: 'center' }}>
      <video ref={videoRef} autoPlay muted style={{ width: '100%', maxWidth: '400px' }} className='' />
      <div>
        {!recording ? (
          <button onClick={startRecording} className='p-4 bg-green-300 active:bg-green-500 hover:bg-green-400 m-5 text-black cursor-pointer rounded-lg'>Start Recording</button>
        ) : (
          <button onClick={stopRecording} className='p-4 bg-green-300 active:bg-green-500 hover:bg-green-400 m-5 text-black cursor-pointer rounded-lg'>Stop Recording</button>
        )}
      </div>
      {videoBlob && (
        <div>
          <button onClick={uploadVideo} className='p-4 bg-blue-300 active:bg-blue-500 hover:bg-blue-400 m-5 text-black cursor-pointer rounded-lg'>Upload Video</button>
        </div>
      )}
      {responseMessage && (
        <div className='p-4 bg-gray-200 m-5 text-black rounded-lg'>
          {responseMessage}
        </div>
      )}
    </div>
  );
};

export default VideoRecorder;