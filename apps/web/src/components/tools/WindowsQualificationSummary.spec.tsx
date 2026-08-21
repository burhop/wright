import { render, screen, within } from "@testing-library/react";
import { describe, expect, it } from "vitest";
import type { WindowsQualificationSummary as Summary } from "../../services/mcp-service";
import { WindowsQualificationSummary } from "./WindowsQualificationSummary";

const summary: Summary = {
  observed_at: "2026-08-13T12:00:00Z",
  evidence_path:
    "docs/mcp-catalog/evidence/windows-qualification-2026-08-13/brep-mcp-windows-qualification.json",
  evidence_digest: "a".repeat(64),
  current: true,
  stale_reasons: [],
  source: {
    result: "passed",
    label: "Source verified",
    reason_code: "source_pinned",
  },
  package_or_registration: {
    result: "passed",
    label: "MCP server installed",
    reason_code: "package_installed",
  },
  startup: {
    result: "passed",
    label: "MCP server started",
    reason_code: "startup_passed",
  },
  protocol: {
    result: "passed",
    label: "MCP protocol passed",
    reason_code: "protocol_passed",
  },
  host_or_backend: {
    result: "partial",
    label: "Host app needed",
    reason_code: "commercial_host_not_configured",
  },
  wright_setup: {
    result: "passed",
    label: "Added to Wright",
    reason_code: "wright_registered",
  },
  gateway: {
    result: "not_tested",
    label: "Gateway check pending",
    reason_code: "gateway_not_tested",
  },
  cleanup: {
    result: "passed",
    label: "Cleanup passed",
    reason_code: "cleanup_passed",
  },
};

describe("WindowsQualificationSummary", () => {
  it("shows eight independent, plainly named qualification boundaries", () => {
    render(<WindowsQualificationSummary summary={summary} />);

    const region = screen.getByRole("region", {
      name: "Windows qualification",
    });
    for (const label of [
      "Source",
      "MCP package or registration",
      "Startup",
      "MCP protocol",
      "Host app or backend",
      "Wright setup",
      "Wright gateway",
      "Cleanup",
    ]) {
      expect(within(region).getByText(label)).toBeVisible();
    }
    expect(within(region).getByText("MCP server installed")).toBeVisible();
    expect(within(region).getByText("Host app needed")).toBeVisible();
    expect(within(region).getByText("Gateway check pending")).toBeVisible();
    expect(
      within(region).getByText("Tested on this Windows setup"),
    ).toBeVisible();
    expect(
      within(region).getByTestId("windows-qualification-evidence-toggle"),
    ).toHaveTextContent("Evidence reference");
  });

  it("makes stale evidence explicit instead of presenting it as current", () => {
    render(
      <WindowsQualificationSummary
        summary={{
          ...summary,
          current: false,
          stale_reasons: ["qualification_source_changed"],
        }}
      />,
    );

    expect(screen.getByRole("status")).toHaveTextContent(
      "Recheck this Windows qualification",
    );
    expect(screen.getByRole("status")).toHaveTextContent(
      "The MCP source changed",
    );
  });
});
