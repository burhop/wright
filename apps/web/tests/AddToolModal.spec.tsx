import { render, screen, fireEvent, waitFor } from "@testing-library/react";
import { describe, it, expect, vi, beforeEach } from "vitest";
import { AddToolModal } from "../src/components/tools/AddToolModal";

describe("AddToolModal", () => {
  const mockOnClose = vi.fn();
  const mockOnSave = vi.fn();

  beforeEach(() => {
    vi.clearAllMocks();
  });

  it("does not render when isOpen is false", () => {
    render(
      <AddToolModal isOpen={false} onClose={mockOnClose} onSave={mockOnSave} />,
    );
    expect(
      screen.queryByText("Register Custom MCP Server"),
    ).not.toBeInTheDocument();
  });

  it("renders correctly when isOpen is true", () => {
    render(
      <AddToolModal isOpen={true} onClose={mockOnClose} onSave={mockOnSave} />,
    );
    expect(screen.getByText("Register Custom MCP Server")).toBeInTheDocument();
    expect(screen.getByLabelText("Server Name")).toBeInTheDocument();
    expect(screen.getByLabelText("Transport Type")).toBeInTheDocument();
  });

  it("requires name input field validation", async () => {
    render(
      <AddToolModal isOpen={true} onClose={mockOnClose} onSave={mockOnSave} />,
    );

    const submitBtn = screen.getByRole("button", { name: "Register" });
    fireEvent.click(submitBtn);

    expect(
      await screen.findByText("Server name is required."),
    ).toBeInTheDocument();
    expect(mockOnSave).not.toHaveBeenCalled();
  });

  it("requires command input validation for stdio transport", async () => {
    render(
      <AddToolModal isOpen={true} onClose={mockOnClose} onSave={mockOnSave} />,
    );

    // Type Name
    const nameInput = screen.getByLabelText("Server Name");
    fireEvent.change(nameInput, { target: { value: "My Stdio Server" } });

    const submitBtn = screen.getByRole("button", { name: "Register" });
    fireEvent.click(submitBtn);

    expect(
      await screen.findByText("CLI command is required for stdio transport."),
    ).toBeInTheDocument();
    expect(mockOnSave).not.toHaveBeenCalled();
  });

  it("splits stdio commands into arrays and invokes onSave", async () => {
    mockOnSave.mockResolvedValueOnce(undefined);
    render(
      <AddToolModal isOpen={true} onClose={mockOnClose} onSave={mockOnSave} />,
    );

    // Fill Name
    fireEvent.change(screen.getByLabelText("Server Name"), {
      target: { value: "Stdio Solver" },
    });

    // Select stdio transport (already selected by default)

    // Fill Command
    fireEvent.change(screen.getByLabelText("CLI Command / Arguments"), {
      target: { value: "uv run main.py --mesh" },
    });

    const submitBtn = screen.getByRole("button", { name: "Register" });
    fireEvent.click(submitBtn);

    await waitFor(() => {
      expect(mockOnSave).toHaveBeenCalledWith(
        "Stdio Solver",
        "stdio",
        ["uv", "run", "main.py", "--mesh"],
        "utilities",
      );
    });
  });

  it("validates URL protocol and calls onSave for SSE transport", async () => {
    mockOnSave.mockResolvedValueOnce(undefined);
    render(
      <AddToolModal isOpen={true} onClose={mockOnClose} onSave={mockOnSave} />,
    );

    // Fill Name
    fireEvent.change(screen.getByLabelText("Server Name"), {
      target: { value: "SSE Solver" },
    });

    // Select SSE transport
    fireEvent.change(screen.getByLabelText("Transport Type"), {
      target: { value: "sse" },
    });

    // Fill URL
    fireEvent.change(screen.getByLabelText("SSE Connection URL"), {
      target: { value: "http://127.0.0.1:4000/sse" },
    });

    const submitBtn = screen.getByRole("button", { name: "Register" });
    fireEvent.click(submitBtn);

    await waitFor(() => {
      expect(mockOnSave).toHaveBeenCalledWith(
        "SSE Solver",
        "sse",
        "http://127.0.0.1:4000/sse",
        "utilities",
      );
    });
  });

  it("triggers onClose when Cancel is clicked", () => {
    render(
      <AddToolModal isOpen={true} onClose={mockOnClose} onSave={mockOnSave} />,
    );

    const cancelBtn = screen.getByRole("button", { name: "Cancel" });
    fireEvent.click(cancelBtn);

    expect(mockOnClose).toHaveBeenCalled();
  });
});
