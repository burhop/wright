import { useEffect, useState } from "react";
import type { FormEvent, ReactNode } from "react";
import {
  clearStoredAccessToken,
  consumeAccessTokenFromLocation,
  createBrowserSession,
  fetchSessionStatus,
  readStoredAccessToken,
  storeAccessToken,
} from "../../services/auth-session";
import { hostAdapter } from "../../services/host-adapter";

interface AuthGateProps {
  children: ReactNode;
}

type AuthState = "checking" | "authenticated" | "needs-token";

export function AuthGate({ children }: AuthGateProps) {
  const [state, setState] = useState<AuthState>("checking");
  const [token, setToken] = useState("");
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (hostAdapter.mode !== "browser") {
      setState("authenticated");
      return;
    }

    let active = true;
    let retryTimer: number | undefined;
    const bootstrap = async () => {
      const discoveredToken =
        consumeAccessTokenFromLocation() || readStoredAccessToken();
      let status;
      try {
        status = await fetchSessionStatus();
      } catch {
        if (!active) return;
        setState("checking");
        retryTimer = window.setTimeout(() => void bootstrap(), 1000);
        return;
      }
      if (!active) return;
      if (!status.auth_required || status.authenticated) {
        setState("authenticated");
        return;
      }
      if (discoveredToken) {
        try {
          await createBrowserSession(discoveredToken);
          if (!active) return;
          setState("authenticated");
          return;
        } catch {
          clearStoredAccessToken();
        }
      }
      setState("needs-token");
    };

    void bootstrap();
    return () => {
      active = false;
      if (retryTimer !== undefined) window.clearTimeout(retryTimer);
    };
  }, []);

  const submit = async (event: FormEvent) => {
    event.preventDefault();
    const trimmed = token.trim();
    if (!trimmed) {
      setError("Enter the access token.");
      return;
    }
    setError(null);
    try {
      await createBrowserSession(trimmed);
      storeAccessToken(trimmed);
      setState("authenticated");
    } catch (err) {
      clearStoredAccessToken();
      setError(err instanceof Error ? err.message : "Invalid access token");
    }
  };

  if (state === "authenticated") {
    return <>{children}</>;
  }

  if (state === "checking") {
    return (
      <div
        role="status"
        style={{
          position: "fixed",
          inset: 0,
          display: "flex",
          alignItems: "center",
          justifyContent: "center",
          background: "var(--color-background)",
          color: "var(--color-secondary)",
          fontFamily: "var(--font-ui)",
        }}
      >
        Connecting to Wright…
      </div>
    );
  }

  return (
    <>
      {state === "needs-token" ? (
        <div
          role="dialog"
          aria-modal="true"
          aria-labelledby="wright-auth-title"
          style={{
            position: "fixed",
            inset: 0,
            zIndex: 2000,
            display: "flex",
            alignItems: "center",
            justifyContent: "center",
            background: "rgba(4, 9, 20, 0.82)",
            backdropFilter: "blur(8px)",
            padding: "24px",
          }}
        >
          <form
            onSubmit={submit}
            style={{
              width: "min(460px, 100%)",
              border: "1px solid var(--color-border)",
              borderRadius: "var(--radius-md)",
              background: "var(--color-surface)",
              boxShadow: "var(--shadow-xl)",
              padding: "var(--space-2xl)",
              display: "flex",
              flexDirection: "column",
              gap: "var(--space-lg)",
            }}
          >
            <div>
              <h2
                id="wright-auth-title"
                style={{
                  margin: 0,
                  color: "var(--color-primary)",
                  fontSize: "1.2rem",
                  fontWeight: 700,
                }}
              >
                Unlock Wright
              </h2>
              <p
                style={{
                  margin: "var(--space-sm) 0 0",
                  color: "var(--color-secondary)",
                  lineHeight: 1.5,
                }}
              >
                Enter the access token printed when this Docker container
                started.
              </p>
            </div>
            <label
              style={{
                display: "flex",
                flexDirection: "column",
                gap: "var(--space-xs)",
                color: "var(--color-primary)",
                fontWeight: 600,
              }}
            >
              Access Token
              <input
                autoFocus
                type="password"
                value={token}
                onChange={(event) => setToken(event.target.value)}
                style={{
                  width: "100%",
                  padding: "var(--space-md)",
                  background: "var(--color-surface-subtle)",
                  border: "1px solid var(--color-border)",
                  borderRadius: "var(--radius-md)",
                  color: "var(--color-primary)",
                }}
              />
            </label>
            {error ? (
              <div
                role="alert"
                style={{
                  border: "1px solid var(--color-error)",
                  borderRadius: "var(--radius-sm)",
                  color: "var(--color-error)",
                  padding: "var(--space-sm) var(--space-md)",
                }}
              >
                {error}
              </div>
            ) : null}
            <button
              type="submit"
              style={{
                alignSelf: "flex-end",
                minWidth: "140px",
                padding: "var(--space-md) var(--space-lg)",
                border: "none",
                borderRadius: "var(--radius-md)",
                background: "var(--color-accent)",
                color: "var(--color-accent-text)",
                fontWeight: 700,
                cursor: "pointer",
              }}
            >
              Unlock
            </button>
          </form>
        </div>
      ) : null}
    </>
  );
}
