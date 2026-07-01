import { render, screen } from "@testing-library/react";
import { describe, it, expect, vi } from "vitest";
import StatusBar from "../src/components/layout/StatusBar";
import type { ServiceStatus, TraceContext } from "../src/store/types";

describe("StatusBar", () => {
  it("renders statuses and latest trace info correctly", () => {
    const mockStatuses: ServiceStatus[] = [
      {
        serviceId: "wright-api",
        name: "Wright API",
        endpoint: "/api/health",
        state: "connected",
        lastChecked: Date.now(),
      },
      {
        serviceId: "hermes-agent",
        name: "Hermes Agent",
        endpoint: "/api/agent/health",
        state: "connected",
        lastChecked: Date.now(),
      },
      {
        serviceId: "llm-backend",
        name: "LLM Backend",
        endpoint: "/api/inference/health",
        state: "disconnected",
        lastChecked: Date.now(),
        error: "LLM backend is not ready",
      },
    ];

    const mockTrace: TraceContext = {
      traceId: "tr-abc123xyz4567890",
      spanId: "span-1",
      actionName: "test-action",
      startTime: Date.now(),
      duration: null,
      status: "in-progress",
    };

    render(<StatusBar statuses={mockStatuses} latestTrace={mockTrace} />);

    expect(screen.getByTestId("status-bar")).toBeInTheDocument();

    expect(screen.getByTestId("status-wright-api")).toBeInTheDocument();
    expect(screen.getByTestId("status-hermes-agent")).toBeInTheDocument();
    expect(screen.getByTestId("status-llm-backend")).toBeInTheDocument();
    expect(screen.queryByTestId("status-inference")).not.toBeInTheDocument();
    expect(screen.queryByText("LLM Inference")).not.toBeInTheDocument();

    expect(screen.queryByTestId("health-error-hermes")).not.toBeInTheDocument();
    expect(screen.getByTestId("health-error-llm-backend")).toBeInTheDocument();
    expect(screen.getByTestId("status-llm-backend")).toHaveAttribute(
      "title",
      "LLM Backend: LLM backend is not ready",
    );
    expect(screen.getByTestId("latest-trace")).toHaveTextContent(
      /TRACE: tr-abc12/,
    );
  });

  it("mocks fetch and tests connected/disconnected status polling updates", async () => {
    const mockFetch = vi.fn().mockImplementation((url: string) => {
      if (url.includes("/api/agent/health")) {
        return Promise.resolve({
          ok: true,
          json: () =>
            Promise.resolve({
              state: "connected",
              latencyMs: 4,
              baseUrl: "http://127.0.0.1:8642",
            }),
        });
      }
      if (url.includes("/api/inference/health")) {
        return Promise.resolve({
          ok: true,
          json: () =>
            Promise.resolve({
              state: "disconnected",
              latencyMs: 4,
              baseUrl: "http://127.0.0.1:8642",
              error: "LLM backend is not ready",
            }),
        });
      }
      return Promise.resolve({
        ok: true,
        json: () => Promise.resolve({ state: "connected", latencyMs: 2 }),
      });
    });
    vi.stubGlobal("fetch", mockFetch);

    // Import healthService inside the test to ensure fresh mock environment
    const healthService = (await import("../src/services/health-service"))
      .default;

    // Run status check once using polling
    healthService.startPolling(50);

    await new Promise((resolve) => setTimeout(resolve, 100));

    const statuses = healthService.getStatuses();
    const wrightStatus = statuses.find((s) => s.serviceId === "wright-api");
    const hermesStatus = statuses.find((s) => s.serviceId === "hermes-agent");
    const llmStatus = statuses.find((s) => s.serviceId === "llm-backend");

    expect(wrightStatus?.state).toBe("connected");
    expect(hermesStatus?.state).toBe("connected");
    expect(llmStatus?.state).toBe("disconnected");
    expect(llmStatus?.error).toBe("LLM backend is not ready");

    const { rerender } = render(<StatusBar statuses={statuses} />);
    expect(screen.queryByTestId("health-error-hermes")).not.toBeInTheDocument();
    expect(screen.getByTestId("health-error-llm-backend")).toBeInTheDocument();

    // Now switch mock to connected
    mockFetch.mockImplementation(() =>
      Promise.resolve({
        ok: true,
        json: () => Promise.resolve({ state: "connected", latencyMs: 1 }),
      }),
    );

    // Wait for another polling interval
    await new Promise((resolve) => setTimeout(resolve, 100));

    const updatedStatuses = healthService.getStatuses();
    const updatedHermesStatus = updatedStatuses.find(
      (s) => s.serviceId === "hermes-agent",
    );
    const updatedLlmStatus = updatedStatuses.find(
      (s) => s.serviceId === "llm-backend",
    );
    expect(updatedHermesStatus?.state).toBe("connected");
    expect(updatedLlmStatus?.state).toBe("connected");

    rerender(<StatusBar statuses={updatedStatuses} />);
    expect(screen.queryByTestId("health-error-hermes")).not.toBeInTheDocument();
    expect(
      screen.queryByTestId("health-error-llm-backend"),
    ).not.toBeInTheDocument();
    expect(screen.getByTestId("status-hermes-agent")).toBeInTheDocument();

    healthService.stopPolling();
    vi.unstubAllGlobals();
  });
});
