import { render, screen, fireEvent, waitFor } from "@testing-library/react";
import { describe, it, expect, vi, beforeEach } from "vitest";
import MessageComposer from "../src/components/chat/MessageComposer";
import { workspaceService } from "../src/services/workspace-service";
import { agentService } from "../src/services/agent-service";

vi.mock("../src/services/agent-service", () => ({
  agentService: {
    getCommands: vi.fn().mockResolvedValue([]),
    uploadFile: vi.fn(),
  },
  default: {
    getCommands: vi.fn().mockResolvedValue([]),
    uploadFile: vi.fn(),
  },
}));

// Mock workspace-service
vi.mock("../src/services/workspace-service", () => ({
  workspaceService: {
    getWorkspaceFiles: vi.fn().mockResolvedValue({
      type: "directory",
      name: "root",
      path: "/",
      children: [
        { type: "file", name: "package.json", path: "/package.json" },
        { type: "file", name: "index.css", path: "/src/index.css" },
      ],
    }),
    getMcpStatus: vi.fn().mockResolvedValue({
      status: "ok",
      message: "Healthy",
      running_mcps: [],
    }),
  },
}));

describe("MessageComposer", () => {
  beforeEach(() => {
    vi.clearAllMocks();
    vi.mocked(agentService.getCommands).mockResolvedValue([]);
  });

  it("sends typed message on submit", () => {
    const handleSend = vi.fn();
    render(<MessageComposer onSend={handleSend} />);

    const input = screen.getByTestId("composer-input");
    const sendBtn = screen.getByTestId("composer-send");

    fireEvent.change(input, { target: { value: "Test calculations" } });
    expect(sendBtn).not.toBeDisabled();

    fireEvent.click(sendBtn);
    expect(handleSend).toHaveBeenCalledWith("Test calculations", []);
    expect(input).toHaveValue("");
  });

  it("renders cancel button and triggers onCancel when isStreaming is true", () => {
    const handleSend = vi.fn();
    const handleCancel = vi.fn();
    render(
      <MessageComposer
        onSend={handleSend}
        isStreaming={true}
        onCancel={handleCancel}
      />,
    );

    const input = screen.getByTestId("composer-input");
    expect(input).not.toBeDisabled();

    const cancelBtn = screen.getByTestId("composer-cancel");
    expect(cancelBtn).toBeInTheDocument();

    fireEvent.click(cancelBtn);
    expect(handleCancel).toHaveBeenCalledTimes(1);
  });

  it("triggers workspace file autocomplete when '@' is typed", async () => {
    const handleSend = vi.fn();
    render(<MessageComposer onSend={handleSend} sessionId="test-session" />);

    const input = screen.getByTestId("composer-input");

    // Type "@"
    fireEvent.change(input, { target: { value: "@" } });

    // Wait for the popup list items to render
    await waitFor(() => {
      expect(screen.getByText("@/package.json")).toBeInTheDocument();
      expect(screen.getByText("@/src/index.css")).toBeInTheDocument();
    });

    // Click the package.json file option
    const fileOption = screen.getByText("@/package.json");
    fireEvent.click(fileOption);

    // Verify it completed in the text input
    expect(input).toHaveValue("@/package.json ");
  });

  it("opens a useful add-context menu from the plus button", () => {
    render(<MessageComposer onSend={vi.fn()} sessionId="test-session" />);

    fireEvent.click(screen.getByRole("button", { name: "Add context" }));

    expect(screen.getByTestId("composer-plus-menu")).toBeInTheDocument();
    expect(
      screen.getByRole("menuitem", { name: /command/i }),
    ).toBeInTheDocument();
    expect(
      screen.getByRole("menuitem", { name: /workspace file/i }),
    ).toBeInTheDocument();
    expect(screen.getByLabelText("Upload image")).toBeInTheDocument();
    expect(
      screen.getByText("Run a Hermes or Wright slash command"),
    ).toBeInTheDocument();
    expect(
      screen.getByText("Reference a file from this workspace"),
    ).toBeInTheDocument();
  });

  it("shows the Wright slash command from the command API", async () => {
    vi.mocked(agentService.getCommands).mockResolvedValueOnce([
      {
        name: "wright",
        description: "Wright engineering platform",
        prefix: "/",
      },
    ]);

    render(<MessageComposer onSend={vi.fn()} sessionId="test-session" />);

    const input = screen.getByTestId("composer-input");
    fireEvent.change(input, { target: { value: "/w" } });

    expect(await screen.findByText("/wright")).toBeInTheDocument();
  });

  it("shows a warning MCP indicator when an expected server is inactive", async () => {
    vi.mocked(workspaceService.getMcpStatus).mockResolvedValueOnce({
      status: "warning",
      message: "MCP server installed but not active: Jarvis OnShape MCP",
      running_mcps: [
        {
          name: "Jarvis OnShape MCP",
          status: "inactive",
          error_message: null,
        },
      ],
    });

    render(<MessageComposer onSend={vi.fn()} sessionId="test-session" />);

    const indicator = await screen.findByTestId("mcp-status-indicator");
    expect(indicator).toHaveStyle({ backgroundColor: "#f59e0b" });
    expect(indicator).toHaveAttribute(
      "title",
      "MCP server installed but not active: Jarvis OnShape MCP",
    );

    fireEvent.click(indicator);

    expect(screen.getByTestId("mcp-status-popup")).toBeInTheDocument();
    expect(screen.getByText("MCP Status: Needs attention")).toBeInTheDocument();
    expect(screen.getByText("Jarvis OnShape MCP")).toBeInTheDocument();
    expect(screen.getByText("inactive")).toBeInTheDocument();
  });
});
