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
    expect(handleSend).toHaveBeenCalledWith("Test calculations");
    expect(input).toHaveValue("");
  });
});
