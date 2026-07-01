import React, { useEffect, useState } from "react";

interface GlobalSettings {
  llm_provider: string;
  theme: string;
  api_keys: Record<string, string>;
}

export function SettingsPage() {
  const [settings, setSettings] = useState<GlobalSettings>({
    llm_provider: "hermes",
    theme: "dark",
    api_keys: {
      OPENAI_API_KEY: "",
      ANTHROPIC_API_KEY: "",
      GEMINI_API_KEY: "",
    },
  });

  const [isLoading, setIsLoading] = useState(false);
  const [isSaving, setIsSaving] = useState(false);
  const [message, setMessage] = useState<{
    text: string;
    type: "success" | "error";
  } | null>(null);

  // Helper to construct API URL
  const getApiUrl = (path: string) => {
    const host = window.location.hostname;
    const port = window.location.port;
    const base =
      port === "5173" || port === "5174" ? `http://${host}:8000` : "";
    return `${base}${path}`;
  };

  // Fetch settings on mount
  useEffect(() => {
    const fetchSettings = async () => {
      setIsLoading(true);
      try {
        const res = await fetch(getApiUrl("/api/settings"));
        if (!res.ok) throw new Error("Failed to load settings from backend");
        const data = await res.json();

        // Ensure standard keys exist in api_keys object
        const apiKeys = {
          OPENAI_API_KEY: "",
          ANTHROPIC_API_KEY: "",
          GEMINI_API_KEY: "",
          ...(data.api_keys || {}),
        };

        setSettings({
          llm_provider: data.llm_provider || "hermes",
          theme: data.theme || "dark",
          api_keys: apiKeys,
        });

        // Set document attribute
        document.documentElement.setAttribute(
          "data-theme",
          data.theme || "dark",
        );
      } catch (err: any) {
        setMessage({
          text: err.message || "Failed to fetch settings from API",
          type: "error",
        });
      } finally {
        setIsLoading(false);
      }
    };

    fetchSettings();
  }, []);

  const handleSave = async (e: React.FormEvent) => {
    e.preventDefault();
    setIsSaving(true);
    setMessage(null);

    try {
      const res = await fetch(getApiUrl("/api/settings"), {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify(settings),
      });

      if (!res.ok) throw new Error("Failed to save settings to backend");

      setMessage({
        text: "Global settings successfully updated!",
        type: "success",
      });

      // Apply theme immediately
      document.documentElement.setAttribute("data-theme", settings.theme);

      // Hide success message after 3 seconds
      setTimeout(() => {
        setMessage(null);
      }, 3000);
    } catch (err: any) {
      setMessage({
        text: err.message || "Failed to save settings",
        type: "error",
      });
    } finally {
      setIsSaving(false);
    }
  };

  const updateApiKey = (key: string, value: string) => {
    setSettings((prev) => ({
      ...prev,
      api_keys: {
        ...prev.api_keys,
        [key]: value,
      },
    }));
  };

  if (isLoading) {
    return (
      <div
        style={{
          display: "flex",
          alignItems: "center",
          justifyContent: "center",
          height: "100%",
          color: "var(--color-secondary)",
          fontFamily: "var(--font-ui)",
        }}
      >
        <div style={{ display: "flex", gap: "4px" }}>
          <span className="thinking-dot" />
          <span className="thinking-dot" />
          <span className="thinking-dot" />
        </div>
        <span style={{ marginLeft: "var(--space-sm)" }}>
          Loading preferences...
        </span>
      </div>
    );
  }

  return (
    <div
      data-testid="page-settings"
      className="animate-fade-in-up"
      style={{
        display: "flex",
        flexDirection: "column",
        height: "100%",
        width: "100%",
        gap: "var(--space-lg)",
        padding: "var(--space-md) var(--space-xl)",
        overflowY: "auto",
        textAlign: "left",
      }}
    >
      {/* Page Header */}
      <div>
        <h1
          style={{
            fontFamily: "var(--font-ui)",
            fontWeight: 700,
            marginBottom: "var(--space-xs)",
          }}
        >
          Global Settings
        </h1>
        <p style={{ color: "var(--color-secondary)", fontSize: "0.9rem" }}>
          Configure default AI models, interface preferences, and API
          credentials.
        </p>
      </div>

      {/* Message Banner */}
      {message && (
        <div
          data-testid="settings-message-banner"
          style={{
            padding: "var(--space-md)",
            borderRadius: "var(--radius-md)",
            border: `1px solid ${message.type === "success" ? "var(--color-success)" : "var(--color-error)"}`,
            backgroundColor:
              message.type === "success"
                ? "rgba(34, 197, 94, 0.05)"
                : "rgba(239, 68, 68, 0.05)",
            color:
              message.type === "success"
                ? "var(--color-success)"
                : "var(--color-error)",
            fontSize: "0.9rem",
            display: "flex",
            alignItems: "center",
            gap: "var(--space-sm)",
          }}
        >
          {message.type === "success" ? "" : ""} {message.text}
        </div>
      )}

      {/* Main Settings Form */}
      <form
        onSubmit={handleSave}
        style={{
          display: "flex",
          flexDirection: "column",
          gap: "var(--space-xl)",
          maxWidth: "680px",
        }}
      >
        {/* Card 1: Core Configuration */}
        <div
          style={{
            backgroundColor: "var(--color-surface)",
            border: "1px solid var(--color-border)",
            borderRadius: "var(--radius-lg)",
            padding: "var(--space-lg)",
            display: "flex",
            flexDirection: "column",
            gap: "var(--space-md)",
          }}
        >
          <h3
            style={{
              fontSize: "1.1rem",
              fontWeight: 600,
              borderBottom: "1px solid var(--color-border)",
              paddingBottom: "var(--space-sm)",
              marginBottom: "var(--space-xs)",
            }}
          >
            Model & UI Preferences
          </h3>

          {/* LLM Provider */}
          <div
            style={{
              display: "flex",
              flexDirection: "column",
              gap: "var(--space-xs)",
            }}
          >
            <label
              style={{
                fontSize: "0.85rem",
                fontWeight: 600,
                color: "var(--color-primary)",
              }}
            >
              Active AI Provider
            </label>
            <select
              data-testid="settings-llm-provider"
              value={settings.llm_provider}
              onChange={(e) =>
                setSettings({ ...settings, llm_provider: e.target.value })
              }
              style={{
                backgroundColor: "var(--color-surface-subtle)",
                border: "1px solid var(--color-border)",
                borderRadius: "var(--radius-md)",
                padding: "8px var(--space-md)",
                fontSize: "0.9rem",
                color: "var(--color-primary)",
                cursor: "pointer",
                transition: "border-color var(--transition-fast)",
              }}
            >
              <option value="hermes">Hermes (Local Custom Model)</option>
              <option value="openai">OpenAI GPT-4o</option>
              <option value="anthropic">Anthropic Claude 3.5 Sonnet</option>
              <option value="gemini">Gemini 1.5 Pro</option>
            </select>
            <span
              style={{ fontSize: "0.75rem", color: "var(--color-secondary)" }}
            >
              Determines the backing language model used by the autonomous
              workspace agents.
            </span>
          </div>

          {/* Interface Theme */}
          <div
            style={{
              display: "flex",
              flexDirection: "column",
              gap: "var(--space-xs)",
              marginTop: "var(--space-sm)",
            }}
          >
            <label
              style={{
                fontSize: "0.85rem",
                fontWeight: 600,
                color: "var(--color-primary)",
              }}
            >
              Interface Theme
            </label>
            <select
              data-testid="settings-theme"
              value={settings.theme}
              onChange={(e) =>
                setSettings({ ...settings, theme: e.target.value })
              }
              style={{
                backgroundColor: "var(--color-surface-subtle)",
                border: "1px solid var(--color-border)",
                borderRadius: "var(--radius-md)",
                padding: "8px var(--space-md)",
                fontSize: "0.9rem",
                color: "var(--color-primary)",
                cursor: "pointer",
                transition: "border-color var(--transition-fast)",
              }}
            >
              <option value="dark">Dark Theme</option>
              <option value="light">Light Theme</option>
            </select>
            <span
              style={{ fontSize: "0.75rem", color: "var(--color-secondary)" }}
            >
              Toggle between the classic high-contrast workspace dark mode and
              clean light mode.
            </span>
          </div>
        </div>

        {/* Card 2: API Keys */}
        <div
          style={{
            backgroundColor: "var(--color-surface)",
            border: "1px solid var(--color-border)",
            borderRadius: "var(--radius-lg)",
            padding: "var(--space-lg)",
            display: "flex",
            flexDirection: "column",
            gap: "var(--space-md)",
          }}
        >
          <h3
            style={{
              fontSize: "1.1rem",
              fontWeight: 600,
              borderBottom: "1px solid var(--color-border)",
              paddingBottom: "var(--space-sm)",
              marginBottom: "var(--space-xs)",
            }}
          >
            API Keys & Secrets
          </h3>
          <p
            style={{
              color: "var(--color-secondary)",
              fontSize: "0.8rem",
              marginTop: "-var(--space-xs)",
              marginBottom: "var(--space-xs)",
            }}
          >
            Keys are saved securely in your local sqlite database and never
            transmitted anywhere else.
          </p>

          {/* OpenAI Key */}
          <div
            style={{
              display: "flex",
              flexDirection: "column",
              gap: "var(--space-xs)",
            }}
          >
            <label
              style={{
                fontSize: "0.85rem",
                fontWeight: 600,
                color: "var(--color-primary)",
              }}
            >
              OpenAI API Key
            </label>
            <input
              data-testid="settings-api-key-openai"
              type="password"
              placeholder="sk-..."
              value={settings.api_keys.OPENAI_API_KEY || ""}
              onChange={(e) => updateApiKey("OPENAI_API_KEY", e.target.value)}
              style={{
                backgroundColor: "var(--color-surface-subtle)",
                border: "1px solid var(--color-border)",
                borderRadius: "var(--radius-md)",
                padding: "8px var(--space-md)",
                fontSize: "0.9rem",
                fontFamily: "var(--font-mono)",
                color: "var(--color-primary)",
                transition: "border-color var(--transition-fast)",
              }}
            />
          </div>

          {/* Anthropic Key */}
          <div
            style={{
              display: "flex",
              flexDirection: "column",
              gap: "var(--space-xs)",
              marginTop: "var(--space-sm)",
            }}
          >
            <label
              style={{
                fontSize: "0.85rem",
                fontWeight: 600,
                color: "var(--color-primary)",
              }}
            >
              Anthropic API Key
            </label>
            <input
              data-testid="settings-api-key-anthropic"
              type="password"
              placeholder="sk-ant-..."
              value={settings.api_keys.ANTHROPIC_API_KEY || ""}
              onChange={(e) =>
                updateApiKey("ANTHROPIC_API_KEY", e.target.value)
              }
              style={{
                backgroundColor: "var(--color-surface-subtle)",
                border: "1px solid var(--color-border)",
                borderRadius: "var(--radius-md)",
                padding: "8px var(--space-md)",
                fontSize: "0.9rem",
                fontFamily: "var(--font-mono)",
                color: "var(--color-primary)",
                transition: "border-color var(--transition-fast)",
              }}
            />
          </div>

          {/* Gemini Key */}
          <div
            style={{
              display: "flex",
              flexDirection: "column",
              gap: "var(--space-xs)",
              marginTop: "var(--space-sm)",
            }}
          >
            <label
              style={{
                fontSize: "0.85rem",
                fontWeight: 600,
                color: "var(--color-primary)",
              }}
            >
              Gemini API Key
            </label>
            <input
              data-testid="settings-api-key-gemini"
              type="password"
              placeholder="AIzaSy..."
              value={settings.api_keys.GEMINI_API_KEY || ""}
              onChange={(e) => updateApiKey("GEMINI_API_KEY", e.target.value)}
              style={{
                backgroundColor: "var(--color-surface-subtle)",
                border: "1px solid var(--color-border)",
                borderRadius: "var(--radius-md)",
                padding: "8px var(--space-md)",
                fontSize: "0.9rem",
                fontFamily: "var(--font-mono)",
                color: "var(--color-primary)",
                transition: "border-color var(--transition-fast)",
              }}
            />
          </div>
        </div>

        {/* Submit Actions */}
        <div
          style={{
            display: "flex",
            justifyContent: "flex-end",
            gap: "var(--space-md)",
          }}
        >
          <button
            data-testid="settings-save-btn"
            type="submit"
            disabled={isSaving}
            style={{
              padding: "10px var(--space-xl)",
              backgroundColor: "var(--color-secondary)",
              color: "var(--color-surface-subtle)",
              fontWeight: 600,
              fontSize: "0.95rem",
              borderRadius: "var(--radius-md)",
              opacity: isSaving ? 0.7 : 1,
              transition:
                "transform var(--transition-fast), opacity var(--transition-fast)",
              boxShadow: "var(--shadow-glow)",
            }}
            onMouseEnter={(e) => {
              if (!isSaving) e.currentTarget.style.transform = "scale(1.02)";
            }}
            onMouseLeave={(e) => {
              e.currentTarget.style.transform = "none";
            }}
          >
            {isSaving ? "Saving Config..." : "Save Preferences"}
          </button>
        </div>
      </form>

      {/* Card 3: System Attributions & Licenses */}
      <div
        style={{
          backgroundColor: "var(--color-surface)",
          border: "1px solid var(--color-border)",
          borderRadius: "var(--radius-lg)",
          padding: "var(--space-lg)",
          display: "flex",
          flexDirection: "column",
          gap: "var(--space-md)",
          maxWidth: "680px",
        }}
      >
        <h3
          style={{
            fontSize: "1.1rem",
            fontWeight: 600,
            borderBottom: "1px solid var(--color-border)",
            paddingBottom: "var(--space-sm)",
            marginBottom: "var(--space-xs)",
          }}
        >
          System Attributions & Licenses
        </h3>
        <p
          style={{
            color: "var(--color-secondary)",
            fontSize: "0.85rem",
            margin: 0,
          }}
        >
          This product is built using open-source software. You can view the
          third-party license agreements below:
        </p>
        <div
          style={{
            display: "flex",
            gap: "var(--space-md)",
            alignItems: "center",
          }}
        >
          <a
            href="/third-party-licenses-web.txt"
            target="_blank"
            rel="noopener noreferrer"
            className="license-link"
          >
            Frontend Web Licenses (TXT)
          </a>
          <span style={{ color: "var(--color-border)", fontSize: "0.85rem" }}>
            |
          </span>
          <a
            href="/third-party-licenses-api.txt"
            target="_blank"
            rel="noopener noreferrer"
            className="license-link"
          >
            Backend API Licenses (TXT)
          </a>
        </div>
      </div>
    </div>
  );
}

export default SettingsPage;
