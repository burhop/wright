import { useCallback, useEffect, useMemo, useState } from "react";
import type { FormEvent } from "react";
import { hostAdapter } from "../../services/host-adapter";

interface SetupStatus {
  is_configured: boolean;
  llm_api_url?: string | null;
  llm_provider?: string | null;
  llm_model?: string | null;
  llm_configured?: boolean;
  llm_auth_configured?: boolean;
}

interface ProviderPreset {
  id: string;
  label: string;
  auth_type: string;
  notes: string;
}

interface CodexLogin {
  session_id: string;
  status: string;
  verification_url?: string | null;
  user_code?: string | null;
  message: string;
  error?: string | null;
}

const apiUrl = (path: string) => `${hostAdapter.getApiBaseUrl()}${path}`;

const fieldStyle = {
  backgroundColor: "var(--color-surface-subtle)",
  border: "1px solid var(--color-border)",
  borderRadius: "var(--radius-md)",
  color: "var(--color-primary)",
  fontFamily: "var(--font-ui)",
  fontSize: "0.9rem",
  padding: "10px 12px",
  width: "100%",
};

const labelStyle = {
  color: "var(--color-primary)",
  fontSize: "0.82rem",
  fontWeight: 650,
};

const panelStyle = {
  backgroundColor: "var(--color-surface)",
  border: "1px solid var(--color-border)",
  borderRadius: "var(--radius-lg)",
  padding: "var(--space-lg)",
};

export function ModelSetupPage() {
  const [status, setStatus] = useState<SetupStatus | null>(null);
  const [providers, setProviders] = useState<ProviderPreset[]>([]);
  const [codexLogin, setCodexLogin] = useState<CodexLogin | null>(null);
  const [baseUrl, setBaseUrl] = useState("");
  const [model, setModel] = useState("");
  const [apiKey, setApiKey] = useState("");
  const [message, setMessage] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [isSaving, setIsSaving] = useState(false);

  const codexProvider = useMemo(
    () => providers.find((provider) => provider.id === "openai-codex"),
    [providers],
  );
  const codexSessionId = codexLogin?.session_id;
  const codexStatus = codexLogin?.status;

  const refreshStatus = useCallback(async () => {
    const response = await hostAdapter.fetch(apiUrl("/api/setup/status"));
    if (response.ok) {
      setStatus(await response.json());
    }
  }, []);

  useEffect(() => {
    refreshStatus().catch(() => undefined);
    hostAdapter
      .fetch(apiUrl("/api/setup/llm/providers"))
      .then((response) => (response.ok ? response.json() : { providers: [] }))
      .then((payload) => setProviders(payload.providers || []))
      .catch(() => setProviders([]));
  }, [refreshStatus]);

  useEffect(() => {
    if (
      !codexSessionId ||
      ["succeeded", "failed"].includes(codexStatus ?? "")
    ) {
      return;
    }
    const timer = window.setInterval(() => {
      hostAdapter
        .fetch(apiUrl(`/api/setup/llm/codex/status/${codexSessionId}`))
        .then((response) => (response.ok ? response.json() : null))
        .then((payload: CodexLogin | null) => {
          if (!payload) return;
          setCodexLogin(payload);
          if (payload.status === "succeeded") {
            setMessage("Codex is connected.");
            refreshStatus().catch(() => undefined);
          }
          if (payload.status === "failed") {
            setError(payload.error || payload.message);
          }
        })
        .catch(() => undefined);
    }, 1500);
    return () => window.clearInterval(timer);
  }, [codexSessionId, codexStatus, refreshStatus]);

  const startCodexLogin = async () => {
    setError(null);
    setMessage(null);
    const response = await hostAdapter.fetch(
      apiUrl("/api/setup/llm/codex/start"),
      {
        method: "POST",
      },
    );
    if (!response.ok) {
      setError("Codex login could not be started.");
      return;
    }
    setCodexLogin(await response.json());
  };

  const saveOpenAiCompatible = async (event: FormEvent) => {
    event.preventDefault();
    setIsSaving(true);
    setError(null);
    setMessage(null);
    try {
      const response = await hostAdapter.fetch(
        apiUrl("/api/setup/llm/configure"),
        {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({
            provider: "openai-compatible",
            base_url: baseUrl,
            model,
            api_key: apiKey,
          }),
        },
      );
      const payload = await response.json();
      if (!response.ok) {
        throw new Error(payload.message || "Provider could not be saved.");
      }
      setApiKey("");
      setMessage(payload.message || "Provider saved.");
      await refreshStatus();
    } catch (err) {
      setError(
        err instanceof Error ? err.message : "Provider could not be saved.",
      );
    } finally {
      setIsSaving(false);
    }
  };

  return (
    <div
      data-testid="page-model-setup"
      className="animate-fade-in-up"
      style={{
        display: "flex",
        flexDirection: "column",
        gap: "var(--space-lg)",
        maxWidth: "980px",
        padding: "var(--space-md) var(--space-lg)",
      }}
    >
      <div>
        <h1
          style={{
            fontFamily: "var(--font-ui)",
            fontSize: "1.6rem",
            fontWeight: 700,
            marginBottom: "var(--space-xs)",
          }}
        >
          Model Setup
        </h1>
        <p style={{ color: "var(--color-secondary)", fontSize: "0.9rem" }}>
          Current provider: {status?.llm_provider || "not connected"}
          {status?.llm_model ? ` / ${status.llm_model}` : ""}
        </p>
      </div>

      {(message || error) && (
        <div
          data-testid="model-setup-message"
          style={{
            ...panelStyle,
            borderColor: error ? "var(--color-error)" : "var(--color-success)",
            color: error ? "var(--color-error)" : "var(--color-success)",
            padding: "var(--space-md)",
          }}
        >
          {error || message}
        </div>
      )}

      <section
        data-testid="codex-provider-panel"
        style={{
          ...panelStyle,
          display: "flex",
          flexDirection: "column",
          gap: "var(--space-md)",
        }}
      >
        <div>
          <h2 style={{ fontSize: "1.05rem", fontWeight: 700 }}>
            {codexProvider?.label || "Codex / ChatGPT Login"}
          </h2>
          <p style={{ color: "var(--color-secondary)", fontSize: "0.85rem" }}>
            {codexProvider?.notes || "Uses Hermes openai-codex provider."}
          </p>
        </div>
        <button
          data-testid="start-codex-login"
          type="button"
          onClick={startCodexLogin}
          style={{
            alignSelf: "flex-start",
            backgroundColor: "var(--color-secondary)",
            border: "none",
            borderRadius: "var(--radius-md)",
            color: "var(--color-surface-subtle)",
            cursor: "pointer",
            fontWeight: 700,
            padding: "10px 16px",
          }}
        >
          Start Login
        </button>

        {codexLogin && (
          <div
            data-testid="codex-login-status"
            style={{
              backgroundColor: "var(--color-surface-subtle)",
              border: "1px solid var(--color-border)",
              borderRadius: "var(--radius-md)",
              display: "grid",
              gap: "var(--space-sm)",
              padding: "var(--space-md)",
            }}
          >
            <div>Status: {codexLogin.status}</div>
            {codexLogin.verification_url && (
              <a
                href={codexLogin.verification_url}
                target="_blank"
                rel="noreferrer"
                style={{ color: "var(--color-secondary)" }}
              >
                {codexLogin.verification_url}
              </a>
            )}
            {codexLogin.user_code && (
              <div
                data-testid="codex-user-code"
                style={{
                  fontFamily: "var(--font-mono)",
                  fontSize: "1.2rem",
                  letterSpacing: "0",
                }}
              >
                {codexLogin.user_code}
              </div>
            )}
            <div style={{ color: "var(--color-secondary)" }}>
              {codexLogin.message}
            </div>
          </div>
        )}
      </section>

      <form
        data-testid="openai-compatible-form"
        onSubmit={saveOpenAiCompatible}
        style={{
          ...panelStyle,
          display: "grid",
          gap: "var(--space-md)",
        }}
      >
        <div>
          <h2 style={{ fontSize: "1.05rem", fontWeight: 700 }}>
            OpenAI-Compatible Endpoint
          </h2>
        </div>
        <label style={{ display: "grid", gap: "var(--space-xs)" }}>
          <span style={labelStyle}>Base URL</span>
          <input
            data-testid="llm-base-url"
            value={baseUrl}
            onChange={(event) => setBaseUrl(event.target.value)}
            placeholder="http://host.docker.internal:11434/v1"
            style={fieldStyle}
          />
        </label>
        <label style={{ display: "grid", gap: "var(--space-xs)" }}>
          <span style={labelStyle}>Model</span>
          <input
            data-testid="llm-model"
            value={model}
            onChange={(event) => setModel(event.target.value)}
            placeholder="model-id"
            style={fieldStyle}
          />
        </label>
        <label style={{ display: "grid", gap: "var(--space-xs)" }}>
          <span style={labelStyle}>API Key</span>
          <input
            data-testid="llm-api-key"
            type="password"
            value={apiKey}
            onChange={(event) => setApiKey(event.target.value)}
            placeholder="NotNeeded"
            style={fieldStyle}
          />
        </label>
        <button
          data-testid="save-openai-compatible"
          type="submit"
          disabled={isSaving}
          style={{
            justifySelf: "start",
            backgroundColor: "var(--color-secondary)",
            border: "none",
            borderRadius: "var(--radius-md)",
            color: "var(--color-surface-subtle)",
            cursor: "pointer",
            fontWeight: 700,
            opacity: isSaving ? 0.7 : 1,
            padding: "10px 16px",
          }}
        >
          {isSaving ? "Saving" : "Save Provider"}
        </button>
      </form>
    </div>
  );
}

export default ModelSetupPage;
