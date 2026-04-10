import WindowPanel from "./WindowPanel";

export default function ErrorPanel({ message, onRetry }: { message: string; onRetry: () => void }) {
  return (
    <WindowPanel title="ERROR.EXE · FAILED" className="error-panel">
      <p className="error-message">{message || "Request failed."}</p>
      <button className="neo-button ghost-button" type="button" onClick={onRetry}>
        [ RETRY ]
      </button>
    </WindowPanel>
  );
}
