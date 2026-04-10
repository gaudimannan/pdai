import { useEffect, useState } from "react";
import WindowPanel from "./WindowPanel";

export default function LoadingPanel({ title, message }: { title: string; message: string }) {
  const [step, setStep] = useState(1);

  useEffect(() => {
    const interval = window.setInterval(() => {
      setStep((current) => (current >= 10 ? 1 : current + 1));
    }, 200);
    return () => window.clearInterval(interval);
  }, []);

  const progress = step * 10;
  const bar = `${"■".repeat(step)}${"□".repeat(10 - step)}`;

  return (
    <WindowPanel title={title} className="loading-panel">
      <p className="ascii-progress">[{bar}] {progress}%</p>
      <p className="muted-copy">{message}</p>
    </WindowPanel>
  );
}
