import type { Page } from "@playwright/test";

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
      ...(options.panelEligible === false ? { reason: "Application forbids framing" } : {}),
    },
    { kind: "browser", eligible: options.browserEligible ?? true },
  ],
  capabilities: [],
  revision: lifecycle === "stopped" ? 5 : 4,
  createdAt: "2026-07-30T12:00:00Z",
  updatedAt: "2026-07-30T12:04:00Z",
});

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
  await page.route("**/api/mcp/servers", (route) => route.fulfill({ json: [] }));
  await page.route("**/api/mcp/tools", (route) => route.fulfill({ json: [] }));
  await page.route("**/api/agent/commands", (route) => route.fulfill({ json: [] }));
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
  await page.route("**/api/workspace/by-id/ws-1/sessions", (route) =>
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
      json: { workspace: { name: "apps", path: "/", type: "directory", children: [] } },
    }),
  );
  await page.route("**/api/workspace/surfaces", (route) =>
    route.fulfill({ json: { items: surfaces } }),
  );
  await page.route("**/api/workspace/surfaces/events", (route) =>
    route.fulfill({ contentType: "text/event-stream", body: ": keepalive\n\n" }),
  );
  await page.route("**/presentation-preference", (route) =>
    route.fulfill({
      json: { kind: "panel", remembered: false, reason: "No remembered choice" },
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
