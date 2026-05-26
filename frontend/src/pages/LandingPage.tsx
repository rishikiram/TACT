import { useNavigate } from "react-router-dom";

const cards: {
  title: string;
  description: string;
  route: string;
  badge: string;
  badgeColor: string;
}[] = [
  {
    title: "Live Explorer",
    description: "Directly search ClinicalTrials.gov.",
    route: "/live",
    badge: "Live",
    badgeColor: "#2e7d32",
  },
  {
    title: "Database Explorer",
    description: "Browse trials stored in the local database. Data is pre-ingested via a data pipeline.",
    route: "/db",
    badge: "SQLite",
    badgeColor: "#1565c0",
  },
];

export default function LandingPage() {
  const navigate = useNavigate();

  return (
    <div
      style={{
        minHeight: "100vh",
        display: "flex",
        flexDirection: "column",
        alignItems: "center",
        justifyContent: "center",
        padding: "40px 24px",
        textAlign: "center",
      }}
    >
      <h1 style={{ marginBottom: "8px", fontSize: "2rem" }}>Clinical Trial Explorer</h1>
      <p style={{ color: "var(--text)", marginBottom: "48px", maxWidth: "480px" }}>
        Choose a data source to explore clinical trial data interactively.
      </p>

      <div
        style={{
          display: "flex",
          gap: "24px",
          flexWrap: "wrap",
          justifyContent: "center",
          maxWidth: "800px",
          width: "100%",
        }}
      >
        {cards.map((card) => (
          <button
            key={card.route}
            onClick={() => navigate(card.route)}
            style={{
              flex: "1 1 300px",
              maxWidth: "340px",
              padding: "32px 28px",
              borderRadius: "12px",
              border: "2px solid var(--accent-border)",
              background: "var(--bg-card, #fff)",
              cursor: "pointer",
              textAlign: "left",
              transition: "background 0.15s, border-color 0.15s",
            }}
            onMouseEnter={(e) => {
              (e.currentTarget as HTMLButtonElement).style.background = "var(--accent-bg)";
              (e.currentTarget as HTMLButtonElement).style.borderColor = "var(--accent-bg)";
            }}
            onMouseLeave={(e) => {
              (e.currentTarget as HTMLButtonElement).style.background = "var(--bg-card, #fff)";
              (e.currentTarget as HTMLButtonElement).style.borderColor = "var(--accent-border)";
            }}
          >
            <span
              style={{
                display: "inline-block",
                padding: "2px 10px",
                borderRadius: "4px",
                background: card.badgeColor,
                color: "#fff",
                fontSize: "0.75rem",
                fontWeight: 600,
                marginBottom: "14px",
                letterSpacing: "0.04em",
              }}
            >
              {card.badge}
            </span>
            <h2 style={{ margin: "0 0 10px", fontSize: "1.25rem", color: "var(--text-h)" }}>
              {card.title}
            </h2>
            <p style={{ margin: 0, color: "var(--text)", fontSize: "0.95rem", lineHeight: 1.5 }}>
              {card.description}
            </p>
          </button>
        ))}
      </div>
    </div>
  );
}
