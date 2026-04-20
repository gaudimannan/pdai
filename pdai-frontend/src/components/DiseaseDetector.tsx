import { useEffect, useRef, useState } from "react";
import type { DiagnosisResult, LoadState } from "../types";
import { parsePercent, splitIssue } from "../utils";
import ErrorPanel from "./ErrorPanel";
import LoadingPanel from "./LoadingPanel";
import ProgressBar from "./ProgressBar";
import WindowPanel from "./WindowPanel";

const SAMPLE_IMAGES = [
  {
    title: "SAMPLE_001",
    url: "https://images.unsplash.com/photo-1416879595882-3373a0480b5b?w=200&q=80"
  },
  {
    title: "SAMPLE_002",
    url: "https://images.unsplash.com/photo-1530836369250-ef72a3f5cda8?w=200&q=80"
  },
  {
    title: "SAMPLE_003",
    url: "https://images.unsplash.com/photo-1574323347407-f5e1ad6d020b?w=200&q=80"
  }
];

export default function DiseaseDetector({ uploadSignal }: { uploadSignal: number }) {
  const uploadRef = useRef<HTMLInputElement>(null);
  const sectionRef = useRef<HTMLElement>(null);
  const [dragging, setDragging] = useState(false);
  const [file, setFile] = useState<File | null>(null);
  const [previewUrl, setPreviewUrl] = useState<string | null>(null);
  const [result, setResult] = useState<DiagnosisResult | null>(null);
  const [status, setStatus] = useState<LoadState>("idle");
  const [error, setError] = useState("");

  useEffect(() => {
    if (uploadSignal > 0) {
      sectionRef.current?.scrollIntoView({ behavior: "smooth", block: "start" });
      window.setTimeout(() => uploadRef.current?.click(), 250);
    }
  }, [uploadSignal]);

  useEffect(() => {
    return () => {
      if (previewUrl) URL.revokeObjectURL(previewUrl);
    };
  }, [previewUrl]);

  async function analyzeFile(nextFile: File) {
    if (!nextFile.type.startsWith("image/")) {
      setError("Only image files can be analyzed.");
      setStatus("error");
      return;
    }
    if (nextFile.size > 10 * 1024 * 1024) {
      setError("Image is larger than 10MB.");
      setStatus("error");
      return;
    }

    setFile(nextFile);
    setResult(null);
    setError("");
    setStatus("loading");
    const nextPreview = URL.createObjectURL(nextFile);
    setPreviewUrl((current) => {
      if (current) URL.revokeObjectURL(current);
      return nextPreview;
    });

    try {
      const body = new FormData();
      body.append("image", nextFile);
      const response = await fetch("/api/predict", { method: "POST", body });
      if (!response.ok) {
        const message = await response.text();
        throw new Error(message || "The diagnosis request failed.");
      }
      const data = (await response.json()) as DiagnosisResult;
      setResult(data);
      setStatus("success");
    } catch (requestError) {
      setError(requestError instanceof Error ? requestError.message : "The diagnosis request failed.");
      setStatus("error");
    }
  }

  function handleFileSelect(nextFile?: File) {
    if (nextFile) void analyzeFile(nextFile);
  }

  async function analyzeSample(url: string, title: string) {
    setStatus("loading");
    setError("");
    setResult(null);
    try {
      const response = await fetch(url);
      if (!response.ok) throw new Error("Sample image fetch failed.");
      const blob = await response.blob();
      const sampleFile = new File([blob], `${title}.jpg`, { type: blob.type || "image/jpeg" });
      await analyzeFile(sampleFile);
    } catch (sampleError) {
      setError(sampleError instanceof Error ? sampleError.message : "Sample image fetch failed.");
      setStatus("error");
    }
  }

  function retry() {
    if (file) void analyzeFile(file);
  }

  function reset() {
    setFile(null);
    setResult(null);
    setError("");
    setStatus("idle");
    setPreviewUrl((current) => {
      if (current) URL.revokeObjectURL(current);
      return null;
    });
  }

  return (
    <div className="tab-page">
      <section className="hero-grid">
        <div className="hero-copy">
          <span className="system-tag">[ SPECIMEN ANALYSIS SYSTEM v1.0 ]</span>
          <h1>
            Diagnose your plants.
            <br />
            Before the damage spreads.
          </h1>
          <div className="hero-rule" aria-hidden="true" />
          <p>
            Upload a leaf photograph. Our model — trained on 20,638 images across 15 plant-health classes —
            returns a diagnosis in under two seconds.
          </p>
          <button className="neo-button green-button hero-cta" type="button" onClick={() => uploadRef.current?.click()}>
            [ UPLOAD LEAF IMAGE ]
          </button>
          <span className="hero-caption">JPG or PNG · Max 10MB · Free</span>
        </div>

        <WindowPanel title="SPECIMEN_001.jpg · COMPLETE" className="hero-preview">
          <div className="specimen-image">[ LEAF_IMAGE.jpg ]</div>
          <div className="terminal-readout">
            <p>CLASS............Tomato</p>
            <p>CONDITION........Early Blight</p>
            <p>CONFIDENCE.......94.2%</p>
            <p>
              SEVERITY.........<strong className="yellow-text">MODERATE</strong>
            </p>
          </div>
          <div className="terminal-strip">DIAGNOSIS COMPLETE</div>
        </WindowPanel>
      </section>

      <section ref={sectionRef} className="content-section">
        <div className="section-label">[ 01 — UPLOAD SPECIMEN ]</div>
        <WindowPanel title="DROP_ZONE.exe">
          <button
            className={`drop-zone ${dragging ? "drop-zone-active" : ""}`}
            onClick={() => uploadRef.current?.click()}
            onDragEnter={(event) => {
              event.preventDefault();
              setDragging(true);
            }}
            onDragOver={(event) => event.preventDefault()}
            onDragLeave={() => setDragging(false)}
            onDrop={(event) => {
              event.preventDefault();
              setDragging(false);
              handleFileSelect(event.dataTransfer.files[0]);
            }}
            type="button"
          >
            <span>[ DROP LEAF IMAGE HERE ]</span>
            <small>or click to browse files</small>
          </button>
          <input
            ref={uploadRef}
            className="hidden-input"
            type="file"
            accept="image/png,image/jpeg"
            onChange={(event) => handleFileSelect(event.target.files?.[0])}
          />
        </WindowPanel>

        <div className="sample-grid">
          {SAMPLE_IMAGES.map((sample) => (
            <WindowPanel key={sample.title} title={sample.title} className="sample-card interactive">
              <button className="sample-button" type="button" onClick={() => void analyzeSample(sample.url, sample.title)}>
                <span role="img" aria-label="Leaf">
                  🍃
                </span>
              </button>
            </WindowPanel>
          ))}
        </div>

        {status === "loading" && <LoadingPanel title="ANALYZING.EXE · RUNNING..." message="Processing leaf specimen..." />}
        {status === "error" && <ErrorPanel message={error} onRetry={retry} />}
        {status === "success" && result && previewUrl && (
          <DiagnosisCard filename={file?.name || "SPECIMEN.jpg"} previewUrl={previewUrl} result={result} onReset={reset} />
        )}
      </section>

      <section className="content-section">
        <div className="section-label">[ 02 — PROCESS ]</div>
        <div className="process-grid">
          <ProcessStep title="STEP_01" number="01" heading="Photograph" copy="Capture one clear leaf against steady light." />
          <ProcessStep title="STEP_02" number="02" heading="Analyze" copy="The classifier reads surface patterns and lesion shapes." />
          <ProcessStep title="STEP_03" number="03" heading="Diagnose" copy="Review the status, confidence, and treatment notes." />
        </div>
      </section>

      <WindowPanel title="MODEL.STATS" className="stats-panel">
        <div className="stats-grid">
          <StatBlock value="20,638" label="TRAINING IMAGES" />
          <StatBlock value="15" label="MODEL CLASSES" />
          <StatBlock value="3" label="PLANT TYPES" />
        </div>
      </WindowPanel>
    </div>
  );
}

function DiagnosisCard({
  filename,
  previewUrl,
  result,
  onReset
}: {
  filename: string;
  previewUrl: string;
  result: DiagnosisResult;
  onReset: () => void;
}) {
  const confidence = parsePercent(result.confidence);
  const isHealthy = result.type === "healthy";
  const issue = splitIssue(result.issue);

  return (
    <div className="result-card">
      <WindowPanel title={`${filename} · ANALYSIS COMPLETE`}>
        <div className="diagnosis-layout">
          <div className="diagnosis-image-block">
            <img src={previewUrl} alt="Uploaded plant specimen" />
            <div className={`verdict ${isHealthy ? "healthy-text" : "danger-text"}`}>
              {isHealthy ? "Healthy." : "Diseased."}
            </div>
          </div>
          <div className="diagnosis-readout">
            <p>PLANT............{issue.plant}</p>
            <p>CONDITION........{issue.condition}</p>
            <p>STATUS...........{result.statusText}</p>
            <p>CONFIDENCE.......{result.confidence}</p>
            <p>SEVERITY.........{result.severity}</p>
            <ProgressBar value={confidence} tone={isHealthy ? "healthy" : "danger"} />
          </div>
        </div>
        <div className="treatment-grid">
          <WindowPanel title="ORGANIC TREATMENT" className="nested-panel">
            <p>{result.organic}</p>
          </WindowPanel>
          <WindowPanel title="CHEMICAL TREATMENT" className="nested-panel">
            <p>{result.chemical}</p>
          </WindowPanel>
        </div>
      </WindowPanel>
      <button className="neo-button ghost-button scan-again" type="button" onClick={onReset}>
        [ SCAN ANOTHER LEAF ]
      </button>
    </div>
  );
}

function ProcessStep({ title, number, heading, copy }: { title: string; number: string; heading: string; copy: string }) {
  return (
    <WindowPanel title={title} className="process-panel">
      <div className="process-number">{number}</div>
      <h3>{heading}</h3>
      <p>{copy}</p>
    </WindowPanel>
  );
}

function StatBlock({ value, label }: { value: string; label: string }) {
  return (
    <div className="stat-block">
      <strong>{value}</strong>
      <span>{label}</span>
    </div>
  );
}
