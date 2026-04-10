import { useState } from "react";
import type { CropResult, LoadState } from "../types";
import { parsePercent } from "../utils";
import ErrorPanel from "./ErrorPanel";
import LoadingPanel from "./LoadingPanel";
import ProgressBar from "./ProgressBar";
import WindowPanel from "./WindowPanel";

export default function CropAdvisor() {
  const [temperature, setTemperature] = useState("");
  const [humidity, setHumidity] = useState("");
  const [rainfall, setRainfall] = useState("");
  const [weatherStatus, setWeatherStatus] = useState<LoadState>("idle");
  const [weatherMessage, setWeatherMessage] = useState("");
  const [results, setResults] = useState<CropResult[]>([]);
  const [status, setStatus] = useState<LoadState>("idle");
  const [error, setError] = useState("");

  const canSubmit = temperature.trim() !== "" && humidity.trim() !== "" && rainfall.trim() !== "";

  async function submit() {
    if (!canSubmit) {
      setError("Enter temperature, humidity, and rainfall before analysis.");
      setStatus("error");
      return;
    }

    setStatus("loading");
    setError("");
    setResults([]);

    try {
      const response = await fetch("/api/recommend", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          temperature: Number(temperature),
          humidity: Number(humidity),
          rainfall: Number(rainfall)
        })
      });
      if (!response.ok) {
        const message = await response.text();
        throw new Error(message || "Crop recommendation failed.");
      }
      const data = (await response.json()) as { crops: CropResult[] };
      setResults(data.crops || []);
      setStatus("success");
    } catch (requestError) {
      setError(requestError instanceof Error ? requestError.message : "Crop recommendation failed.");
      setStatus("error");
    }
  }

  async function useCurrentWeather() {
    if (!navigator.geolocation) {
      setWeatherStatus("error");
      setWeatherMessage("[GEOLOCATION NOT SUPPORTED]");
      return;
    }

    setWeatherStatus("loading");
    setWeatherMessage("[FETCHING WEATHER DATA...]");

    try {
      const position = await new Promise<GeolocationPosition>((resolve, reject) => {
        navigator.geolocation.getCurrentPosition(resolve, reject, {
          enableHighAccuracy: false,
          timeout: 10000,
          maximumAge: 300000
        });
      });

      const { latitude, longitude } = position.coords;
      const weatherUrl = new URL("https://api.open-meteo.com/v1/forecast");
      weatherUrl.searchParams.set("latitude", latitude.toString());
      weatherUrl.searchParams.set("longitude", longitude.toString());
      weatherUrl.searchParams.set("current", "temperature_2m,relative_humidity_2m,rain");
      weatherUrl.searchParams.set("timezone", "auto");

      const response = await fetch(weatherUrl.toString());
      if (!response.ok) throw new Error("Weather API request failed.");

      const data = (await response.json()) as {
        current?: {
          temperature_2m?: number;
          relative_humidity_2m?: number;
          rain?: number;
        };
      };

      const current = data.current || {};
      setTemperature(formatWeatherValue(current.temperature_2m ?? 25));
      setHumidity(formatWeatherValue(current.relative_humidity_2m ?? 70));
      setRainfall(formatWeatherValue(current.rain && current.rain > 0 ? current.rain : 100));

      const label = await resolveLocationLabel(latitude, longitude);
      setWeatherStatus("success");
      setWeatherMessage(`[LOCATION DETECTED: ${label}]`);
    } catch (requestError) {
      setWeatherStatus("error");
      setWeatherMessage(
        requestError instanceof Error ? `[WEATHER FETCH FAILED: ${requestError.message}]` : "[WEATHER FETCH FAILED]"
      );
    }
  }

  return (
    <div className="tab-page crop-page">
      <section className="crop-hero">
        <span className="system-tag">[ CROP RECOMMENDATION SYSTEM ]</span>
        <h1>Find the right crop for your conditions.</h1>
      </section>

      <WindowPanel title="WEATHER_INPUT.exe">
        <form
          className="weather-form"
          onSubmit={(event) => {
            event.preventDefault();
            void submit();
          }}
        >
          <FieldInput label="Temperature (°C)" value={temperature} onChange={setTemperature} placeholder="25" />
          <FieldInput label="Humidity (%)" value={humidity} onChange={setHumidity} placeholder="70" />
          <FieldInput label="Rainfall (mm)" value={rainfall} onChange={setRainfall} placeholder="100" />
          <div className="location-row">
            <button
              className="neo-button ghost-button location-button"
              type="button"
              disabled={weatherStatus === "loading"}
              onClick={() => void useCurrentWeather()}
            >
              {weatherStatus === "loading" ? "[ FETCHING WEATHER DATA... ]" : "[ USE MY LOCATION ]"}
            </button>
            {weatherMessage && (
              <p className={`location-status ${weatherStatus === "error" ? "location-error" : "location-success"}`}>
                {weatherMessage}
              </p>
            )}
          </div>
          <button className="neo-button green-button analyze-button" type="submit">
            [ ANALYZE CONDITIONS →]
          </button>
        </form>
      </WindowPanel>

      {status === "loading" && <LoadingPanel title="CROP_MODEL.EXE · RUNNING..." message="Processing weather inputs..." />}
      {status === "error" && <ErrorPanel message={error} onRetry={() => void submit()} />}
      {status === "success" && (
        <WindowPanel title="CROP_RECOMMENDATIONS.exe" className="crop-results">
          {results.length === 0 ? (
            <p className="muted-copy">No crop recommendations returned.</p>
          ) : (
            <div className="crop-card-grid">
              {results.slice(0, 3).map((crop) => (
                <CropCard key={crop.name} crop={crop} />
              ))}
            </div>
          )}
        </WindowPanel>
      )}
    </div>
  );
}

function formatWeatherValue(value: number) {
  return Number.isInteger(value) ? String(value) : value.toFixed(1);
}

async function resolveLocationLabel(latitude: number, longitude: number) {
  const fallback = `${latitude.toFixed(2)}, ${longitude.toFixed(2)}`;

  try {
    const url = new URL("https://nominatim.openstreetmap.org/reverse");
    url.searchParams.set("format", "jsonv2");
    url.searchParams.set("lat", latitude.toString());
    url.searchParams.set("lon", longitude.toString());
    url.searchParams.set("zoom", "10");

    const response = await fetch(url.toString(), { headers: { "Accept-Language": "en" } });
    if (!response.ok) return fallback;

    const data = (await response.json()) as {
      address?: {
        city?: string;
        town?: string;
        village?: string;
        state?: string;
        country?: string;
      };
    };
    const address = data.address || {};
    const city = address.city || address.town || address.village || address.state;
    return [city, address.country].filter(Boolean).join(", ") || fallback;
  } catch {
    return fallback;
  }
}

function FieldInput({
  label,
  value,
  onChange,
  placeholder
}: {
  label: string;
  value: string;
  onChange: (value: string) => void;
  placeholder: string;
}) {
  return (
    <label className="field-label">
      <span>{label}</span>
      <input
        type="number"
        value={value}
        onChange={(event) => onChange(event.target.value)}
        placeholder={placeholder}
        step="any"
      />
    </label>
  );
}

function CropCard({ crop }: { crop: CropResult }) {
  const score = parsePercent(crop.score);
  return (
    <WindowPanel title={crop.name.toUpperCase()} className="crop-card nested-panel">
      <div className="crop-readout">
        <p>MATCH SCORE......{crop.score}</p>
        <p>SUITABILITY......{crop.suitability}</p>
        <p>YIELD............{crop.yield}</p>
        <p className="crop-science">{crop.scientificName}</p>
        <strong>DESCRIPTION</strong>
        <p>{crop.description}</p>
        <ProgressBar value={score} tone="healthy" />
      </div>
    </WindowPanel>
  );
}
