import type { Page } from "@playwright/test";

export const workspaceSurfaceTestPort =
  process.env.WRIGHT_PLAYWRIGHT_PORT || "5173";

export function workspaceSurfaceOrigin(hostname: string): string {
  return `http://${hostname}:${workspaceSurfaceTestPort}`;
}

export const liveSurface = (
  lifecycle: "ready" | "unhealthy" | "stopped" = "ready",
  options: {
    readonly surfaceId?: string;
    readonly panelEligible?: boolean;
    readonly browserEligible?: boolean;
    readonly sharing?: "shared" | "isolated";
    readonly instanceId?: string;
    readonly generation?: number;
  } = {},
) => ({
  schemaVersion: 1,
  surfaceId: options.surfaceId ?? "surface-app",
  workspaceId: "ws-1",
  source: {
    kind: "live_app",
    sourceId: "shareable-app",
    sourceVersion: "a".repeat(64),
    manifestId: "shareable-app",
  },
  title: "Shareable app",
  lifecycle,
  instance:
    lifecycle === "stopped"
      ? null
      : {
          instanceId: options.instanceId ?? "instance-shared",
          generation: options.generation ?? 3,
          sharing: options.sharing ?? "shared",
          readyAt: "2026-07-30T12:00:00Z",
        },
  presentations: [
    {
      kind: "panel",
      eligible: options.panelEligible ?? true,
      ...(options.panelEligible === false
        ? { reason: "Application forbids framing" }
        : {}),
    },
    { kind: "browser", eligible: options.browserEligible ?? true },
  ],
  capabilities: [],
  revision: lifecycle === "stopped" ? 5 : 4,
  createdAt: "2026-07-30T12:00:00Z",
  updatedAt: "2026-07-30T12:04:00Z",
});

export async function mockManagedRivetSurface(
  page: Page,
  canvasHtml: string,
): Promise<{ startCount: () => number }> {
  let declared = false;
  let lifecycle: "declared" | "ready" = "declared";
  let starts = 0;
  const token = "r".repeat(43);
  const surface = () => ({
    schemaVersion: 1,
    surfaceId: "surface-rivet",
    workspaceId: "ws-1",
    source: {
      kind: "live_app",
      sourceId: "wright.rivet-editor",
      sourceVersion: "a".repeat(64),
      manifestId: "wright.rivet-editor",
    },
    title: "Rivet",
    lifecycle,
    instance:
      lifecycle === "ready"
        ? {
            instanceId: "instance-rivet",
            generation: 1,
            sharing: "isolated",
            readyAt: "2026-07-30T12:00:00Z",
          }
        : null,
    presentations:
      lifecycle === "ready"
        ? [
            { kind: "panel", eligible: true },
            { kind: "browser", eligible: true },
          ]
        : [],
    capabilities: [],
    revision: lifecycle === "ready" ? 3 : 1,
    createdAt: "2026-07-30T12:00:00Z",
    updatedAt: "2026-07-30T12:00:00Z",
  });

  await page.route("**/api/workspace/workflows/editor/surface", (route) =>
    route.fulfill({
      json: {
        availability: "available",
        detail: null,
        manifest: {
          schemaVersion: 1,
          id: "wright.rivet-editor",
          version: "2.0.0",
          title: "Rivet",
          launch: { mode: "command", argv: ["python", "host.py"] },
        },
      },
    }),
  );
  await page.route("**/api/workspace/surfaces", async (route) => {
    if (route.request().method() === "POST") {
      declared = true;
      await route.fulfill({ status: 201, json: surface() });
      return;
    }
    await route.fulfill({ json: { items: declared ? [surface()] : [] } });
  });
  await page.route(
    "**/api/workspace/surfaces/surface-rivet/start",
    async (route) => {
      starts += 1;
      lifecycle = "ready";
      await route.fulfill({
        status: 202,
        json: {
          surfaceId: "surface-rivet",
          instanceId: "instance-rivet",
          generation: 1,
          state: "ready",
          sharing: "isolated",
          ownership: "launched",
          platform: "test",
          lifetimePolicy: "workspace",
          failure: null,
          actions: [
            { operation: "restart", label: "Restart application" },
            { operation: "stop", label: "Stop application" },
          ],
        },
      });
    },
  );
  await page.route(
    "**/api/workspace/surfaces/surface-rivet/presentations",
    async (route) => {
      const kind = (route.request().postDataJSON() as { kind?: string }).kind;
      await route.fulfill({
        status: 201,
        json: {
          presentationId: `presentation-rivet-${kind ?? "panel"}`,
          instanceId: "instance-rivet",
          generation: 1,
          kind: kind ?? "panel",
          absoluteBootstrapUrl: `http://s-rivet.localhost:8000/__wright/bootstrap#${token}`,
          expiresAt: "2026-07-30T20:00:00Z",
        },
      });
    },
  );
  await page.route(
    "**/api/workspace/surfaces/surface-rivet/presentations/*",
    (route) => route.fulfill({ status: 204 }),
  );
  await page.route("**/__wright-surface/**", (route) =>
    route.fulfill({ contentType: "text/html", body: canvasHtml }),
  );

  return { startCount: () => starts };
}

export async function mockWorkspaceShell(
  page: Page,
  surfaces: readonly Record<string, unknown>[],
): Promise<void> {
  await page.addInitScript(() => {
    window.localStorage.setItem("wright.workspaceSurfaces.testEnabled", "1");
  });
  await page.route("**/api/setup/status", (route) =>
    route.fulfill({ json: { is_configured: true, theme: "dark" } }),
  );
  for (const path of ["health", "agent/health", "inference/health"]) {
    await page.route(`**/api/${path}`, (route) =>
      route.fulfill({ json: { status: "ok" } }),
    );
  }
  await page.route("**/api/mcp/servers", (route) =>
    route.fulfill({ json: [] }),
  );
  await page.route("**/api/mcp/tools", (route) => route.fulfill({ json: [] }));
  await page.route("**/api/agent/commands", (route) =>
    route.fulfill({ json: [] }),
  );
  await page.route("**/api/workspace/by-id/ws-1/mcp-status", (route) =>
    route.fulfill({ json: { servers: [] } }),
  );
  await page.route("**/api/agent/active", (route) =>
    route.fulfill({ json: "hermes" }),
  );
  await page.route("**/api/agent/sessions*", (route) =>
    route.fulfill({
      json: { sessions: [{ session_id: "session-1", title: "Default" }] },
    }),
  );
  await page.route("**/api/workspace/by-id/ws-1/sessions*", (route) =>
    route.fulfill({
      json: { sessions: [{ session_id: "session-1", title: "Default" }] },
    }),
  );
  await page.route("**/api/workspace/by-id/ws-1", (route) =>
    route.fulfill({
      json: {
        workspace_id: "ws-1",
        session_id: "session-1",
        workspace_name: "Apps",
        local_path: "/tmp/apps",
      },
    }),
  );
  await page.route("**/api/workspace/activate", (route) =>
    route.fulfill({
      json: {
        success: true,
        session_id: "session-1",
        workspace_path: "/tmp/apps",
      },
    }),
  );
  await page.route("**/api/agent/sessions/session-1/history", (route) =>
    route.fulfill({ json: { messages: [] } }),
  );
  await page.route("**/api/workspace/files?*", (route) =>
    route.fulfill({
      json: {
        workspace: { name: "apps", path: "/", type: "directory", children: [] },
      },
    }),
  );
  await page.route("**/api/workspace/surfaces", (route) =>
    route.fulfill({ json: { items: surfaces } }),
  );
  // Runtime controls inspect each listed live instance during mount. Keep those
  // requests inside the fixture instead of accepting the dev server's HTML.
  for (const item of surfaces) {
    if (
      (item.source as { kind?: string } | undefined)?.kind !== "live_app" ||
      !item.instance
    ) {
      continue;
    }
    const surface = item as ReturnType<typeof liveSurface>;
    const instance = surface.instance!;
    await page.route(
      `**/api/workspace/surfaces/${encodeURIComponent(surface.surfaceId)}/live-app`,
      (route) =>
        route.fulfill({
          json: {
            surfaceId: surface.surfaceId,
            instanceId: instance.instanceId,
            generation: instance.generation,
            state: surface.lifecycle,
            sharing: instance.sharing,
            ownership: "launched",
            platform: "test",
            lifetimePolicy: "workspace",
            failure: null,
            actions:
              surface.lifecycle === "ready" || surface.lifecycle === "unhealthy"
                ? [
                    { operation: "restart", label: "Restart application" },
                    { operation: "stop", label: "Stop application" },
                  ]
                : [],
          },
        }),
    );
  }
  await page.route("**/api/workspace/surfaces/events", (route) =>
    route.fulfill({
      contentType: "text/event-stream",
      body: ": keepalive\n\n",
    }),
  );
  await page.route("**/presentation-preference", (route) =>
    route.fulfill({
      json: {
        kind: "panel",
        remembered: false,
        reason: "No remembered choice",
      },
    }),
  );
}

export const previewAppHtml = `<!doctype html>
<html><body>
  <button id="increment">Increment shared count</button>
  <output id="count">loading</output>
  <script>
    const output = document.querySelector('#count');
    async function refresh() {
      const response = await fetch('/shared/value');
      output.textContent = String((await response.json()).value);
    }
    document.querySelector('#increment').addEventListener('click', async () => {
      await fetch('/shared/increment', { method: 'POST' });
      await refresh();
    });
    refresh();
  </script>
</body></html>`;
