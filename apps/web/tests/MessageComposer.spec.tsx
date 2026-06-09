import { render, screen, fireEvent } from "@testing-library/react";
import { describe, it, expect, vi } from "vitest";
import MessageComposer from "../src/components/chat/MessageComposer";

describe("MessageComposer", () => {
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
      />
    );

    const input = screen.getByTestId("composer-input");
    expect(input).not.toBeDisabled();

    const cancelBtn = screen.getByTestId("composer-cancel");
    expect(cancelBtn).toBeInTheDocument();

    fireEvent.click(cancelBtn);
    expect(handleCancel).toHaveBeenCalledTimes(1);
  });
});
