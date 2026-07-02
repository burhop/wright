import { useState, useEffect } from "react";
import StatusBar from "./StatusBar";
import useHealthStatus from "../../hooks/useHealthStatus";
import telemetry from "../../services/telemetry";
import type { TraceContext } from "../../store/types";

export function Header() {
  const statuses = useHealthStatus();
  const [latestTrace, setLatestTrace] = useState<TraceContext | null>(null);
  useEffect(() => {
    const interval = setInterval(() => {
      const recent = telemetry.getRecentTraces(1);
      if (recent.length > 0) {
        setLatestTrace(recent[0]);
      }
    }, 1000);

    return () => clearInterval(interval);
  }, []);

  return (
    <header
      data-testid="header"
      className="glass-panel"
      style={{
        height: "48px",
        borderBottom: "1px solid var(--color-border)",
        display: "flex",
        alignItems: "center",
        justifyContent: "space-between",
        padding: "0 var(--space-xl)",
        zIndex: 10,
        boxShadow: "0 2px 8px rgba(0, 0, 0, 0.2)",
      }}
    >
      <div
        style={{
          display: "flex",
          alignItems: "center",
          gap: "var(--space-md)",
        }}
      >
        <span
          style={{
            fontSize: "1rem",
            fontWeight: "700",
            letterSpacing: "1.5px",
            fontFamily: "var(--font-ui)",
            color: "var(--color-primary)",
            textShadow: "0 0 10px rgba(255, 255, 255, 0.1)",
          }}
        >
          WRIGHT
        </span>
      </div>

      <div
        style={{
          display: "flex",
          alignItems: "center",
          gap: "var(--space-md)",
        }}
      >
        <StatusBar statuses={statuses} latestTrace={latestTrace} />
      </div>
    </header>
  );
}

export default Header;
