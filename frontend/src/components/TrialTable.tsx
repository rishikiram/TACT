import { useState } from "react";
import type { Trial } from "../api/trials";

interface Props {
  trials: Trial[];
}

function JsonNode({ value, depth = 0 }: { value: unknown; depth?: number }) {
  const [collapsed, setCollapsed] = useState(depth > 0);

  if (value === null || value === undefined) {
    return <span style={{ color: "var(--text)" }}>null</span>;
  }

  if (typeof value !== "object") {
    const color = typeof value === "string" ? "#a8d8a8" : "#7ec8e3";
    return <span style={{ color }}>{JSON.stringify(value)}</span>;
  }

  const isArray = Array.isArray(value);
  const entries = isArray
    ? (value as unknown[]).map((v, i) => [String(i), v] as [string, unknown])
    : Object.entries(value as Record<string, unknown>);

  const brackets = isArray ? ["[", "]"] : ["{", "}"];
  const indent = "  ".repeat(depth);
  const innerIndent = "  ".repeat(depth + 1);

  if (entries.length === 0) {
    return <span style={{ color: "var(--text)" }}>{brackets[0]}{brackets[1]}</span>;
  }

  return (
    <span>
      <button
        onClick={() => setCollapsed(!collapsed)}
        style={{
          background: "none",
          border: "none",
          cursor: "pointer",
          padding: "0 2px",
          color: "var(--text)",
          font: "inherit",
          fontSize: "11px",
        }}
      >
        {collapsed ? "▶" : "▼"}
      </button>
      <span style={{ color: "var(--text)" }}>{brackets[0]}</span>
      {collapsed ? (
        <span
          style={{ color: "var(--text)", cursor: "pointer" }}
          onClick={() => setCollapsed(false)}
        >
          {isArray ? ` ${entries.length} items ` : " … "}
        </span>
      ) : (
        <>
          {entries.map(([k, v]) => (
            <div key={k} style={{ paddingLeft: "16px" }}>
              <span style={{ color: innerIndent ? "#c08645" : "#c08645" }}>
                {!isArray && `"${k}": `}
              </span>
              <JsonNode value={v} depth={depth + 1} />
              <span style={{ color: "var(--text)" }}>,</span>
            </div>
          ))}
          <div style={{ paddingLeft: `${depth * 16}px` }}></div>
        </>
      )}
      <span style={{ color: "var(--text)" }}>{indent}{brackets[1]}</span>
    </span>
  );
}

const PHASES = [1, 2, 3, 4] as const;
type PhaseNum = typeof PHASES[number];
const PHASE_KEYS: Record<PhaseNum, keyof Trial> = { 1: "phase1", 2: "phase2", 3: "phase3", 4: "phase4" };

export function TrialTable({ trials }: Props) {
  const [expandedId, setExpandedId] = useState<string | null>(null);
  const [jsonId, setJsonId] = useState<string | null>(null);
  const [phaseFilter, setPhaseFilter] = useState<Set<PhaseNum>>(new Set());

  const togglePhase = (p: PhaseNum) =>
    setPhaseFilter((prev) => {
      const next = new Set(prev);
      next.has(p) ? next.delete(p) : next.add(p);
      return next;
    });

  const visible =
    phaseFilter.size === 0
      ? trials
      : trials.filter((t) => [...phaseFilter].some((p) => t[PHASE_KEYS[p]]));

  if (trials.length === 0) {
    return <p style={{ padding: "16px", color: "var(--text)" }}>No trials to display.</p>;
  }

  return (
    <>
      <div style={{ display: "flex", gap: "16px", padding: "12px 16px", borderBottom: "1px solid var(--border)", alignItems: "center" }}>
        <span style={{ fontSize: "13px", color: "var(--text)", fontWeight: 600 }}>Phase:</span>
        {PHASES.map((p) => (
          <label key={p} style={{ display: "flex", alignItems: "center", gap: "5px", fontSize: "13px", color: "var(--text-h)", cursor: "pointer" }}>
            <input
              type="checkbox"
              checked={phaseFilter.has(p)}
              onChange={() => togglePhase(p)}
              style={{ accentColor: "var(--accent)", cursor: "pointer" }}
            />
            {p}
          </label>
        ))}
        {phaseFilter.size > 0 && (
          <span style={{ fontSize: "12px", color: "var(--text)", marginLeft: "auto" }}>
            {visible.length} / {trials.length}
          </span>
        )}
      </div>
      <ul style={{ listStyle: "none", padding: 0, margin: 0 }}>
      {visible.map((trial) => {
        const isOpen = expandedId === trial.nctId;
        const showJson = jsonId === trial.nctId;
        return (
          <li
            key={trial.nctId}
            style={{ borderBottom: "1px solid var(--border)" }}
          >
            <button
              onClick={() => setExpandedId(isOpen ? null : trial.nctId)}
              style={{
                width: "100%",
                textAlign: "left",
                padding: "14px 16px",
                background: "none",
                border: "none",
                cursor: "pointer",
                display: "flex",
                justifyContent: "space-between",
                alignItems: "center",
                gap: "12px",
                color: "var(--text-h)",
                font: "inherit",
              }}
            >
              <span style={{ flex: 1 }}>{trial.briefTitle}</span>
              <span style={{ fontSize: "12px", color: "var(--text)", whiteSpace: "nowrap" }}>
                {trial.overallStatus}
              </span>
              <span style={{ fontSize: "12px", color: "var(--text)" }}>
                {isOpen ? "▲" : "▼"}
              </span>
            </button>

            {isOpen && (
              <div
                style={{
                  padding: "0 16px 16px",
                  textAlign: "left",
                  fontSize: "15px",
                  display: "flex",
                  flexDirection: "column",
                  gap: "8px",
                }}
              >
                <div><strong>ID:</strong> {trial.nctId}</div>
                {trial.phases.length > 0 && (
                  <div><strong>Phase:</strong> {trial.phases.join(", ")}</div>
                )}
                {trial.conditions.length > 0 && (
                  <div><strong>Conditions:</strong> {trial.conditions.join(", ")}</div>
                )}
                {trial.locations.length > 0 && (
                  <div>
                    <strong>Sites:</strong> {trial.locations.length} location
                    {trial.locations.length !== 1 ? "s" : ""}
                  </div>
                )}
                {trial.briefSummary && (
                  <div>
                    <strong>Summary:</strong>
                    <p style={{ margin: "4px 0 0", color: "var(--text)" }}>{trial.briefSummary}</p>
                  </div>
                )}
                <div>
                  <button
                    onClick={() => setJsonId(showJson ? null : trial.nctId)}
                    style={{
                      marginTop: "4px",
                      padding: "4px 10px",
                      fontSize: "12px",
                      borderRadius: "4px",
                      border: "1px solid var(--border)",
                      background: "none",
                      color: "var(--text)",
                      cursor: "pointer",
                      font: "inherit",
                    }}
                  >
                    {showJson ? "Hide JSON" : "View JSON"}
                  </button>
                  {showJson && (
                    <pre
                      style={{
                        marginTop: "8px",
                        padding: "12px",
                        background: "var(--code-bg)",
                        borderRadius: "6px",
                        fontSize: "12px",
                        overflowX: "auto",
                        color: "var(--text-h)",
                        lineHeight: 1.5,
                      }}
                    >
                      <JsonNode value={trial} depth={0} />
                    </pre>
                  )}
                </div>
              </div>
            )}
          </li>
        );
      })}
    </ul>
    </>
  );
}
