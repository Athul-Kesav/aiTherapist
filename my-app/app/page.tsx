"use client";

import ShinyButton from "@/components/ShinyButton";
import { useRouter } from "next/navigation";

export default function Home() {
  const router = useRouter();

  return (
    <>
      <div className="h-screen w-screen flex flex-col justify-center items-center -z-40 ">
        <div className="h-screen w-screen absolute -z-10 overflow-hidden">
          <div className="blob1 z-10"></div>
          <div className="blob2 z-10"></div>
          <div className="blob3 z-10"></div>
          <div className="blob4 z-10"></div>
        </div>
        <h1 className="text-white font-alohaMagazine  pointer-events-none z-40 text-5xl sm:text-7xl italic absolute top-1/2 left-1/2 origin-center transform -translate-x-1/2 -translate-y-1/2  ">
          EmpathAIse
          <p className="text-lg sm:text-lg font-montserrat text-center z-10 absolute left-1/2 transform -translate-x-1/2 font-sans not-italic w-full">
            An AI-powered friend
            <br />
            to help you understand yourself better.
          </p>
        </h1>
        <div className="absolute bottom-20">
          {/* <div
            className="relative inline-flex items-center justify-center gap-4 group cursor-pointer "
            onClick={handleCallToAction}
          >
            <div className="absolute inset-0 duration-1000 opacity-30 transitiona-all bg-gradient-to-r from-indigo-500 via-pink-500 to-yellow-400 rounded-xl blur-lg filter group-hover:opacity-65 group-hover:duration-200"></div>
            <a
              role="button"
              className="not-italic group relative inline-flex items-center justify-center text-base rounded-xl bg-black px-8 py-3 font-montserrat text-white transition-all duration-200 hover:shadow-lg hover:-translate-y-0.5 active:translate-y-0.5 hover:shadow-gray-600/30"
            >
              Get Started For Free
              <svg
                aria-hidden="true"
                viewBox="0 0 10 10"
                height="10"
                width="10"
                fill="none"
                className="mt-0.5 ml-2 -mr-1 stroke-white stroke-1"
              >
                <path
                  d="M0 5h7"
                  className="transition opacity-0 group-hover:opacity-100"
                />{" "}
                <path
                  d="M1 1l4 4-4 4"
                  className="transition group-hover:translate-x-[3px]"
                ></path>
              </svg>
            </a>
          </div> */}
          <ShinyButton
            btnText="Get Started"
            cta={() => {
              router.push("/dude");
            }}
          />
        </div>
      </div>
    </>
  );
}
