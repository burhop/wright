export const AUTH_TOKEN_STORAGE_KEY = "wright.localApiToken";

export interface SessionStatus {
  auth_required: boolean;
  authenticated: boolean;
}

export function readStoredAccessToken(): string | null {
  if (typeof window === "undefined") return null;
  try {
    return window.localStorage.getItem(AUTH_TOKEN_STORAGE_KEY);
  } catch {
    return null;
  }
}

export function storeAccessToken(token: string): void {
  if (typeof window === "undefined") return;
  window.localStorage.setItem(AUTH_TOKEN_STORAGE_KEY, token);
}

export function clearStoredAccessToken(): void {
  if (typeof window === "undefined") return;
  window.localStorage.removeItem(AUTH_TOKEN_STORAGE_KEY);
}

export function consumeAccessTokenFromLocation(): string | null {
  if (typeof window === "undefined") return null;

  const current = new URL(window.location.href);
  const hashParams = new URLSearchParams(
    window.location.hash.startsWith("#")
      ? window.location.hash.slice(1)
      : window.location.hash,
  );
  const token =
    hashParams.get("wright_token") ||
    hashParams.get("token") ||
    current.searchParams.get("wright_token") ||
    current.searchParams.get("token");

  if (!token) return null;

  current.searchParams.delete("wright_token");
  current.searchParams.delete("token");
  current.hash = "";
  window.history.replaceState(
    window.history.state,
    document.title,
    `${current.pathname}${current.search}${current.hash}`,
  );
  storeAccessToken(token);
  return token;
}

function getApiBaseUrl(): string {
  if (typeof window === "undefined") return "http://127.0.0.1:8000";
  const host = window.location.hostname;
  const port = window.location.port;
  if (port === "5173" || port === "5174") {
    return "";
  }
  return `${window.location.protocol}//${host}${port ? `:${port}` : ""}`;
}

export async function fetchSessionStatus(): Promise<SessionStatus> {
  const response = await fetch(`${getApiBaseUrl()}/api/auth/session/status`, {
    credentials: "same-origin",
  });
  if (!response.ok) {
    throw new Error(`Failed to check session: HTTP ${response.status}`);
  }
  return response.json();
}

export async function createBrowserSession(token: string): Promise<void> {
  const response = await fetch(`${getApiBaseUrl()}/api/auth/session`, {
    method: "POST",
    credentials: "same-origin",
    headers: {
      "Content-Type": "application/json",
    },
    body: JSON.stringify({ token }),
  });

  if (!response.ok) {
    if (response.status === 401) {
      throw new Error("Invalid access token");
    }
    throw new Error(`Failed to unlock Wright: HTTP ${response.status}`);
  }
}
