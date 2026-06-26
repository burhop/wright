import { render, screen, waitFor, fireEvent } from "@testing-library/react";
import { describe, it, expect, vi, beforeEach, afterEach } from "vitest";
import SetupPage from "../src/components/pages/SetupPage";

describe("SetupPage", () => {
  beforeEach(() => {
    vi.restoreAllMocks();
  });

  afterEach(() => {
    vi.restoreAllMocks();
  });

  it("allows Hermes setup to continue without an LLM URL", async () => {
    const onConfigured = vi.fn();
    const fetchMock = vi
      .fn()
      .mockResolvedValueOnce({
        json: async () => ({
          is_configured: false,
          llm_api_url: "",
          active_agent: "hermes",
          theme: "dark",
        }),
      })
      .mockResolvedValueOnce({
        ok: true,
        json: async () => ({ success: true }),
      });
    vi.stubGlobal("fetch", fetchMock);

    render(<SetupPage onConfigured={onConfigured} />);

    const nextButton = await screen.findByRole("button", { name: /next/i });
    expect(nextButton).not.toBeDisabled();

    fireEvent.click(nextButton);

    await waitFor(() => expect(onConfigured).toHaveBeenCalledTimes(1));
    expect(fetchMock).toHaveBeenLastCalledWith(
      "/api/setup/configure",
      expect.objectContaining({
        method: "POST",
        body: JSON.stringify({
          llm_api_url: "",
          active_agent: "hermes",
        }),
      }),
    );
  });
});
