import { fireEvent, render, screen, waitFor } from "@testing-library/react";
import { beforeEach, describe, expect, it, vi } from "vitest";
import ModelSetupPage from "../src/components/pages/ModelSetupPage";
import { hostAdapter } from "../src/services/host-adapter";

const jsonResponse = (payload: unknown, ok = true) =>
  Promise.resolve({
    ok,
    json: () => Promise.resolve(payload),
  } as Response);

describe("ModelSetupPage", () => {
  beforeEach(() => {
    vi.restoreAllMocks();
    vi.spyOn(hostAdapter, "getApiBaseUrl").mockReturnValue("");
  });

  it("starts Hermes Codex login and shows the device code", async () => {
    const fetchMock = vi
      .spyOn(hostAdapter, "fetch")
      .mockImplementation((input: RequestInfo | URL, init?: RequestInit) => {
        const url = String(input);
        if (url.endsWith("/api/setup/status")) {
          return jsonResponse({
            llm_provider: null,
            llm_model: null,
            llm_configured: false,
          });
        }
        if (url.endsWith("/api/setup/llm/providers")) {
          return jsonResponse({
            providers: [
              {
                id: "openai-codex",
                label: "Codex / ChatGPT Login",
                auth_type: "oauth_device_or_seed_file",
                notes: "Uses Hermes openai-codex provider.",
              },
            ],
          });
        }
        if (url.endsWith("/api/setup/llm/codex/start")) {
          expect(init?.method).toBe("POST");
          return jsonResponse({
            session_id: "job-1",
            status: "awaiting_user",
            verification_url: "https://auth.openai.com/codex/device",
            user_code: "ABCD-EFGH",
            message: "Open the verification URL and enter the code.",
          });
        }
        return jsonResponse({});
      });

    render(<ModelSetupPage />);

    fireEvent.click(await screen.findByTestId("start-codex-login"));

    expect(await screen.findByTestId("codex-user-code")).toHaveTextContent(
      "ABCD-EFGH",
    );
    expect(screen.getByTestId("codex-login-status")).toHaveTextContent(
      "awaiting_user",
    );
    expect(fetchMock).toHaveBeenCalledWith(
      "/api/setup/llm/codex/start",
      expect.objectContaining({ method: "POST" }),
    );
  });

  it("saves an OpenAI-compatible provider", async () => {
    vi.spyOn(hostAdapter, "fetch").mockImplementation(
      (input: RequestInfo | URL, init?: RequestInit) => {
        const url = String(input);
        if (url.endsWith("/api/setup/status")) {
          return jsonResponse({ llm_provider: null });
        }
        if (url.endsWith("/api/setup/llm/providers")) {
          return jsonResponse({ providers: [] });
        }
        if (url.endsWith("/api/setup/llm/configure")) {
          expect(init?.method).toBe("POST");
          expect(JSON.parse(String(init?.body))).toMatchObject({
            provider: "openai-compatible",
            base_url: "http://host.docker.internal:11434/v1",
            model: "cad-model",
          });
          return jsonResponse({
            success: true,
            configured: true,
            auth_configured: true,
            provider: "custom",
            base_url: "http://host.docker.internal:11434/v1",
            model: "cad-model",
            message: "Hermes LLM provider configured successfully.",
          });
        }
        return jsonResponse({});
      },
    );

    render(<ModelSetupPage />);

    fireEvent.change(await screen.findByTestId("llm-base-url"), {
      target: { value: "http://host.docker.internal:11434/v1" },
    });
    fireEvent.change(screen.getByTestId("llm-model"), {
      target: { value: "cad-model" },
    });
    fireEvent.change(screen.getByTestId("llm-api-key"), {
      target: { value: "NotNeeded" },
    });
    fireEvent.submit(screen.getByTestId("openai-compatible-form"));

    await waitFor(() => {
      expect(screen.getByTestId("model-setup-message")).toHaveTextContent(
        "Hermes LLM provider configured successfully.",
      );
    });
  });
});
