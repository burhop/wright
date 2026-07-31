import { render, screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { afterEach, describe, expect, it, vi } from "vitest";

import { hostAdapter } from "../../services/host-adapter";
import type { SurfaceDescriptor } from "../../services/surfaces/surface-contract";
import { LiveAppControls } from "./LiveAppControls";

const descriptor = (
  lifecycle: SurfaceDescriptor["lifecycle"],
  withInstance = lifecycle !== "declared",
): SurfaceDescriptor => ({
  schemaVersion: 1,
  surfaceId: "surface-app",
  workspaceId: "workspace-1",
  source: {
    kind: "live_app",
    sourceId: "demo.app",
    sourceVersion: "a".repeat(64),
    manifestId: "demo.app",
  },
  title: "Demo application",
  lifecycle,
  instance: withInstance
    ? { instanceId: "instance-1", generation: 2, sharing: "shared" }
    : null,
  presentations: [],
  capabilities: [],
  revision: 3,
  createdAt: "2026-07-30T12:00:00Z",
  updatedAt: "2026-07-30T12:00:00Z",
});

const runtime = (state: SurfaceDescriptor["lifecycle"]) => ({
  surfaceId: "surface-app",
  instanceId: "instance-1",
  generation: 2,
  state,
  sharing: "shared",
  ownership: "launched",
  platform: "windows_job",
  lifetimePolicy: "workspace",
  leaseExpiresAt: null,
  idleSeconds: null,
  lastActivityAt: "2026-07-30T12:00:00Z",
  startedAt: "2026-07-30T12:00:00Z",
  readyAt: "2026-07-30T12:00:01Z",
  endedAt: null,
  failure: null,
  actions:
    state === "ready"
      ? [
          { operation: "restart", label: "Restart application" },
          { operation: "stop", label: "Stop application" },
        ]
      : [],
});

afterEach(() => {
  vi.restoreAllMocks();
});

describe("LiveAppControls", () => {
  it("starts a declared app and exposes only backend-projected next actions", async () => {
    const user = userEvent.setup();
    const changed = vi.fn();
    const fetch = vi
      .spyOn(hostAdapter, "fetch")
      .mockResolvedValue(
        new Response(JSON.stringify(runtime("ready")), { status: 202 }),
      );
    render(
      <LiveAppControls
        descriptor={descriptor("declared", false)}
        sessionId="session-1"
        onRuntimeChange={changed}
      />,
    );

    await user.click(screen.getByRole("button", { name: "Start application" }));
    await waitFor(() =>
      expect(screen.getByRole("status")).toHaveTextContent("ready"),
    );
    expect(
      screen.getByRole("button", { name: "Restart application" }),
    ).toBeVisible();
    expect(
      screen.getByRole("button", { name: "Stop application" }),
    ).toBeVisible();
    expect(changed).toHaveBeenCalledWith(
      expect.objectContaining({ state: "ready" }),
    );
    expect(fetch).toHaveBeenCalledWith(
      expect.stringMatching(/\/surface-app\/start$/),
      expect.objectContaining({
        method: "POST",
        headers: expect.objectContaining({
          "X-Wright-Workspace-ID": "workspace-1",
          "X-Wright-Session-ID": "session-1",
          "Idempotency-Key": expect.stringContaining("live-app-start"),
        }),
      }),
    );
  });

  it("provides accessible health and bounded log inspection", async () => {
    const user = userEvent.setup();
    vi.spyOn(hostAdapter, "fetch").mockImplementation(async (url) => {
      const value = String(url);
      if (value.endsWith("/health")) {
        return new Response(
          JSON.stringify({
            instanceId: "instance-1",
            generation: 2,
            state: "ready",
            ok: true,
            diagnosticCode: null,
            message: "Application probe succeeded",
            observedStatus: 200,
            attempts: 1,
          }),
        );
      }
      if (value.includes("/logs?")) {
        return new Response(
          JSON.stringify({
            entries: [
              {
                sequence: 1,
                stream: "stdout",
                message: "dashboard ready",
                capturedAt: "2026-07-30T12:00:00Z",
                byteCount: 15,
              },
            ],
            rotated: false,
            droppedBytes: 4,
            nextSequence: 2,
          }),
        );
      }
      return new Response(JSON.stringify(runtime("ready")));
    });
    render(
      <LiveAppControls
        descriptor={descriptor("ready")}
        sessionId="session-1"
      />,
    );
    await screen.findByRole("button", { name: "Check application health" });

    await user.click(
      screen.getByRole("button", { name: "Check application health" }),
    );
    expect(await screen.findByRole("note")).toHaveTextContent(/healthy/i);
    await user.click(
      screen.getByRole("button", { name: "View application logs" }),
    );
    expect(
      await screen.findByRole("log", { name: "Managed application logs" }),
    ).toHaveTextContent("dashboard ready");
    expect(screen.getByRole("log")).toHaveTextContent(
      "4 log bytes were dropped",
    );
  });
});
