export type Tab = "disease" | "crop";
export type Theme = "light" | "dark";
export type LoadState = "idle" | "loading" | "success" | "error";

export type DiagnosisResult = {
  type: "healthy" | "diseased";
  issue: string;
  confidence: string;
  severity: string;
  statusText: "HEALTHY" | "SEVERE" | "CAUTION" | string;
  organic: string;
  chemical: string;
};

export type CropResult = {
  name: string;
  scientificName: string;
  score: string;
  description: string;
  suitability: string;
  yield: string;
};
