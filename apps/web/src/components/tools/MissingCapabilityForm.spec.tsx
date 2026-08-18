import { render, screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { beforeEach, describe, expect, it, vi } from "vitest";
import { mcpService } from "../../services/mcp-service";
import { MissingCapabilityForm } from "./MissingCapabilityForm";

vi.mock("../../services/mcp-service", async (loadOriginal) => {
  const original =
    await loadOriginal<typeof import("../../services/mcp-service")>();
  return {
    ...original,
    mcpService: {
      ...original.mcpService,
      reportMissingCapability: vi.fn(),
    },
  };
});

const context = {
  query: "enclosure cooling",
  filters: { domain: "cfd", compatibility: "incompatible" },
};

const saved = {
  report_id: "report-1",
  name: "Requested CFD MCP",
  vendor: "Example Solver",
  domains: ["cfd"],
  expected_task: "Run a cooling study",
  search_context: context,
  reporter: "engineer-1",
  created_at: "2026-08-12T15:00:00Z",
  updated_at: "2026-08-12T15:00:00Z",
  state: "submitted" as const,
};

describe("MissingCapabilityForm", () => {
  beforeEach(() => vi.clearAllMocks());

  it("preserves visible search context and browser-validates required fields", async () => {
    const user = userEvent.setup();
    render(
      <MissingCapabilityForm
        isOpen
        searchContext={context}
        onClose={vi.fn()}
      />,
    );
    expect(
      screen.getByTestId("missing-capability-search-context"),
    ).toHaveTextContent(
      "enclosure cooling · domain: cfd · compatibility: incompatible",
    );
    await user.click(
      screen.getByRole("button", { name: "Submit review request" }),
    );
    expect(mcpService.reportMissingCapability).not.toHaveBeenCalled();
  });

  it("submits structured fields and explains that the result is not installable", async () => {
    const user = userEvent.setup();
    vi.mocked(mcpService.reportMissingCapability).mockResolvedValue(saved);
    render(
      <MissingCapabilityForm
        isOpen
        searchContext={context}
        onClose={vi.fn()}
      />,
    );
    await user.type(screen.getByLabelText("MCP server name"), saved.name);
    await user.clear(screen.getByLabelText("Vendor or publisher"));
    await user.type(screen.getByLabelText("Vendor or publisher"), saved.vendor);
    await user.type(
      screen.getByLabelText("What engineering task should it perform?"),
      saved.expected_task,
    );
    await user.click(
      screen.getByRole("button", { name: "Submit review request" }),
    );

    expect(mcpService.reportMissingCapability).toHaveBeenCalledWith(
      expect.objectContaining({
        name: saved.name,
        vendor: saved.vendor,
        domains: ["cfd"],
        expected_task: saved.expected_task,
        search_context: context,
      }),
      expect.stringContaining("missing-capability-"),
    );
    expect(await screen.findByRole("status")).toHaveTextContent("report-1");
    expect(screen.getByRole("status")).toHaveTextContent(
      "not an installable MCP server",
    );
  });

  it("keeps the form and context available after a safe failure", async () => {
    const user = userEvent.setup();
    vi.mocked(mcpService.reportMissingCapability).mockRejectedValue(
      new Error("Review the source URL."),
    );
    render(
      <MissingCapabilityForm
        isOpen
        searchContext={context}
        onClose={vi.fn()}
      />,
    );
    await user.type(screen.getByLabelText("MCP server name"), "Broken source");
    await user.type(
      screen.getByLabelText("What engineering task should it perform?"),
      "Inspect a model",
    );
    await user.click(
      screen.getByRole("button", { name: "Submit review request" }),
    );
    expect(await screen.findByRole("alert")).toHaveTextContent(
      "Review the source URL.",
    );
    expect(screen.getByLabelText("MCP server name")).toHaveValue(
      "Broken source",
    );
    expect(
      screen.getByTestId("missing-capability-search-context"),
    ).toHaveTextContent("enclosure cooling");
  });

  it("traps focus and closes with Escape", async () => {
    const user = userEvent.setup();
    const onClose = vi.fn();
    render(
      <MissingCapabilityForm
        isOpen
        searchContext={context}
        onClose={onClose}
      />,
    );

    const close = screen.getByTestId("missing-capability-close");
    await waitFor(() => expect(close).toHaveFocus());
    await user.keyboard("{Shift>}{Tab}{/Shift}");
    expect(screen.getByTestId("missing-capability-submit")).toHaveFocus();
    await user.keyboard("{Escape}");
    expect(onClose).toHaveBeenCalledOnce();
  });
});
