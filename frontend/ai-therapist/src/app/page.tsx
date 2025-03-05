"use client";

import { useRouter } from "next/navigation";
import Image from "next/image";

export default function Home() {
  const router = useRouter();

  return (
    <div className="flex flex-col items-center justify-around h-screen p-7">
      <div className="w-screen h-screen absolute z-0 ">
        <Image src="/background.jpg" alt="background" layout="fill" objectFit="cover" className="" />
      </div>
      <div className="text-4xl top-1/2 sm:text-6xl text-center font-serif text-white z-0 mix-blend-difference ">
        EmpathAIse
        <p className="text-sm sm:text-lg font-serif text-center text-white">
          An AI-powered companion that listens to you <br/> and provides emotional
          support.
        </p>
      </div>
      <button
        className="absolute font-semibold text-2xl font-sans bottom-7 px-5 py-2 text-black border border-transparent hover:border-black hover:text-black  bg-[#D7C5F9] hover:bg-[#D7C5F970] rounded-md active:bg-[#D7C5F9] transition-all duration-200 cursor-pointer"
        onClick={() => {
          router.push("/dude");
        }}
      >
        Get Started
      </button>
    </div>
  );
}
