import styled from "@emotion/styled";

import { animate, motion, useMotionValue } from "framer-motion";
import { useEffect, useState } from "react";
import Cell, { CELL_SIZE } from "./Cell";

const Container = styled(motion.div)<{
  columns: number;
}>`
  position: absolute;
  top: 0;
  left: 0;
  width: 100vw;
  height: 100vh;
  overflow: hidden;
  display: grid;
  grid-template-columns: repeat(${(props) => props.columns}, 1fr);
`;

function Grid() {
  const [columns, setColumns] = useState(0);
  const [rows, setRows] = useState(0);

  // mouse position
  const mouseX = useMotionValue(0);
  const mouseY = useMotionValue(0);

  useEffect(() => {
    const handleMouseMove = (e: MouseEvent) => {
      // animate mouse x and y
      animate(mouseX, e.clientX);
      animate(mouseY, e.clientY);
    };
    // recalculate grid on resize
    window.addEventListener("mousemove", handleMouseMove);
    // cleanup
    return () => {
      window.removeEventListener("mousemove", handleMouseMove);
    };
  }, []);

  // determine rows and columns
  useEffect(() => {
    const calculateGrid = () => {
      const columnCount = Math.ceil(window.outerWidth / CELL_SIZE);
      setColumns(columnCount);
      const rowCount = Math.ceil(window.outerHeight / CELL_SIZE);
      setRows(rowCount);
    };
    // calculate the grid on load
    calculateGrid();
    // recalculate grid on resize
    window.addEventListener("resize", calculateGrid);
    // cleanup
    return () => {
      window.removeEventListener("resize", calculateGrid);
    };
  }, []);

  return (
    <Container columns={columns}>
      {Array.from({ length: columns * rows }).map((_, i) => (
        <Cell key={i} mouseX={mouseX} mouseY={mouseY} />
      ))}
    </Container>
  );
}

export default Grid;
