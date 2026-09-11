import { hostAdapter } from "./host-adapter";

export type Theme = "dark" | "light";
export interface UiPreferences {
  theme: Theme;
  llm_provider: string;
}
const THEME_KEY = "wright.ui.theme";
let themeRevision = 0;
let pendingPreferences: Promise<UiPreferences> | null = null;
export const normalizeTheme = (value: unknown): Theme =>
  value === "light" ? "light" : "dark";

export function applyTheme(value: unknown) {
  const theme = normalizeTheme(value);
  document.documentElement.dataset.theme = theme;
  document.documentElement.style.colorScheme = theme;
  themeRevision += 1;
}
export function rememberTheme(value: unknown) {
  const theme = normalizeTheme(value);
  applyTheme(theme);
  try {
    localStorage.setItem(THEME_KEY, theme);
  } catch {
    /* Browser storage is optional. */
  }
}
export function restoreCachedTheme() {
  try {
    applyTheme(localStorage.getItem(THEME_KEY));
  } catch {
    applyTheme("dark");
  }
}
export function readUiPreferences(): Promise<UiPreferences> {
  if (pendingPreferences) return pendingPreferences;
  pendingPreferences = hostAdapter
    .fetch(hostAdapter.getApiBaseUrl() + "/api/settings")
    .then(async (response) => {
      if (!response.ok)
        throw new Error("Could not load preferences. Please try again.");
      const data = await response.json();
      return {
        theme: normalizeTheme(data.theme),
        llm_provider: data.llm_provider || "hermes",
      };
    })
    .finally(() => {
      pendingPreferences = null;
    });
  return pendingPreferences;
}
export async function saveUiPreferences(preferences: UiPreferences) {
  const response = await hostAdapter.fetch(
    hostAdapter.getApiBaseUrl() + "/api/settings",
    {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      // Keep the legacy request contract without reading, changing, or deleting credentials.
      body: JSON.stringify({ ...preferences, api_keys: {} }),
    },
  );
  if (!response.ok)
    throw new Error(
      "Could not save preferences. Your changes have not been saved.",
    );
  rememberTheme(preferences.theme);
}
export function initializeSavedTheme() {
  let active = true;
  const revision = themeRevision;
  void readUiPreferences()
    .then((preferences) => {
      // A slow startup response must not replace a more recent user/desktop choice.
      if (active && revision === themeRevision)
        rememberTheme(preferences.theme);
    })
    .catch(() => {
      /* Retain the last saved local theme while the API is unavailable. */
    });
  return () => {
    active = false;
  };
}
