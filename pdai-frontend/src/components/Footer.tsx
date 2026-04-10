import { useMemo } from "react";

export default function Footer() {
  const year = useMemo(() => new Date().getFullYear(), []);

  return (
    <footer className="site-footer">
      <div className="footer-ghost" aria-hidden="true">
        PDAi
      </div>
      <strong>PDAi</strong>
      <span>Built on PlantVillage dataset · EfficientNet-B0 · {year}</span>
      <a href="https://github.com" target="_blank" rel="noreferrer">
        [GH]
      </a>
    </footer>
  );
}
