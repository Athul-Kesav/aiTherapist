import { motion } from "framer-motion";
import "./ShinyButton.css";

type ButtonProps = {
    btnText : string,
    cta : () => void
}
const ShinyButton = ({btnText, cta}:ButtonProps) => {
  return (
    <motion.button
      initial={{ "--x": "100%" }}
      animate={{ "--x": "-100%" }}
      transition={{
        repeat: Infinity,
        repeatType: "loop",
        repeatDelay: 1,
        type: "spring",
        stiffness: 100,
        damping: 50,
        mass: 10,
        
      }}
      className="px-6 py-3 rounded-md relative radial-gradient z-50 cursor-pointer hover:scale-[102%] active:scale-[97%] transition-all duration-300"
      onClick={cta}
    >
      <span className="text-neutral-100 text-3xl sm:text-xl font-montserrat tracking-wide font-light h-full w-full block relative linear-mask">
        {btnText}
      </span>
      <span className="block absolute inset-0 rounded-md p-[2px] linear-overlay" />
    </motion.button>
  );
};

export default ShinyButton;