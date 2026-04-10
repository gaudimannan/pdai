import { useEffect, useState } from "react";

export default function ProgressBar({ value, tone }: { value: number; tone: "healthy" | "danger" }) {
  const [width, setWidth] = useState(0);

  useEffect(() => {
    const frame = window.requestAnimationFrame(() => setWidth(value));
    return () => window.cancelAnimationFrame(frame);
  }, [value]);

  return (
    <div className="meter" aria-label={`Score ${value}%`}>
      <div
        className={`meter-fill ${tone === "healthy" ? "meter-green" : "meter-red"}`}
        style={{ width: `${width}%` }}
      />
    </div>
  );
}
