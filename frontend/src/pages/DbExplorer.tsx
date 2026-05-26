import { useState, useEffect } from "react";
import { Link } from "react-router-dom";
import { useDbTrials } from "../hooks/useDbTrials";
import { fetchDbPresets } from "../api/dbTrials";
import { TrialTable } from "../components/TrialTable";
import { UsStatesMap } from "../components/maps/UsStatesMap";
import { HeatMap } from "../components/maps/HeatMap";
import { ScatterMap } from "../components/maps/ScatterMap";

const MAPS = ["Choropleth", "Heatmap", "Scatter"] as const;
type MapView = typeof MAPS[number];

function ToggleBar<T extends string>({
  options,
  selected,
  onSelect,
}: {
  options: readonly T[];
  selected: T;
  onSelect: (v: T) => void;
}) {
  return (
    <div style={{ display: "flex", gap: "8px", flexWrap: "wrap" }}>
      {options.map((opt) => (
        <button
          key={opt}
          onClick={() => onSelect(opt)}
          style={{
            padding: "6px 14px",
            borderRadius: "6px",
            border: "2px solid var(--accent-border)",
            background: selected === opt ? "var(--accent-bg)" : "none",
            color: "var(--text-h)",
            cursor: "pointer",
            font: "inherit",
            fontWeight: selected === opt ? 600 : 400,
          }}
        >
          {opt}
        </button>
      ))}
    </div>
  );
}

export default function DbExplorer() {
  const [presets, setPresets] = useState<string[]>([]);
  const [presetsError, setPresetsError] = useState(false);
  const [selectedPreset, setSelectedPreset] = useState<string>("");
  const [mapView, setMapView] = useState<MapView>("Choropleth");

  useEffect(() => {
    fetchDbPresets()
      .then((list) => {
        setPresets(list);
        if (list.length > 0) setSelectedPreset(list[0]);
      })
      .catch(() => setPresetsError(true));
  }, []);

  const { data, isLoading, isError } = useDbTrials({ preset: selectedPreset });
  const trials = data?.trials ?? [];

  const presetLabel = (p: string) =>
    p.replace(/_/g, " ").replace(/\b\w/g, (c) => c.toUpperCase());

  return (
    <div style={{ padding: "24px", textAlign: "left" }}>
      <div style={{ display: "flex", alignItems: "center", gap: "16px", marginBottom: "4px" }}>
        <h1 style={{ marginTop: 0, marginBottom: "2rem" }}>Clinical Trial Explorer</h1>
        <span
          style={{
            padding: "2px 10px",
            borderRadius: "4px",
            background: "#1565c0",
            color: "#fff",
            fontSize: "0.75rem",
            fontWeight: 600,
            letterSpacing: "0.04em",
          }}
        >
          SQLite
        </span>
      </div>
      <Link
        to="/"
        style={{ position: "fixed", top: "16px", left: "16px", fontSize: "0.875rem", color: "var(--text)", textDecoration: "none", zIndex: 100 }}
      >
        ← Back
      </Link>

      {presetsError && (
        <p style={{ color: "red" }}>
          Could not reach the database API. Make sure the FastAPI server is running:{" "}
          <code>cd backend_py && uvicorn api:app --reload --port 8010</code>
        </p>
      )}

      {presets.length > 0 && (
        <div style={{ display: "flex", flexDirection: "column", gap: "12px", marginBottom: "24px" }}>
          <ToggleBar
            options={presets.map(presetLabel) as unknown as readonly string[]}
            selected={presetLabel(selectedPreset)}
            onSelect={(label) => {
              const match = presets.find((p) => presetLabel(p) === label);
              if (match) setSelectedPreset(match);
            }}
          />
          <ToggleBar options={MAPS} selected={mapView} onSelect={setMapView} />
        </div>
      )}

      {isLoading && <p>Loading trials…</p>}
      {isError && <p style={{ color: "red" }}>Failed to load trials from database.</p>}

      {!isLoading && !isError && trials.length > 0 && (
        <>
          <p style={{ marginBottom: "16px", color: "var(--text)" }}>
            {trials.length} trial{trials.length !== 1 ? "s" : ""}
          </p>

          {mapView === "Choropleth" && <UsStatesMap trials={trials} />}
          {mapView === "Heatmap" && <HeatMap trials={trials} />}
          {mapView === "Scatter" && <ScatterMap trials={trials} />}

          <div style={{ marginTop: "24px", border: "1px solid var(--border)", borderRadius: "8px", overflow: "hidden" }}>
            <TrialTable trials={trials} />
          </div>
        </>
      )}
    </div>
  );
}
