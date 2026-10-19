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

const recovered = (
  state = "passed",
  enabled = false,
  digest = scope.plan_digest,
) => ({
  content: [],
  structuredContent: {
    ...scope,
    plan_digest: digest,
    presentation: "not_pending",
    provider_status: {
      installed: true,
      active: false,
      enabled_here: enabled,
      recorded_validation: { evidence_id: "validation-saved", state },
    },
  },
});
it("recovers a lost validation reply by reading saved status before explicit enable, without validating again", async () => {
  const call = vi.fn(async (name: string) => {
    if (name === "wright_connection_validate")
      throw Error("withheld after saved validation");
    if (name === "wright_connection_enable")
      return {
        content: [],
        structuredContent: {
          ...scope,
          enablement: { enabled: true, invocation_approved: false },
        },
      };
    return recovered();
  });
  render(<NativeSignin scope={scope} call={call} />);
  fireEvent.click(
    screen.getByRole("button", { name: "Sign in and validate provider" }),
  );
  await screen.findByText(/Validation outcome is not confirmed/);
  fireEvent.click(screen.getByRole("button", { name: "Check sign-in status" }));
  const enable = await screen.findByRole("button", {
    name: "Enable in this workspace",
  });
  expect(enable).toBeEnabled();
  expect(
    call.mock.calls.filter(([name]) => name === "wright_connection_enable"),
  ).toHaveLength(0);
  expect(
    call.mock.calls.filter(([name]) => name === "wright_connection_validate"),
  ).toHaveLength(1);
  fireEvent.click(enable);
  await screen.findByText(/Enabled in this workspace/);
  expect(
    call.mock.calls.filter(([name]) => name === "wright_connection_enable"),
  ).toHaveLength(1);
});
it("reopens a saved enabled provider by read only and never replays the grant", async () => {
  const call = vi.fn().mockResolvedValue(recovered("passed", true));
  render(<NativeSignin scope={scope} call={call} />);
  expect(call).not.toHaveBeenCalled();
  fireEvent.click(screen.getByRole("button", { name: "Check sign-in status" }));
  await screen.findByText(/Saved workspace availability is enabled/);
  expect(
    screen.getByRole("button", { name: "Enable in this workspace" }),
  ).toBeDisabled();
  expect(call.mock.calls.map(([name]) => name)).toEqual([
    "wright_connection_signin",
  ]);
});
it.each(["failed", "stale", "blocked"])(
  "does not offer enable for recorded %s validation",
  async (state) => {
    const call = vi.fn().mockResolvedValue(recovered(state));
    render(<NativeSignin scope={scope} call={call} />);
    fireEvent.click(
      screen.getByRole("button", { name: "Check sign-in status" }),
    );
    await screen.findByText(new RegExp("Saved provider check is " + state));
    expect(
      screen.queryByRole("button", { name: "Enable in this workspace" }),
    ).toBeNull();
    expect(call).toHaveBeenCalledTimes(1);
  },
);
it("rejects recovered provider status for another plan digest", async () => {
  const call = vi
    .fn()
    .mockResolvedValue(recovered("passed", false, "b".repeat(64)));
  render(<NativeSignin scope={scope} call={call} />);
  fireEvent.click(screen.getByRole("button", { name: "Check sign-in status" }));
  await screen.findByText("Sign-in status unavailable.");
  expect(
    screen.queryByRole("button", { name: "Enable in this workspace" }),
  ).toBeNull();
});

it("shows a device code and opens only the operator URL without callback instructions", async () => {
  const deviceStatus = {
    ...status,
    _meta: {
      "wright/signin": {
        device: {
          verification_uri: "https://issuer.example/device",
          verification_uri_complete:
            "https://issuer.example/device?user_code=TEST-1234",
          user_code: "TEST-1234",
        },
      },
    },
  };
  const call = vi.fn().mockResolvedValue(deviceStatus);
  const openLink = vi.fn().mockResolvedValue(undefined);
  render(<NativeSignin scope={scope} call={call} openLink={openLink} />);
  fireEvent.click(screen.getByRole("button", { name: "Check sign-in status" }));
  expect(await screen.findByText("TEST-1234")).toBeVisible();
  expect(document.body.textContent).toContain("No network setup is needed");
  expect(document.body.textContent).not.toContain("Forward");
  expect(document.body.textContent).not.toContain("127.0.0.1");
  expect(openLink).not.toHaveBeenCalled();
  fireEvent.click(
    screen.getByRole("button", { name: "Open provider sign-in" }),
  );
  expect(openLink).toHaveBeenCalledWith(
    "https://issuer.example/device?user_code=TEST-1234",
  );
  call.mockResolvedValue({
    ...deviceStatus,
    structuredContent: {
      ...deviceStatus.structuredContent,
      presentation: "expired",
    },
    _meta: {},
  });
  fireEvent.click(screen.getByRole("button", { name: "Check sign-in status" }));
  await waitFor(() => expect(screen.queryByText("TEST-1234")).toBeNull());
});

it("rejects a device completion URL on another origin", async () => {
  const call = vi.fn().mockResolvedValue({
    ...status,
    _meta: {
      "wright/signin": {
        device: {
          verification_uri: "https://issuer.example/device",
          verification_uri_complete: "https://other.example/steal",
          user_code: "TEST-1234",
        },
      },
    },
  });
  const openLink = vi.fn();
  render(<NativeSignin scope={scope} call={call} openLink={openLink} />);
  fireEvent.click(screen.getByRole("button", { name: "Check sign-in status" }));
  expect(await screen.findByText("Sign-in status unavailable.")).toBeVisible();
  expect(screen.queryByText("TEST-1234")).toBeNull();
  expect(openLink).not.toHaveBeenCalled();
});

it("allows a new explicit connection attempt only after reading a recorded terminal failure", async () => {
  const call = vi.fn(async (name: string) =>
    name === "wright_connection_signin"
      ? {
          content: [],
          structuredContent: {
            ...scope,
            presentation: "unavailable",
            provider_status: {
              installed: true,
              active: false,
              enabled_here: false,
              recorded_validation: {
                state: "failed",
                evidence_id: "failed-check",
              },
            },
          },
        }
      : {
          content: [],
          structuredContent: { ...scope, validation: { state: "failed" } },
        },
  );
  render(<NativeSignin scope={scope} call={call} providerName="SteveCAD" />);
  fireEvent.click(screen.getByRole("button", { name: "Connect SteveCAD" }));
  await screen.findByText(/Protocol validation: failed/);
  expect(
    screen.getByRole("button", { name: "Connect SteveCAD" }),
  ).toBeDisabled();
  fireEvent.click(screen.getByRole("button", { name: "Check sign-in status" }));
  await waitFor(() =>
    expect(
      screen.getByRole("button", { name: "Connect SteveCAD" }),
    ).toBeEnabled(),
  );
  expect(
    call.mock.calls.filter(([name]) => name === "wright_connection_validate"),
  ).toHaveLength(1);
  fireEvent.click(screen.getByRole("button", { name: "Connect SteveCAD" }));
  await waitFor(() =>
    expect(
      call.mock.calls.filter(([name]) => name === "wright_connection_validate"),
    ).toHaveLength(2),
  );
  expect(document.body.textContent).not.toContain("forwarding");
});
