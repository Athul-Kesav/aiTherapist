export default function Dude() {
  return (
    <div className="flex flex-col items-center justify-center h-screen w-screen ">
      <div className="h-screen w-screen absolute -z-10 overflow-hidden">
        <div className="blob1 z-10 opacity-50"></div>
        <div className="blob2 z-10 opacity-50"></div>
        <div className="blob3 z-10 opacity-50"></div>
        <div className="blob4 z-10 opacity-50"></div>
      </div>
      <div className="z-20 absolute bottom-5 sm:bottom-10 items-center left-1/2 transform -translate-x-1/2 w-[90%] max-w-md bg-black/20 border border-white/25 backdrop-blur-xl px-4 py-2 rounded-lg flex justify-center gap-2 shadow-2xl shadow-black/70">
        <input
          type="text"
          className="w-full bg-transparent text-white/75 text-2xl sm:text-lg outline-none font-montserrat placeholder:font-montserrat "
          placeholder="confide in"
        />
        <div className="bg-black/5 w-[90px] h-16 sm:w-14 sm:h-12 flex items-center justify-center border border-white/25 hover:rounded-md transition-all duration-300 p-[10px] rounded-4xl group cursor-pointer backdrop-blur-3xl active:rounded-sm shadow-lg shadow-black/30">
          <svg
            xmlns="http://www.w3.org/2000/svg"
            viewBox="0 0 24 24"
            fill="none"
            stroke="currentColor"
            strokeWidth="1.5"
            strokeLinecap="round"
            strokeLinejoin="round"
            className="lucide lucide-mic group-hover:scale-[110%] transition-all duration-300 rounded-full group-active:scale-90 group-hover:rounded-md"
          >
            <path d="M12 2a3 3 0 0 0-3 3v7a3 3 0 0 0 6 0V5a3 3 0 0 0-3-3Z" />
            <path d="M19 10v2a7 7 0 0 1-14 0v-2" />
            <line x1="12" x2="12" y1="19" y2="22" />
          </svg>
        </div>
        <div className="bg-black/5 w-[90px] h-16 sm:w-14 sm:h-12 flex items-center justify-center border border-white/25 hover:rounded-2xl transition-all duration-300 p-[10px] rounded-md group cursor-pointer backdrop-blur-3xl active:rounded-4xl shadow-lg shadow-black/30">
          <svg
            xmlns="http://www.w3.org/2000/svg"
            viewBox="0 0 24 24"
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

      <h1 className="font-alohaMagazine text-5xl tracking-wider">
        Hello, Athul
      </h1>
    </div>
  );
}
