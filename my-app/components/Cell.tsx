"use client";

import styled from "@emotion/styled";

import { motion, MotionValue, useTransform } from "framer-motion";
import { useState, useRef, useEffect } from "react";

interface CellProps {
  mouseX: MotionValue<number>;
  mouseY: MotionValue<number>;
}

export const CELL_SIZE = 60;

const Container = styled.div`
  width: ${CELL_SIZE}px;
  height: ${CELL_SIZE}px;
  border: 1px dashed #555;
  color: #777;
  display: flex;
  justify-content: center;
  align-items: center;
  user-select: none;
`;

const Cell: React.FC<CellProps> = ({ mouseX, mouseY }) => {
  const [position, setPosition] = useState([0, 0]);
  const ref = useRef<HTMLDivElement>(null);
  const direction = useTransform<number, number>(
    [mouseX, mouseY],
    ([newX, newY]) => {
      const diffY = newY - position[1];
      const diffX = newX - position[0];
      const angleRadians = Math.atan2(diffY, diffX);
      const angleDegrees = Math.floor(angleRadians * (180 / Math.PI));
      return angleDegrees;
    }
  );

  useEffect(() => {
    if (!ref.current) return;
    const rect = ref.current.getBoundingClientRect();
    // center x coordinate
    const x = rect.left + CELL_SIZE / 2;
    // center y coordinate
    const y = rect.top + CELL_SIZE / 2;
    setPosition([x, y]);
  }, [ref.current]);

  return (
    <Container ref={ref}>
      <motion.div style={{ rotate: direction }}>_</motion.div>
    </Container>
  );
};

export default Cell;
