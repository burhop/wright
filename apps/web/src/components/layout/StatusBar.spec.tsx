import { render, screen } from "@testing-library/react";
import { describe, expect, it } from "vitest";
import StatusBar from "./StatusBar";

describe("agent model status scope", () => {
  it("names the agent model without implying all workflow providers are unavailable", () => {
    render(<StatusBar />);
    expect(screen.getByText("Agent model")).toBeVisible();
    expect(screen.queryByText("LLM Backend")).not.toBeInTheDocument();
  });

  it("keeps configured but unprobed state distinct from a successful connection", () => {
    const reason =
      "An agent model is configured in Hermes. Its provider connection has not been checked; workflow model readiness is assessed separately.";
    render(
      <StatusBar
        statuses={[
          {
            serviceId: "llm-backend",
            name: "Agent model",
            endpoint: "/api/inference/health",
            state: "unknown",
            lastChecked: 123,
            error: reason,
          },
        ]}
      />,
    );
    expect(screen.getByTestId("status-llm-backend")).toHaveAttribute(
      "title",
      `Agent model: ${reason}`,
    );
    expect(
      screen.queryByTestId("health-error-llm-backend"),
    ).not.toBeInTheDocument();
  });
});
