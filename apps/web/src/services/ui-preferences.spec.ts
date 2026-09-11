import { beforeEach, describe, expect, it, vi } from "vitest";
import { waitFor } from "@testing-library/react";
import { hostAdapter } from "./host-adapter";
import {
  applyTheme,
  initializeSavedTheme,
  readUiPreferences,
  rememberTheme,
  restoreCachedTheme,
  saveUiPreferences,
} from "./ui-preferences";

vi.mock("./host-adapter", () => ({
  hostAdapter: { fetch: vi.fn(), getApiBaseUrl: () => "" },
}));

const fetchMock = vi.mocked(hostAdapter.fetch);
const response = (theme: string) =>
  new Response(JSON.stringify({ theme, llm_provider: "hermes" }));

beforeEach(() => {
  fetchMock.mockReset();
  applyTheme("dark");
});

describe("saved interface preferences", () => {
  it("loads the persisted theme and shares startup requests", async () => {
    let resolve!: (value: Response) => void;
    fetchMock.mockReturnValue(
      new Promise((done) => {
        resolve = done;
      }),
    );
    const stop = initializeSavedTheme();
    const preferences = readUiPreferences();
    expect(fetchMock).toHaveBeenCalledTimes(1);
    expect(fetchMock).toHaveBeenCalledWith("/api/settings");
    resolve(response("light"));
    await preferences;
    await waitFor(() =>
      expect(document.documentElement.dataset.theme).toBe("light"),
    );
    expect(document.documentElement.style.colorScheme).toBe("light");
    expect(localStorage.getItem("wright.ui.theme")).toBe("light");
    stop();
  });

  it("does not overwrite a newer selection with a delayed startup response", async () => {
    let resolve!: (value: Response) => void;
    fetchMock.mockReturnValue(
      new Promise((done) => {
        resolve = done;
      }),
    );
    const stop = initializeSavedTheme();
    const pending = readUiPreferences();
    applyTheme("light");
    resolve(response("dark"));
    await pending;
    expect(document.documentElement.dataset.theme).toBe("light");
    stop();
  });

  it("keeps the cached saved theme when the API is unavailable", async () => {
    localStorage.setItem("wright.ui.theme", "light");
    restoreCachedTheme();
    fetchMock.mockRejectedValue(new Error("Offline"));
    const stop = initializeSavedTheme();
    await expect(readUiPreferences()).rejects.toThrow("Offline");
    expect(document.documentElement.dataset.theme).toBe("light");
    stop();
  });

  it("saves appearance without modifying existing provider credentials", async () => {
    fetchMock.mockResolvedValue(new Response("{}"));
    await saveUiPreferences({ theme: "light", llm_provider: "hermes" });
    expect(JSON.parse(fetchMock.mock.calls[0][1]?.body as string)).toEqual({
      theme: "light",
      llm_provider: "hermes",
      api_keys: {},
    });
    expect(fetchMock.mock.calls[0][1]?.method).toBe("POST");
    expect(localStorage.getItem("wright.ui.theme")).toBe("light");
  });

  it("does not remember an unsaved preview if saving fails", async () => {
    rememberTheme("dark");
    applyTheme("light");
    fetchMock.mockResolvedValue(new Response("Unavailable", { status: 503 }));
    await expect(
      saveUiPreferences({ theme: "light", llm_provider: "hermes" }),
    ).rejects.toThrow("Your changes have not been saved");
    expect(document.documentElement.dataset.theme).toBe("light");
    expect(localStorage.getItem("wright.ui.theme")).toBe("dark");
  });
});
