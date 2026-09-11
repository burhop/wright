import { beforeEach, describe, expect, it, vi } from "vitest";
import {
  cleanup,
  fireEvent,
  render,
  screen,
  waitFor,
} from "@testing-library/react";
import { MemoryRouter } from "react-router-dom";
import { hostAdapter } from "../../services/host-adapter";
import { SettingsPage } from "./SettingsPage";

vi.mock("../../services/host-adapter", () => ({
  hostAdapter: { fetch: vi.fn(), getApiBaseUrl: () => "" },
}));
const fetchMock = vi.mocked(hostAdapter.fetch);
const saved = () =>
  new Response(JSON.stringify({ theme: "dark", llm_provider: "hermes" }));
const renderSettings = () =>
  render(
    <MemoryRouter>
      <SettingsPage />
    </MemoryRouter>,
  );

beforeEach(() => {
  cleanup();
  fetchMock.mockReset();
  document.documentElement.dataset.theme = "dark";
});

describe("Settings", () => {
  it("previews the theme immediately and leaves credentials to Hermes", async () => {
    fetchMock
      .mockResolvedValueOnce(saved())
      .mockResolvedValueOnce(new Response("{}"));
    renderSettings();
    const theme = screen.getByLabelText("Interface Theme");
    await waitFor(() => expect(theme).toBeEnabled());
    expect(screen.queryByText("API Keys & Secrets")).not.toBeInTheDocument();
    expect(
      screen.queryByTestId("settings-llm-provider"),
    ).not.toBeInTheDocument();
    expect(
      screen.getByRole("link", { name: /Open Model Setup/ }),
    ).toHaveAttribute("href", "/setup/model");
    fireEvent.change(theme, { target: { value: "light" } });
    expect(document.documentElement.dataset.theme).toBe("light");
    expect(fetchMock).toHaveBeenCalledTimes(1);
    fireEvent.click(screen.getByRole("button", { name: "Save Preferences" }));
    expect(await screen.findByText("Preferences saved.")).toBeInTheDocument();
    expect(JSON.parse(fetchMock.mock.calls[1][1]?.body as string)).toEqual({
      theme: "light",
      llm_provider: "hermes",
      api_keys: {},
    });
    fireEvent.change(theme, { target: { value: "dark" } });
    expect(document.documentElement.dataset.theme).toBe("dark");
  });

  it("keeps save disabled when preferences fail to load and allows retry", async () => {
    fetchMock
      .mockResolvedValueOnce(new Response("Unavailable", { status: 503 }))
      .mockResolvedValueOnce(saved());
    renderSettings();
    expect(await screen.findByRole("alert")).toHaveTextContent(
      "Could not load preferences",
    );
    expect(
      screen.getByRole("button", { name: "Save Preferences" }),
    ).toBeDisabled();
    fireEvent.click(screen.getByRole("button", { name: "Try again" }));
    await waitFor(() =>
      expect(screen.getByLabelText("Interface Theme")).toBeEnabled(),
    );
    expect(screen.queryByRole("alert")).not.toBeInTheDocument();
  });

  it("shows a save failure without claiming that the preview was saved", async () => {
    fetchMock
      .mockResolvedValueOnce(saved())
      .mockResolvedValueOnce(new Response("Unavailable", { status: 503 }));
    renderSettings();
    await waitFor(() =>
      expect(screen.getByLabelText("Interface Theme")).toBeEnabled(),
    );
    fireEvent.change(screen.getByLabelText("Interface Theme"), {
      target: { value: "light" },
    });
    fireEvent.click(screen.getByRole("button", { name: "Save Preferences" }));
    expect(await screen.findByRole("alert")).toHaveTextContent(
      "Your changes have not been saved",
    );
    expect(localStorage.getItem("wright.ui.theme")).toBe("dark");
    expect(screen.queryByText("Preferences saved.")).not.toBeInTheDocument();
  });
});
