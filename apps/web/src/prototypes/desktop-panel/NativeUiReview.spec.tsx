import { afterEach, expect, it, vi } from "vitest";
import {
  cleanup,
  fireEvent,
  render,
  screen,
  waitFor,
} from "@testing-library/react";
import { NativeUiReview } from "./NativeUiReview";
import type { HomeCall } from "./NativeHomePanel";

afterEach(() => {
  cleanup();
  document.body.innerHTML = "";
  vi.restoreAllMocks();
});
const scope = {
  workspace_id: "a",
  session_id: "chat-a",
  workspace_name: "A",
  available: true,
  reason: null,
};
const location = () => ({
  active_surface: "home" as const,
  editor_has_unsaved_changes: false,
});

it.each(["sent", "unsupported", "lost"] as const)(
  "selects safely, saves once and reports %s chat delivery",
  async (delivery) => {
    const surface = document.createElement("main");
    surface.innerHTML =
      '<button>Do not activate</button><input value="private-input">';
    document.body.append(surface);
    const action = vi.fn();
    surface.querySelector("button")!.addEventListener("click", action);
    const call = vi.fn<HomeCall>().mockImplementation(async (_tool, args) => {
      const request = args.request as Record<string, string>;
      return {
        content: [],
        structuredContent: {
          ok: true,
          document: {
            workspace_id: "a",
            session_id: "chat-a",
            filename: request.filename,
            path: `uploads/${request.sha256}/${request.filename}`,
            sha256: request.sha256,
            bytes: atob(request.content_base64).length,
          },
        },
      };
    });
    const onSaved = vi.fn();
    const requestReview = vi.fn().mockImplementation(async () => {
      if (delivery === "lost") throw Error("Unconfirmed delivery");
      return delivery;
    });
    render(
      <NativeUiReview
        root={() => surface}
        host={() => undefined}
        location={location}
        workspace={() => scope}
        events={[]}
        call={call}
        onSaved={onSaved}
        requestReview={requestReview}
      />,
    );
    fireEvent.click(screen.getByRole("button", { name: "Report UI problem" }));
    expect(call).not.toHaveBeenCalled();
    fireEvent.click(
      screen.getByRole("button", { name: "Point to an element" }),
    );
    fireEvent.click(screen.getByRole("button", { name: "Do not activate" }));
    expect(action).not.toHaveBeenCalled();
    await waitFor(() =>
      expect(screen.getByLabelText("Problem description")).toHaveFocus(),
    );
    fireEvent.change(screen.getByLabelText("Problem description"), {
      target: {
        value: "Clipped control. Bearer accidental-token sk-privatekey",
      },
    });
    expect(call).not.toHaveBeenCalled();
    fireEvent.click(screen.getByRole("button", { name: "Save UI report" }));
    await screen.findByText(/Report saved for the tester/);
    expect(call).toHaveBeenCalledTimes(1);
    expect(call.mock.calls[0][0]).toBe("wright_workspace_file_upload");
    const request = call.mock.calls[0][1].request as Record<string, string>;
    const text = new TextDecoder().decode(
      Uint8Array.from(atob(request.content_base64), (c) => c.charCodeAt(0)),
    );
    expect(text).toContain("Clipped control");
    expect(text).not.toMatch(
      /private-input|Do not activate|accidental-token|sk-privatekey/,
    );
    expect(JSON.parse(text).selected_element.relative_selector).toBe(
      "button:nth-of-type(1)",
    );
    expect(onSaved).toHaveBeenCalledExactlyOnceWith(
      scope,
      `uploads/${request.sha256}/${request.filename}`,
    );
    expect(requestReview).not.toHaveBeenCalled();
    const ask = screen.getByRole("button", { name: "Ask chat to review" });
    fireEvent.click(ask);
    fireEvent.click(ask);
    await screen.findByText(
      delivery === "sent"
        ? "Review request sent to this conversation."
        : delivery === "unsupported"
          ? /does not support panel-to-chat/
          : /Chat delivery is unconfirmed/,
    );
    expect(requestReview).toHaveBeenCalledExactlyOnceWith(
      scope,
      `uploads/${request.sha256}/${request.filename}`,
    );
    expect(ask).toBeDisabled();
    fireEvent.click(screen.getByRole("button", { name: "Close report" }));
    expect(
      screen.getByRole("button", { name: "Report UI problem" }),
    ).toHaveFocus();
  },
);

it("cancels element picking without a write and explains missing workspace scope", () => {
  const surface = document.createElement("main");
  document.body.append(surface);
  const call = vi.fn();
  render(
    <NativeUiReview
      root={() => surface}
      host={() => undefined}
      location={location}
      workspace={() => undefined}
      events={[]}
      call={call}
    />,
  );
  fireEvent.click(screen.getByRole("button", { name: "Report UI problem" }));
  expect(screen.queryByRole("button", { name: "Save UI report" })).toBeNull();
  expect(screen.getByText(/Choose an available workspace/)).toBeVisible();
  fireEvent.click(screen.getByRole("button", { name: "Point to an element" }));
  fireEvent.keyDown(document, { key: "Escape" });
  expect(screen.getByLabelText("Problem description")).toBeVisible();
  expect(call).not.toHaveBeenCalled();
});
