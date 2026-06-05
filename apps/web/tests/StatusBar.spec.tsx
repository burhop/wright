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
        state: "disconnected",
        lastChecked: Date.now(),
      },
      {
        serviceId: "inference",
        name: "LLM Inference",
        endpoint: "/api/inference/health",
        state: "unknown",
        lastChecked: null,
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
    expect(screen.getByTestId("status-inference")).toBeInTheDocument();

    expect(screen.getByTestId("health-error-hermes")).toBeInTheDocument();
    expect(screen.getByTestId("latest-trace")).toHaveTextContent(
      /TRACE: tr-abc12/,
    );
  });

  it("mocks fetch and tests connected/disconnected status polling updates", async () => {
    const mockFetch = vi.fn().mockImplementation((url: string) => {
      if (url.includes("/api/agent/health")) {
        return Promise.resolve({
          ok: true,
          json: () => Promise.resolve({ state: "disconnected", latencyMs: 4 }),
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

    expect(wrightStatus?.state).toBe("connected");
    expect(hermesStatus?.state).toBe("disconnected");

    const { rerender } = render(<StatusBar statuses={statuses} />);
    expect(screen.getByTestId("health-error-hermes")).toBeInTheDocument();

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
    expect(updatedHermesStatus?.state).toBe("connected");

    rerender(<StatusBar statuses={updatedStatuses} />);
    expect(screen.queryByTestId("health-error-hermes")).not.toBeInTheDocument();
    expect(screen.getByTestId("status-hermes-agent")).toBeInTheDocument();

    healthService.stopPolling();
    vi.unstubAllGlobals();
  });
});
