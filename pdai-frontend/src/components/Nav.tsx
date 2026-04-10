import type { Tab, Theme } from "../types";

type NavProps = {
  activeTab: Tab;
  onTabChange: (tab: Tab) => void;
  theme: Theme;
  onThemeToggle: () => void;
  onUpload: () => void;
};

export default function Nav({ activeTab, onTabChange, theme, onThemeToggle, onUpload }: NavProps) {
  return (
    <header className="site-header">
      <div className="site-nav">
        <button className="brand-button" onClick={() => onTabChange("disease")} type="button">
          PDAi
        </button>
        <div className="nav-rule" aria-hidden="true" />
        <div className="nav-actions">
          <button className="icon-button" onClick={onThemeToggle} type="button" aria-label="Toggle dark mode">
            {theme === "dark" ? "☀" : "☽"}
          </button>
          <button className="neo-button green-button nav-upload" onClick={onUpload} type="button">
            [ UPLOAD SPECIMEN →]
          </button>
        </div>
      </div>
      <nav className="tab-bar" aria-label="Primary">
        <button
          className={`tab-button ${activeTab === "disease" ? "is-active" : ""}`}
          onClick={() => onTabChange("disease")}
          type="button"
        >
          <span className="tab-full">DISEASE DETECTOR</span>
          <span className="tab-short">D-01</span>
        </button>
        <button
          className={`tab-button ${activeTab === "crop" ? "is-active" : ""}`}
          onClick={() => onTabChange("crop")}
          type="button"
        >
          <span className="tab-full">CROP ADVISOR</span>
          <span className="tab-short">C-02</span>
        </button>
      </nav>
    </header>
  );
}
