import React, { useEffect, useRef } from "react";
import * as d3 from "d3";

type Props = {
  width?: number;
  height?: number;
  severity?: "ok" | "warn" | "critical";
};

// Overlay ligero para simular "hormigas" moviéndose.
export function D3Overlay({ width = 800, height = 360, severity = "ok" }: Props) {
  const ref = useRef<SVGSVGElement>(null);

  useEffect(() => {
    const svg = d3.select(ref.current);
    svg.selectAll("*").remove();
    svg.attr("width", width).attr("height", height);

    const color = severity === "critical" ? "#ef4444" : severity === "warn" ? "#f59e0b" : "#22d3ee";
    const ants = d3.range(18).map(() => ({
      x: Math.random() * width,
      y: Math.random() * height,
      dx: (Math.random() - 0.5) * 2,
      dy: (Math.random() - 0.5) * 2,
    }));

    const circles = svg
      .selectAll("circle")
      .data(ants)
      .enter()
      .append("circle")
      .attr("r", 2.5)
      .attr("fill", color)
      .attr("opacity", 0.6);

    let rafId: number;
    const tick = () => {
      ants.forEach((a) => {
        a.x += a.dx;
        a.y += a.dy;
        if (a.x < 0 || a.x > width) a.dx *= -1;
        if (a.y < 0 || a.y > height) a.dy *= -1;
      });
      circles.attr("cx", (d) => (d as any).x).attr("cy", (d) => (d as any).y);
      rafId = requestAnimationFrame(tick);
    };
    rafId = requestAnimationFrame(tick);
    return () => cancelAnimationFrame(rafId);
  }, [width, height, severity]);

  return <svg ref={ref} style={{ position: "absolute", inset: 0, pointerEvents: "none" }} />;
}
