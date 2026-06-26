import { useEffect, useState, type ReactNode } from "react";
import { useLocation } from "react-router-dom";
import Header from "./Header";
import Sidebar from "./Sidebar";
import { webMcpService } from "../../services/webmcp-service";
import { isDesktop } from "../../services/host-adapter";

interface AppShellProps {
  children: ReactNode;
}

const getApiUrl = (path: string) => {
  if (typeof window === "undefined") return `http://127.0.0.1:8000${path}`;
  const host = window.location.hostname;
  const port = window.location.port;
  // If in dev mode, API server is on 8000. In production, same host/port.
  const base = port && port !== "8000" ? `http://${host}:8000` : "";
  return `${base}${path}`;
};

const readPreference = (key: string) => {
  try {
    return window.localStorage.getItem(key);
  } catch {
    return null;
  }
};

const writePreference = (key: string, value: string) => {
  try {
    window.localStorage.setItem(key, value);
  } catch {
    // Storage can be unavailable in restricted browser/test contexts.
  }
};

export function AppShell({ children }: AppShellProps) {
  const location = useLocation();
  const isWorkspaceView = location.pathname.startsWith("/workspace/");

  const [isSplit, setIsSplit] = useState(
    () => readPreference("wright-split-active") === "true",
  );
  const [splitPercent, setSplitPercent] = useState<number>(() => {
    const saved = readPreference("wright-split-percent");
    const parsed = saved ? parseFloat(saved) : Number.NaN;
    return Number.isFinite(parsed) ? parsed : 30;
  });
  const [isDragging, setIsDragging] = useState(false);


  useEffect(() => {
    webMcpService.connect();
    return () => {
      webMcpService.disconnect();
    };
  }, []);

  useEffect(() => {
    const handleToggle = () => {
      setIsSplit((prev) => {
        const next = !prev;
        writePreference("wright-split-active", next ? "true" : "false");
        window.dispatchEvent(
          new CustomEvent("wright-split-state-changed", {
            detail: { active: next },
          }),
        );
        return next;
      });
    };
    window.addEventListener("wright-split-toggle", handleToggle);
    return () => window.removeEventListener("wright-split-toggle", handleToggle);
  }, []);

  const handleMouseDown = (e: React.MouseEvent) => {
    e.preventDefault();
    setIsDragging(true);
  };

  useEffect(() => {
    if (!isDragging) return;

    const handleMouseMove = (e: MouseEvent) => {
      const containerWidth = window.innerWidth;
      if (containerWidth <= 0) return;
      const newPercent = (e.clientX / containerWidth) * 100;
      // Clamp percent between 5% and 95%
      const clampedPercent = Math.max(5, Math.min(95, newPercent));
      setSplitPercent(clampedPercent);
      writePreference("wright-split-percent", clampedPercent.toString());
    };

    const handleMouseUp = () => {
      setIsDragging(false);
    };

    window.addEventListener("mousemove", handleMouseMove);
    window.addEventListener("mouseup", handleMouseUp);

    return () => {
      window.removeEventListener("mousemove", handleMouseMove);
      window.removeEventListener("mouseup", handleMouseUp);
    };
  }, [isDragging]);

  const desktop = isDesktop();

  return (
    <div
      data-testid="app-shell"
      data-desktop={desktop}
      style={{
        display: "flex",
        flexDirection: "column",
        height: "100svh",
        width: "100vw",
        backgroundColor: "var(--color-neutral)",
        color: "var(--color-primary)",
        overflow: "hidden",
        paddingTop: desktop ? "var(--titlebar-height, 34px)" : "0px",
      }}
    >
      <Header />

      <div style={{ display: "flex", flex: 1, overflow: "hidden" }}>
        {!isWorkspaceView && <Sidebar />}

        {isWorkspaceView && isSplit ? (
          <div
            style={{
              display: "flex",
              flex: 1,
              overflow: "hidden",
              width: "100%",
            }}
          >
            {/* Left side: Wright UI */}
            <div
              style={{
                width: `${splitPercent}%`,
                display: "flex",
                flexDirection: "column",
                overflow: "hidden",
                position: "relative",
              }}
            >
              <main
                style={{
                  flex: 1,
                  overflowY: "auto",
                  padding: 0,
                  backgroundColor: "var(--color-neutral)",
                }}
              >
                {children}
              </main>
            </div>

            {/* Draggable Resizer Bar */}
            <div
              data-testid="split-resizer"
              style={{
                width: "6px",
                cursor: "col-resize",
                backgroundColor: isDragging
                  ? "var(--color-secondary)"
                  : "var(--color-border)",
                zIndex: 20,
                transition: "background-color 0.2s",
                position: "relative",
                userSelect: "none",
              }}
              onMouseDown={handleMouseDown}
            >
              <div
                style={{
                  position: "absolute",
                  left: "50%",
                  top: "50%",
                  transform: "translate(-50%, -50%)",
                  width: "2px",
                  height: "24px",
                  backgroundColor: "rgba(255, 255, 255, 0.3)",
                  borderRadius: "1px",
                }}
              />
            </div>

            {/* Right side: Onshape iframe */}
            <div
              style={{
                flex: 1,
                position: "relative",
                backgroundColor: "var(--color-neutral)",
                display: "flex",
                flexDirection: "column",
              }}
            >
              <iframe
                src={getApiUrl("/api/proxy/onshape")}
                title="Onshape UI"
                style={{
                  width: "100%",
                  height: "100%",
                  border: "none",
                  backgroundColor: "#ffffff",
                }}
              />
              {/* Invisible Overlay to capture drag events when mouse is over iframe */}
              {isDragging && (
                <div
                  style={{
                    position: "absolute",
                    top: 0,
                    left: 0,
                    right: 0,
                    bottom: 0,
                    zIndex: 30,
                    backgroundColor: "transparent",
                    cursor: "col-resize",
                  }}
                />
              )}
            </div>
          </div>
        ) : (
          <main
            style={{
              flex: 1,
              overflowY: "auto",
              padding: isWorkspaceView ? "0" : "var(--space-xl)",
              backgroundColor: "var(--color-neutral)",
            }}
          >
            {children}
          </main>
        )}
      </div>
    </div>
  );
}

export default AppShell;

