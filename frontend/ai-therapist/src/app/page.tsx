'use client';

import { useRouter } from "next/navigation";


export default function Home() {

  const router = useRouter();

  return (
    <div className="flex flex-col items-center justify-around h-screen p-7 bg-gray-950">
      <h1 className="text-4xl font-serif">AI Therapist</h1>
      <p className="text-lg font-serif text-center">An AI-powered chatbot that listens to you and provides emotional support.</p>
      <button className="px-4 py-2 mt-4 text-white bg-blue-500 rounded-md" onClick={() => {
        router.push("/dude");
      }}>Get Started</button>
    </div>
  );
}
