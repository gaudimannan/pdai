import type { ReactNode } from "react";

type WindowPanelProps = {
  title: string;
  children: ReactNode;
  className?: string;
};

export default function WindowPanel({ title, children, className = "" }: WindowPanelProps) {
  return (
    <section className={`window-panel ${className}`.trim()}>
      <div className="window-titlebar">
        <div className="chrome-dots" aria-hidden="true">
          <span className="chrome-dot chrome-dot-red" />
          <span className="chrome-dot chrome-dot-yellow" />
          <span className="chrome-dot chrome-dot-green" />
        </div>
        <span className="window-title">{title}</span>
      </div>
      <div className="window-content">{children}</div>
    </section>
  );
}
