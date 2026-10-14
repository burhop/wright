import {
  act,
  cleanup,
  fireEvent,
  render,
  screen,
  waitFor,
} from "@testing-library/react";
import { afterEach, expect, it, vi } from "vitest";
import { NativeSignin } from "./NativeSignin";
const scope = {
  workspace_id: "w",
  session_id: "s",
  plan_id: "p",
  plan_digest: "a".repeat(64),
};
const url = "https://issuer.example/auth?state=synthetic-private";
const status = {
  content: [],
  structuredContent: {
    workspace_id: "w",
    session_id: "s",
    plan_id: "p",
    presentation: "awaiting_user",
  },
  _meta: {
    "wright/signin": {
      authorization_url: url,
      callback_uri: "http://127.0.0.1:9505/oauth/callback",
    },
  },
};
afterEach(cleanup);
it("does not start sign-in on render and opens only app-private URL on explicit click", async () => {
  const call = vi.fn().mockResolvedValue(status);
  const openLink = vi.fn().mockResolvedValue(undefined);
  render(<NativeSignin scope={scope} call={call} openLink={openLink} />);
  expect(call).not.toHaveBeenCalled();
  fireEvent.click(screen.getByRole("button", { name: "Check sign-in status" }));
  const open = await screen.findByRole("button", {
    name: "Open provider sign-in",
  });
  expect(document.body.textContent).not.toContain("synthetic-private");
  expect(openLink).not.toHaveBeenCalled();
  fireEvent.click(open);
  expect(openLink).toHaveBeenCalledWith(url);
  expect(
    call.mock.calls.every((args) => args[0] === "wright_connection_signin"),
  ).toBe(true);
});
it("does not retry validation after lost acknowledgement", async () => {
  const call = vi.fn().mockRejectedValue(Error("transport lost"));
  render(<NativeSignin scope={scope} call={call} />);
  fireEvent.click(
    screen.getByRole("button", { name: "Sign in and validate provider" }),
  );
  expect(
    await screen.findByText(/Validation outcome is not confirmed/),
  ).toBeVisible();
  expect(
    screen.getByRole("button", { name: "Sign in and validate provider" }),
  ).toBeDisabled();
  fireEvent.click(screen.getByRole("button", { name: "Check sign-in status" }));
  await waitFor(() =>
    expect(
      call.mock.calls.filter(
        (args) => args[0] === "wright_connection_validate",
      ),
    ).toHaveLength(1),
  );
  expect(
    screen.queryByRole("button", { name: "Open provider sign-in" }),
  ).toBeNull();
});
it("rejects another plan's private navigation data", async () => {
  const call = vi.fn().mockResolvedValue({
    ...status,
    structuredContent: { ...status.structuredContent, plan_id: "other" },
  });
  render(<NativeSignin scope={scope} call={call} openLink={vi.fn()} />);
  fireEvent.click(screen.getByRole("button", { name: "Check sign-in status" }));
  expect(await screen.findByText("Sign-in status unavailable.")).toBeVisible();
  expect(
    screen.queryByRole("button", { name: "Open provider sign-in" }),
  ).toBeNull();
});

it("discards a pending manual status read when validation finishes", async () => {
  let finish!: (value: typeof status) => void;
  let lateRead!: (value: typeof status) => void;
  const validation = new Promise<typeof status>((resolve) => {
    finish = resolve;
  });
  const manual = new Promise<typeof status>((resolve) => {
    lateRead = resolve;
  });
  let reads = 0;
  const call = vi.fn((name: string) => {
    if (name === "wright_connection_validate") return validation;
    return ++reads === 1 ? Promise.resolve(status) : manual;
  });
  render(<NativeSignin scope={scope} call={call} />);
  fireEvent.click(
    screen.getByRole("button", { name: "Sign in and validate provider" }),
  );
  await screen.findByRole("button", { name: "Open provider sign-in" });
  fireEvent.click(screen.getByRole("button", { name: "Check sign-in status" }));
  await act(async () => finish(status));
  await act(async () => lateRead(status));
  expect(
    screen.queryByRole("button", { name: "Open provider sign-in" }),
  ).toBeNull();
});

it("requires a separate enable click and does not repeat an uncertain grant", async () => {
  const call = vi.fn(async (name: string) => {
    if (name === "wright_connection_enable")
      throw Error("lost acknowledgement");
    return {
      content: [],
      structuredContent: { ...scope, validation: { state: "passed" } },
    };
  });
  render(<NativeSignin scope={scope} call={call} />);
  expect(
    screen.queryByRole("button", { name: "Enable in this workspace" }),
  ).toBeNull();
  fireEvent.click(
    screen.getByRole("button", { name: "Sign in and validate provider" }),
  );
  const enable = await screen.findByRole("button", {
    name: "Enable in this workspace",
  });
  expect(
    call.mock.calls.filter(([name]) => name === "wright_connection_enable"),
  ).toHaveLength(0);
  fireEvent.click(enable);
  expect(
    await screen.findByText(/Workspace availability was not confirmed/),
  ).toBeVisible();
  expect(enable).toBeDisabled();
  fireEvent.click(enable);
  expect(
    call.mock.calls.filter(([name]) => name === "wright_connection_enable"),
  ).toHaveLength(1);
});
