'use client';

import { useEffect, useRef, useState } from "react";

const InteractiveBubbles: React.FC = () => {
  const interactiveRef = useRef<HTMLDivElement>(null);
  const [curX, setCurX] = useState<number>(0);
  const [curY, setCurY] = useState<number>(0);
  const [tgX, setTgX] = useState<number>(0);
  const [tgY, setTgY] = useState<number>(0);

  useEffect(() => {
    const move = (): void => {
      setCurX((prevX) => prevX + (tgX - prevX) / 20);
      setCurY((prevY) => prevY + (tgY - prevY) / 20);
      if (interactiveRef.current) {
        interactiveRef.current.style.transform = `translate(${Math.round(curX)}px, ${Math.round(curY)}px)`;
      }
      requestAnimationFrame(move);
    };
    move();
  }, [tgX, tgY]);

  useEffect(() => {
    const handleMouseMove = (event: MouseEvent): void => {
      setTgX(event.clientX);
      setTgY(event.clientY);
    };
    window.addEventListener("mousemove", handleMouseMove);
    return () => window.removeEventListener("mousemove", handleMouseMove);
  }, []);

  return (
    <div className="relative w-screen h-screen overflow-hidden bg-gradient-to-br from-purple-800 to-blue-900">
      
      <div className="absolute w-full h-full">
        <div className="absolute w-full h-full bg-purple-400 rounded-full opacity-80 animate-bounce blur-3xl mix-blend-hard-light" />
        <div className="absolute w-full h-full bg-pink-500 rounded-full opacity-80 animate-spin blur-3xl mix-blend-hard-light" />
        <div className="absolute w-full h-full bg-cyan-400 rounded-full opacity-80 animate-pulse blur-3xl mix-blend-hard-light" />
        <div ref={interactiveRef} className="absolute w-32 h-32 bg-indigo-400 opacity-70 mix-blend-hard-light" />
      </div>
    </div>
  );
};

export default InteractiveBubbles;