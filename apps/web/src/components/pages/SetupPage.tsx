import React, { useState, useEffect } from "react";

const getApiUrl = (path: string) => {
  if (typeof window === "undefined") return `http://127.0.0.1:8000${path}`;
  const host = window.location.hostname;
  const port = window.location.port;
  const base = port === "5173" || port === "5174" ? `http://${host}:8000` : "";
  return `${base}${path}`;
};

interface SetupPageProps {
  onConfigured: () => void;
}

const SetupPage: React.FC<SetupPageProps> = ({ onConfigured }) => {
  const [llmUrl, setLlmUrl] = useState("");
  const [selectedAgent, setSelectedAgent] = useState("hermes");
  const [healthStatus, setHealthStatus] = useState<
    "idle" | "checking" | "healthy" | "unhealthy"
  >("idle");
  const [latency, setLatency] = useState<number | null>(null);
  const [errorMsg, setErrorMsg] = useState<string | null>(null);
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [submitError, setSubmitError] = useState<string | null>(null);
  const canContinue = selectedAgent === "hermes" || healthStatus === "healthy";

  // Load initial settings if present
  useEffect(() => {
    fetch(getApiUrl("/api/setup/status"))
      .then((res) => res.json())
      .then((data) => {
        if (data.llm_api_url) {
          setLlmUrl(data.llm_api_url);
        }
        if (data.active_agent) {
          setSelectedAgent(data.active_agent);
        }
      })
      .catch(() => {});
  }, []);

  // Debounced health check
  useEffect(() => {
    if (!llmUrl.trim()) {
      setHealthStatus("idle");
      setErrorMsg(null);
      setLatency(null);
      return;
    }

    setHealthStatus("checking");
    setErrorMsg(null);

    const timer = setTimeout(async () => {
      try {
        const response = await fetch(
          getApiUrl(`/api/setup/health?url=${encodeURIComponent(llmUrl)}`),
        );
        if (!response.ok) {
          throw new Error(`Server returned HTTP ${response.status}`);
        }
        const data = await response.json();
        if (data.status === "healthy") {
          setHealthStatus("healthy");
          setLatency(Math.round(data.latency_ms));
          setErrorMsg(null);
        } else {
          setHealthStatus("unhealthy");
          setErrorMsg(data.error || "Connection failed. Verify host and port.");
          setLatency(null);
        }
      } catch (err: any) {
        setHealthStatus("unhealthy");
        setErrorMsg(
          err.message || "Failed to connect to health check endpoint.",
        );
        setLatency(null);
      }
    }, 600);

    return () => clearTimeout(timer);
  }, [llmUrl]);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!canContinue) return;

    setIsSubmitting(true);
    setSubmitError(null);

    try {
      const response = await fetch(getApiUrl("/api/setup/configure"), {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify({
          llm_api_url: llmUrl,
          active_agent: selectedAgent,
        }),
      });

      if (!response.ok) {
        const errData = await response.json();
        throw new Error(errData.detail || "Failed to save configuration");
      }

      onConfigured();
    } catch (err: any) {
      setSubmitError(
        err.message || "An error occurred while saving the configuration.",
      );
    } finally {
      setIsSubmitting(false);
    }
  };

  return (
    <div style={styles.container}>
      <div style={styles.backgroundGlow} />

      <div style={styles.card} className="glass-panel animate-fade-in-up">
        <div style={styles.header}>
          <div style={styles.logoContainer}>
            <span style={styles.logoText}>W</span>
          </div>
          <h1 style={styles.title}>Welcome to Wright</h1>
          <p style={styles.subtitle}>
            Activate your workspace agent and optionally connect an LLM host.
          </p>
        </div>

        <form onSubmit={handleSubmit} style={styles.form}>
          {/* LLM URL Field */}
          <div style={styles.formGroup}>
            <label style={styles.label}>LLM Inference Host API URL</label>
            <div style={styles.inputContainer}>
              <input
                type="text"
                value={llmUrl}
                onChange={(e) => setLlmUrl(e.target.value)}
                placeholder="e.g. http://localhost:8000"
                style={{
                  ...styles.input,
                  borderColor:
                    healthStatus === "healthy"
                      ? "var(--color-success)"
                      : healthStatus === "unhealthy"
                        ? "var(--color-error)"
                        : "var(--color-border)",
                }}
                disabled={isSubmitting}
              />

              {/* Status Indicator inside/beside the input */}
              <div style={styles.indicatorContainer}>
                {healthStatus === "checking" && (
                  <span style={styles.checkingText}>
                    <span className="thinking-dot" />
                    <span className="thinking-dot" />
                    <span className="thinking-dot" />
                  </span>
                )}
                {healthStatus === "healthy" && (
                  <span style={styles.healthyBadge}>
                    <span
                      style={styles.successDot}
                      className="pulse-success-glow"
                    />
                    Connected {latency !== null ? `(${latency}ms)` : ""}
                  </span>
                )}
                {healthStatus === "unhealthy" && (
                  <span style={styles.errorBadge}>Disconnected</span>
                )}
              </div>
            </div>

            {errorMsg && (
              <div style={styles.errorText}>
                <strong>Connection Error:</strong> {errorMsg}
                <div style={styles.helpText}>
                  Ensure the LLM API is running, accepts CORS, or uses the
                  correct port (e.g. 8000/v1).
                </div>
              </div>
            )}
            {selectedAgent === "hermes" && !llmUrl.trim() && (
              <div style={styles.helpNote}>
                Hermes is already the workspace agent. You can add an LLM host
                later from settings.
              </div>
            )}
          </div>

          {/* Agent Selection Grid */}
          <div style={styles.formGroup}>
            <label style={styles.label}>Select Workspace Agent Engine</label>
            <div style={styles.agentGrid}>
              {/* Hermes Option */}
              <div
                style={{
                  ...styles.agentCard,
                  borderColor:
                    selectedAgent === "hermes"
                      ? "var(--color-secondary)"
                      : "var(--color-border)",
                  backgroundColor:
                    selectedAgent === "hermes"
                      ? "rgba(56, 189, 248, 0.05)"
                      : "var(--color-surface-subtle)",
                  cursor: "pointer",
                }}
                onClick={() => setSelectedAgent("hermes")}
              >
                <div style={styles.agentHeader}>
                  <strong style={styles.agentName}>Hermes</strong>
                  <span style={styles.recommendedBadge}>Active</span>
                </div>
                <p style={styles.agentDesc}>
                  Fully-integrated workspace agent supporting files, Git tools,
                  and full-loop CAD operations.
                </p>
              </div>

              {/* OpenClaw (Disabled) */}
              <div
                style={{
                  ...styles.agentCard,
                  ...styles.disabledAgentCard,
                }}
              >
                <div style={styles.agentHeader}>
                  <strong style={styles.agentName}>OpenClaw</strong>
                  <span style={styles.comingSoonBadge}>Coming Soon</span>
                </div>
                <p style={styles.agentDesc}>
                  Agent scaffolding for autonomous tool use and external
                  platform bridges.
                </p>
              </div>

              {/* Pi (Disabled) */}
              <div
                style={{
                  ...styles.agentCard,
                  ...styles.disabledAgentCard,
                }}
              >
                <div style={styles.agentHeader}>
                  <strong style={styles.agentName}>Pi</strong>
                  <span style={styles.comingSoonBadge}>Coming Soon</span>
                </div>
                <p style={styles.agentDesc}>
                  Optimized micro-agent framework for light-weight local code
                  search & execution.
                </p>
              </div>
            </div>
          </div>

          {submitError && (
            <div style={styles.submitErrorAlert}>{submitError}</div>
          )}

          {/* Action Button */}
          <div style={styles.actionContainer}>
            <button
              type="submit"
              disabled={!canContinue || isSubmitting}
              style={{
                ...styles.button,
                backgroundColor: canContinue
                  ? "var(--color-secondary)"
                  : "#1e293b",
                color: canContinue ? "#090D16" : "#64748b",
                cursor: canContinue ? "pointer" : "not-allowed",
                boxShadow: canContinue
                  ? "0 0 15px rgba(56, 189, 248, 0.3)"
                  : "none",
              }}
            >
              {isSubmitting ? "Saving..." : "Next "}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
};

const styles: { [key: string]: React.CSSProperties } = {
  container: {
    display: "flex",
    alignItems: "center",
    justifyContent: "center",
    minHeight: "100vh",
    width: "100%",
    backgroundColor: "var(--color-neutral)",
    position: "relative",
    overflow: "hidden",
    fontFamily: "var(--font-ui)",
    padding: "20px",
  },
  backgroundGlow: {
    position: "absolute",
    width: "600px",
    height: "600px",
    borderRadius: "50%",
    background:
      "radial-gradient(circle, rgba(56,189,248,0.08) 0%, rgba(9,13,22,0) 70%)",
    top: "50%",
    left: "50%",
    transform: "translate(-50%, -50%)",
    pointerEvents: "none",
    zIndex: 0,
  },
  card: {
    width: "100%",
    maxWidth: "540px",
    padding: "40px",
    borderRadius: "var(--radius-xl)",
    boxShadow: "var(--shadow-xl)",
    zIndex: 1,
    display: "flex",
    flexDirection: "column",
    gap: "24px",
  },
  header: {
    display: "flex",
    flexDirection: "column",
    alignItems: "center",
    textAlign: "center",
    gap: "12px",
  },
  logoContainer: {
    width: "48px",
    height: "48px",
    borderRadius: "var(--radius-lg)",
    background:
      "linear-gradient(135deg, var(--color-secondary), var(--color-accent))",
    display: "flex",
    alignItems: "center",
    justifyContent: "center",
    boxShadow: "0 0 12px rgba(56, 189, 248, 0.3)",
    marginBottom: "8px",
  },
  logoText: {
    color: "#090D16",
    fontWeight: "bold",
    fontSize: "24px",
  },
  title: {
    fontSize: "28px",
    fontWeight: 600,
    color: "var(--color-primary)",
    letterSpacing: "-0.5px",
  },
  subtitle: {
    fontSize: "14px",
    color: "#94a3b8",
    maxWidth: "400px",
    lineHeight: "1.5",
  },
  form: {
    display: "flex",
    flexDirection: "column",
    gap: "20px",
  },
  formGroup: {
    display: "flex",
    flexDirection: "column",
    gap: "8px",
  },
  label: {
    fontSize: "13px",
    fontWeight: 500,
    color: "#cbd5e1",
    textTransform: "uppercase",
    letterSpacing: "0.5px",
  },
  inputContainer: {
    position: "relative",
    display: "flex",
    alignItems: "center",
  },
  input: {
    width: "100%",
    padding: "14px 16px",
    paddingRight: "140px", // leave room for badges
    borderRadius: "var(--radius-md)",
    backgroundColor: "var(--color-surface-subtle)",
    border: "1px solid var(--color-border)",
    color: "var(--color-primary)",
    fontSize: "15px",
    transition: "var(--transition-fast)",
  },
  indicatorContainer: {
    position: "absolute",
    right: "12px",
    display: "flex",
    alignItems: "center",
  },
  checkingText: {
    color: "var(--color-secondary)",
    fontSize: "13px",
    display: "flex",
    gap: "2px",
  },
  healthyBadge: {
    color: "var(--color-success)",
    fontSize: "13px",
    fontWeight: 500,
    display: "flex",
    alignItems: "center",
    gap: "6px",
  },
  successDot: {
    width: "8px",
    height: "8px",
    borderRadius: "50%",
    backgroundColor: "var(--color-success)",
  },
  errorBadge: {
    color: "var(--color-error)",
    fontSize: "13px",
    fontWeight: 500,
  },
  errorText: {
    backgroundColor: "rgba(239, 68, 68, 0.08)",
    border: "1px solid rgba(239, 68, 68, 0.15)",
    borderRadius: "var(--radius-md)",
    padding: "12px 14px",
    fontSize: "13px",
    color: "#fca5a5",
    lineHeight: "1.5",
  },
  helpText: {
    fontSize: "11px",
    color: "#f87171",
    marginTop: "6px",
  },
  helpNote: {
    color: "#94a3b8",
    fontSize: "12px",
    lineHeight: "1.4",
  },
  agentGrid: {
    display: "flex",
    flexDirection: "column",
    gap: "12px",
  },
  agentCard: {
    padding: "16px",
    borderRadius: "var(--radius-md)",
    border: "1px solid var(--color-border)",
    transition: "var(--transition-fast)",
    display: "flex",
    flexDirection: "column",
    gap: "6px",
  },
  disabledAgentCard: {
    backgroundColor: "rgba(19, 27, 46, 0.3)",
    borderColor: "rgba(30, 41, 59, 0.5)",
    opacity: 0.5,
    cursor: "not-allowed",
  },
  agentHeader: {
    display: "flex",
    justifyContent: "space-between",
    alignItems: "center",
  },
  agentName: {
    color: "var(--color-primary)",
    fontSize: "15px",
  },
  recommendedBadge: {
    backgroundColor: "rgba(16, 185, 129, 0.1)",
    color: "var(--color-success)",
    padding: "2px 8px",
    borderRadius: "var(--radius-sm)",
    fontSize: "11px",
    fontWeight: 600,
  },
  comingSoonBadge: {
    backgroundColor: "rgba(100, 116, 139, 0.1)",
    color: "#94a3b8",
    padding: "2px 8px",
    borderRadius: "var(--radius-sm)",
    fontSize: "11px",
    fontWeight: 500,
  },
  agentDesc: {
    fontSize: "13px",
    color: "#94a3b8",
    lineHeight: "1.4",
  },
  submitErrorAlert: {
    backgroundColor: "rgba(239, 68, 68, 0.1)",
    border: "1px solid var(--color-error)",
    borderRadius: "var(--radius-md)",
    padding: "12px",
    color: "var(--color-error)",
    fontSize: "13px",
  },
  actionContainer: {
    display: "flex",
    justifyContent: "flex-end",
    marginTop: "8px",
  },
  button: {
    padding: "14px 28px",
    borderRadius: "var(--radius-md)",
    fontWeight: 600,
    fontSize: "15px",
    transition: "all 0.2s ease",
    border: "none",
  },
};

export default SetupPage;
