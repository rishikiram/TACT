import { useState, useEffect } from "react";
import { Link } from "react-router-dom";
import { fetchDictionary } from "../api/dbTrials";
import type { DictionaryColumn, DictionaryResult } from "../api/dbTrials";

function AnnotationRow({ label, value }: { label: string; value: string }) {
  return (
    <div style={{ display: "flex", gap: "12px", padding: "4px 0" }}>
      <span style={{ minWidth: "140px", fontWeight: 600, color: "var(--text-h)", fontSize: "0.85rem" }}>
        {label}
      </span>
      <span style={{ color: value ? "var(--text-h)" : "var(--text)", fontSize: "0.85rem", opacity: value ? 1 : 0.4 }}>
        {value || "—"}
      </span>
    </div>
  );
}

function DictionaryRow({ col }: { col: DictionaryColumn }) {
  const [expanded, setExpanded] = useState(false);
  const hasAnnotations = col.source || col.derivation || col.plainDescription;

  return (
    <>
      <tr
        onClick={() => setExpanded((e) => !e)}
        style={{ cursor: "pointer", borderBottom: "1px solid var(--border)" }}
      >
        <td style={tdStyle}>
          <span style={{ fontFamily: "monospace", fontWeight: 600, fontSize: "0.9rem" }}>
            {col.name}
          </span>
          {hasAnnotations && (
            <span style={{ marginLeft: "6px", fontSize: "0.7rem", color: "var(--text)", opacity: 0.6 }}>
              {expanded ? "▲" : "▼"}
            </span>
          )}
        </td>
        <td style={tdStyle}>
          <span style={{ fontFamily: "monospace", fontSize: "0.85rem", color: "var(--text)" }}>
            {col.type || "—"}
          </span>
        </td>
        <td style={tdStyle}>
          {col.nullCount} ({col.nullPct}%)
        </td>
        <td style={tdStyle}>{col.uniqueCount}</td>
        <td style={{ ...tdStyle, color: "var(--text)", fontSize: "0.85rem", maxWidth: "260px" }}>
          {col.sampleValues.length > 0 ? col.sampleValues.join(", ") : <span style={{ opacity: 0.4 }}>—</span>}
        </td>
      </tr>
      {expanded && (
        <tr style={{ background: "var(--accent-bg, #f5f8ff)" }}>
          <td colSpan={5} style={{ padding: "12px 16px 16px", borderBottom: "1px solid var(--border)" }}>
            <AnnotationRow label="Source" value={col.source} />
            <AnnotationRow label="Derivation" value={col.derivation} />
            <AnnotationRow label="Plain description" value={col.plainDescription} />
          </td>
        </tr>
      )}
    </>
  );
}

const tdStyle: React.CSSProperties = {
  padding: "10px 14px",
  verticalAlign: "middle",
  fontSize: "0.9rem",
  color: "var(--text-h)",
};

const thStyle: React.CSSProperties = {
  padding: "10px 14px",
  textAlign: "left",
  fontSize: "0.8rem",
  fontWeight: 600,
  color: "var(--text)",
  borderBottom: "2px solid var(--border)",
  whiteSpace: "nowrap",
};

export default function DataDictionary() {
  const [result, setResult] = useState<DictionaryResult | null>(null);
  const [error, setError] = useState(false);
  const [search, setSearch] = useState("");

  useEffect(() => {
    fetchDictionary()
      .then(setResult)
      .catch(() => setError(true));
  }, []);

  const filtered = result?.columns.filter((col) => {
    const q = search.toLowerCase();
    return (
      col.name.toLowerCase().includes(q) ||
      col.source.toLowerCase().includes(q) ||
      col.derivation.toLowerCase().includes(q) ||
      col.plainDescription.toLowerCase().includes(q)
    );
  }) ?? [];

  return (
    <div style={{ padding: "24px", textAlign: "left" }}>
      <Link
        to="/"
        style={{ position: "fixed", top: "16px", left: "16px", fontSize: "0.875rem", color: "var(--text)", textDecoration: "none", zIndex: 100 }}
      >
        ← Back
      </Link>

      <div style={{ display: "flex", alignItems: "center", gap: "16px", marginBottom: "24px" }}>
        <h1 style={{ marginTop: 0, marginBottom: 0 }}>Data Dictionary</h1>
        {result && (
          <span style={{ padding: "2px 10px", borderRadius: "4px", background: "#6a1b9a", color: "#fff", fontSize: "0.75rem", fontWeight: 600, letterSpacing: "0.04em" }}>
            {result.totalRows} records
          </span>
        )}
      </div>

      {error && (
        <p style={{ color: "red" }}>
          Could not reach the database API. Make sure the FastAPI server is running:{" "}
          <code>cd backend_py && uvicorn api:app --reload --port 8010</code>
        </p>
      )}

      {!result && !error && <p>Loading…</p>}

      {result && (
        <>
          <input
            type="text"
            placeholder="Search columns, descriptions, sources…"
            value={search}
            onChange={(e) => setSearch(e.target.value)}
            style={{
              width: "100%",
              maxWidth: "420px",
              padding: "8px 12px",
              marginBottom: "20px",
              borderRadius: "6px",
              border: "1px solid var(--border)",
              font: "inherit",
              fontSize: "0.9rem",
              background: "none",
              color: "var(--text-h)",
              boxSizing: "border-box",
            }}
          />

          <div style={{ border: "1px solid var(--border)", borderRadius: "8px", overflow: "hidden" }}>
            <table style={{ width: "100%", borderCollapse: "collapse" }}>
              <thead>
                <tr style={{ background: "var(--bg-card, #fafafa)" }}>
                  <th style={thStyle}>Column</th>
                  <th style={thStyle}>Type</th>
                  <th style={thStyle}>Nulls</th>
                  <th style={thStyle}>Unique</th>
                  <th style={thStyle}>Sample Values</th>
                </tr>
              </thead>
              <tbody>
                {filtered.map((col) => (
                  <DictionaryRow key={col.name} col={col} />
                ))}
                {filtered.length === 0 && (
                  <tr>
                    <td colSpan={5} style={{ padding: "24px", textAlign: "center", color: "var(--text)", opacity: 0.5 }}>
                      No columns match "{search}"
                    </td>
                  </tr>
                )}
              </tbody>
            </table>
          </div>
          <p style={{ marginTop: "10px", fontSize: "0.8rem", color: "var(--text)", opacity: 0.6 }}>
            Click a row to expand source, derivation, and plain-language description.
          </p>
        </>
      )}
    </div>
  );
}
