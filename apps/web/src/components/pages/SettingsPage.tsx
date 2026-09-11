import { useEffect, useState, type FormEvent } from "react";
import { Link } from "react-router-dom";
import {
  applyTheme,
  readUiPreferences,
  rememberTheme,
  saveUiPreferences,
  type Theme,
  type UiPreferences,
} from "../../services/ui-preferences";

const cardStyle = {
  backgroundColor: "var(--color-surface)",
  border: "1px solid var(--color-border)",
  borderRadius: "var(--radius-lg)",
  padding: "var(--space-lg)",
  display: "flex",
  flexDirection: "column",
  gap: "var(--space-md)",
} as const;

export function SettingsPage() {
  const [preferences, setPreferences] = useState<UiPreferences>({
    llm_provider: "hermes",
    theme: "dark",
  });
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [retry, setRetry] = useState(0);
  const [loaded, setLoaded] = useState(false);
  const [message, setMessage] = useState<{
    text: string;
    type: "success" | "error";
  } | null>(null);

  useEffect(() => {
    let active = true;
    setLoading(true);
    setMessage(null);
    void readUiPreferences()
      .then((value) => {
        if (!active) return;
        setPreferences(value);
        rememberTheme(value.theme);
        setLoaded(true);
      })
      .catch((error) => {
        if (active) setMessage({ text: error.message, type: "error" });
      })
      .finally(() => {
        if (active) setLoading(false);
      });
    return () => {
      active = false;
    };
  }, [retry]);

  const save = async (event: FormEvent) => {
    event.preventDefault();
    setSaving(true);
    setMessage(null);
    try {
      await saveUiPreferences(preferences);
      setMessage({ text: "Preferences saved.", type: "success" });
    } catch (error) {
      setMessage({
        text:
          error instanceof Error
            ? error.message
            : "Could not save preferences.",
        type: "error",
      });
    } finally {
      setSaving(false);
    }
  };

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
      <header>
        <h1 style={{ marginBottom: "var(--space-xs)" }}>Global Settings</h1>
        <p style={{ color: "var(--color-text-muted)" }}>
          Choose how Wright looks and access your AI connection.
        </p>
      </header>
      {message && (
        <div
          role={message.type === "error" ? "alert" : "status"}
          data-testid="settings-message-banner"
          style={{
            color:
              message.type === "error"
                ? "var(--color-error)"
                : "var(--color-success)",
          }}
        >
          {message.text}
        </div>
      )}
      {loading && <p role="status">Loading preferences…</p>}
      {!loading && !loaded && (
        <button type="button" onClick={() => setRetry((value) => value + 1)}>
          Try again
        </button>
      )}
      <form
        onSubmit={save}
        style={{
          display: "flex",
          flexDirection: "column",
          gap: "var(--space-lg)",
          maxWidth: 680,
        }}
      >
        <section style={cardStyle} aria-labelledby="appearance-title">
          <h2 id="appearance-title" style={{ fontSize: "1.1rem" }}>
            Appearance
          </h2>
          <label
            htmlFor="interface-theme"
            style={{ fontSize: "0.85rem", fontWeight: 600 }}
          >
            Interface Theme
          </label>
          <select
            id="interface-theme"
            data-testid="settings-theme"
            value={preferences.theme}
            disabled={loading || saving || !loaded}
            onChange={(event) => {
              const theme = event.target.value as Theme;
              setPreferences((value) => ({ ...value, theme }));
              applyTheme(theme);
              setMessage(null);
            }}
            style={{
              backgroundColor: "var(--color-surface-subtle)",
              border: "1px solid var(--color-border)",
              borderRadius: "var(--radius-md)",
              padding: "8px var(--space-md)",
              color: "var(--color-primary)",
              cursor: "pointer",
            }}
          >
            <option value="dark">Dark Theme</option>
            <option value="light">Light Theme</option>
          </select>
          <p style={{ fontSize: "0.8rem", color: "var(--color-text-muted)" }}>
            Changes appear immediately. Save Preferences to remember your
            choice.
          </p>
        </section>
        <div style={{ display: "flex", justifyContent: "flex-end" }}>
          <button
            data-testid="settings-save-btn"
            type="submit"
            disabled={loading || saving || !loaded}
            style={{
              padding: "10px var(--space-xl)",
              backgroundColor: "var(--color-secondary)",
              color: "var(--color-surface-subtle)",
              fontWeight: 600,
              borderRadius: "var(--radius-md)",
              opacity: loading || saving || !loaded ? 0.6 : 1,
            }}
          >
            {saving ? "Saving…" : "Save Preferences"}
          </button>
        </div>
      </form>
      <section
        style={{ ...cardStyle, maxWidth: 680 }}
        aria-labelledby="ai-connection-title"
      >
        <h2 id="ai-connection-title" style={{ fontSize: "1.1rem" }}>
          AI connection
        </h2>
        <p>Hermes manages your AI models and provider credentials.</p>
        <Link to="/setup/model" style={{ color: "var(--color-secondary)" }}>
          Open Model Setup →
        </Link>
      </section>
      <section
        style={{ ...cardStyle, maxWidth: 680 }}
        aria-labelledby="licenses-title"
      >
        <h2 id="licenses-title" style={{ fontSize: "1.1rem" }}>
          System Attributions &amp; Licenses
        </h2>
        <p style={{ color: "var(--color-text-muted)", fontSize: "0.85rem" }}>
          Third-party software license agreements:
        </p>
        <div
          style={{ display: "flex", flexWrap: "wrap", gap: "var(--space-md)" }}
        >
          <a
            href="/third-party-licenses-web.txt"
            target="_blank"
            rel="noopener noreferrer"
            className="license-link"
          >
            Frontend Web Licenses (TXT)
          </a>
          <a
            href="/third-party-licenses-api.txt"
            target="_blank"
            rel="noopener noreferrer"
            className="license-link"
          >
            Backend API Licenses (TXT)
          </a>
        </div>
      </section>
    </div>
  );
}
export default SettingsPage;
