import { useEffect, useState } from "react";
import CropAdvisor from "./components/CropAdvisor";
import DiseaseDetector from "./components/DiseaseDetector";
import Footer from "./components/Footer";
import Nav from "./components/Nav";
import type { Tab, Theme } from "./types";

function App() {
  const [tab, setTab] = useState<Tab>("disease");
  const [uploadSignal, setUploadSignal] = useState(0);
  const [theme, setTheme] = useState<Theme>(() =>
    document.documentElement.getAttribute("data-theme") === "dark" ? "dark" : "light"
  );

  useEffect(() => {
    if (theme === "dark") {
      document.documentElement.setAttribute("data-theme", "dark");
    } else {
      document.documentElement.removeAttribute("data-theme");
    }
    localStorage.setItem("pdai-theme", theme);
  }, [theme]);

  function openUpload() {
    setTab("disease");
    window.setTimeout(() => setUploadSignal((current) => current + 1), 0);
  }

  return (
    <div className="app-shell">
      <Nav
        activeTab={tab}
        onTabChange={setTab}
        theme={theme}
        onThemeToggle={() => setTheme((current) => (current === "dark" ? "light" : "dark"))}
        onUpload={openUpload}
      />

      <main className="app-main">
        {tab === "disease" ? <DiseaseDetector uploadSignal={uploadSignal} /> : <CropAdvisor />}
      </main>

      <Footer />
    </div>
  );
}

export default App;
