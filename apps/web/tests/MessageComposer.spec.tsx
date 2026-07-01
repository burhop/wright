import { render, screen, fireEvent, waitFor } from "@testing-library/react";
import { describe, it, expect, vi, beforeEach } from "vitest";
import MessageComposer from "../src/components/chat/MessageComposer";

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
});
