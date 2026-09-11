import { render, screen } from "@testing-library/react";
import { describe, expect, it } from "vitest";

import type { RivetRunStep } from "../../services/workspace-service";
import { RivetRunStepList } from "./RivetRunStepList";

describe("RivetRunStepList", () => {
  it("renders legacy steps without retained value collections", () => {
    const legacyStep = {
      step_id: "legacy-step",
      sequence: 1,
      node_id: "node-legacy",
      label: "Inspect legacy model",
      kind: "mcp_call",
      qualified_tool_name: "example.inspect",
      request_id: "request-legacy",
      trace_id: "trace-legacy",
      state: "succeeded",
      started_at: "2026-08-20T14:00:01Z",
      completed_at: "2026-08-20T14:00:03Z",
      duration_ms: 2000,
      reason_code: null,
    } as unknown as RivetRunStep;

    render(<RivetRunStepList steps={[legacyStep]} />);

    expect(
      screen.getByRole("button", { name: /Inspect legacy model/ }),
    ).toBeVisible();
    expect(screen.getAllByText("unavailable")).toHaveLength(2);
  });
});
