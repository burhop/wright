import { useState, useEffect } from "react";
import { useLocation } from "react-router-dom";
import StatusBar from "./StatusBar";
import useHealthStatus from "../../hooks/useHealthStatus";
import telemetry from "../../services/telemetry";
import type { TraceContext } from "../../store/types";
import { SplitIcon } from "../common/Icons";

const readPreference = (key: string) => {
  try {
    return window.localStorage.getItem(key);
  } catch {
    return null;
  }
};

export function Header() {
  const statuses = useHealthStatus();
  const [latestTrace, setLatestTrace] = useState<TraceContext | null>(null);
  const location = useLocation();
  const isWorkspaceView = location.pathname.startsWith("/workspace/");

  const [isSplit, setIsSplit] = useState(
    () => readPreference("wright-split-active") === "true",
  );

  useEffect(() => {
    const handleStateChange = (e: Event) => {
      const customEvent = e as CustomEvent;
      setIsSplit(customEvent.detail?.active ?? false);
    };
    window.addEventListener("wright-split-state-changed", handleStateChange);
    return () =>
      window.removeEventListener("wright-split-state-changed", handleStateChange);
  }, []);

  const handleToggleSplit = () => {
    window.dispatchEvent(new CustomEvent("wright-split-toggle"));
  };

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
        <span
          style={{
            fontSize: "0.65rem",
            fontWeight: "600",
            color: "var(--color-secondary)",
            border: "1px solid rgba(56, 189, 248, 0.3)",
            backgroundColor: "rgba(56, 189, 248, 0.05)",
            padding: "2px 8px",
            borderRadius: "20px",
            textTransform: "uppercase",
            letterSpacing: "1px",
            boxShadow: "var(--shadow-glow)",
          }}
        >
          LOCAL-FIRST
        </span>
      </div>

      <div
        style={{
          display: "flex",
          alignItems: "center",
          gap: "var(--space-md)",
        }}
      >
        {isWorkspaceView && (
          <button
            data-testid="split-view-toggle"
            onClick={handleToggleSplit}
            style={{
              background: "none",
              border: "1px solid var(--color-border)",
              borderRadius: "var(--radius-md)",
              color: isSplit ? "var(--color-secondary)" : "var(--color-primary)",
              opacity: isSplit ? 1 : 0.65,
              padding: "4px 12px",
              height: "30px",
              cursor: "pointer",
              display: "flex",
              alignItems: "center",
              gap: "6px",
              fontSize: "0.75rem",
              fontWeight: "600",
              boxShadow: isSplit ? "var(--shadow-glow)" : "none",
              transition: "all var(--transition-fast)",
            }}
            title="Toggle Onshape Split View"
          >
            <SplitIcon size={14} style={{ display: "inline-block" }} />
            <span>Split Onshape</span>
          </button>
        )}
        <StatusBar statuses={statuses} latestTrace={latestTrace} />
      </div>
    </header>
  );
}

export default Header;

