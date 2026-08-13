import { expect, test } from "@playwright/test";

import { liveSurface, mockWorkspaceShell } from "./presentation-fixture";

const dashboardHtml = `<!doctype html>
<html><body>
  <h1 id="dashboard-title">FastAPI operations dashboard</h1>
  <p id="nested-asset">loading nested asset</p>
  <p id="sse-status">waiting for SSE</p>
  <p id="websocket-status">waiting for WebSocket</p>
  <a id="deep-link" href="/reports/daily?view=deep">Open daily report</a>
  <script src="/assets/dashboard.js"></script>
</body></html>`;

const dashboardScript = `
fetch('/assets/data/dashboard.json')
  .then((response) => response.json())
  .then((value) => { document.querySelector('#nested-asset').textContent = value.label; });
const events = new EventSource('/events');
events.addEventListener('dashboard', (event) => {
  document.querySelector('#sse-status').textContent = event.data;
  events.close();
});
const socket = new WebSocket(new URL('/socket', window.location.href).href.replace(/^http/, 'ws'));
socket.addEventListener('message', (event) => {
  document.querySelector('#websocket-status').textContent = event.data;
  socket.close();
});
`;

const runtime = (
  state: "failed" | "ready" | "stopped",
  generation: number,
) => ({
  surfaceId: "surface-app",
  instanceId: "instance-managed",
  generation,
  state,
  sharing: "shared",
  ownership: "wright-owned",
  platform: "windows",
  lifetimePolicy: "workspace",
  failure:
    state === "failed"
      ? {
          code: "SURFACE_PROCESS_EXITED",
          message: "Dashboard process exited unexpectedly.",
          retryable: true,
        }
      : null,
  actions:
    state === "failed"
      ? [{ operation: "retry", label: "Retry application" }]
      : state === "stopped"
        ? [{ operation: "restart", label: "Start application again" }]
        : [
            { operation: "restart", label: "Restart application" },
            { operation: "stop", label: "Stop application" },
          ],
});

test.describe("managed FastAPI dashboard journey", () => {
  test("recovers a crash and supports panel, browser, transports, navigation, restart, and stop", async ({
    page,
    context,
  }) => {
    await mockWorkspaceShell(page, [liveSurface("ready")]);

    let state: "failed" | "ready" | "stopped" = "failed";
    let generation = 3;
    const operations: string[] = [];

    await page.route(
      "**/api/workspace/surfaces/surface-app/live-app",
      (route) => route.fulfill({ json: runtime(state, generation) }),
    );
    await page.route(
      "**/api/workspace/surfaces/surface-app/live-app/health",
      (route) =>
        route.fulfill({
          json: {
            instanceId: "instance-managed",
            generation,
            state,
            ok: state === "ready",
            diagnosticCode: null,
            message:
              state === "ready"
                ? "Dashboard is healthy."
                : "Dashboard is unavailable.",
            observedStatus: state === "ready" ? 200 : null,
            attempts: 1,
          },
        }),
    );
    await page.route(
      "**/api/workspace/surfaces/surface-app/live-app/logs?*",
      (route) =>
        route.fulfill({
          json: {
            entries: [
              {
                sequence: 1,
                stream: "stderr",
                message: "Dashboard process exited unexpectedly.",
                capturedAt: "2026-07-30T12:00:01Z",
                byteCount: 40,
              },
            ],
            rotated: false,
            droppedBytes: 0,
            nextSequence: 2,
          },
        }),
    );
    for (const operation of ["retry", "restart", "stop"] as const) {
      await page.route(
        `**/api/workspace/surfaces/surface-app/${operation}`,
        async (route) => {
          operations.push(operation);
          if (operation === "stop") {
            state = "stopped";
          } else {
            state = "ready";
            generation += 1;
          }
          await route.fulfill({ json: runtime(state, generation) });
        },
      );
    }

    let presentation = 0;
    await page.route(
      "**/api/workspace/surfaces/surface-app/presentations",
      async (route) => {
        presentation += 1;
        const kind = String(
          (route.request().postDataJSON() as { kind: "panel" | "browser" })
            .kind,
        );
        await route.fulfill({
          status: 201,
          json: {
            presentationId: `presentation-${presentation}`,
            instanceId: "instance-managed",
            generation,
            kind,
            absoluteBootstrapUrl: `http://s-${kind}-${presentation}.localhost:5173/__wright/bootstrap#abcdefghijklmnopqrstuvwxyz012345`,
            expiresAt: "2026-07-30T13:00:00Z",
          },
        });
      },
    );
    await page.route(
      "**/api/workspace/surfaces/surface-app/presentations/*",
      (route) => route.fulfill({ status: 204, body: "" }),
    );

    await context.route(
      /^http:\/\/s-[^.]+\.localhost:5173\/.*/,
      async (route) => {
        const url = new URL(route.request().url());
        const surfacePath = url.pathname.replace(
          /^\/__wright-surface\/[^/]+/,
          "",
        );
        if (surfacePath === "/__wright/bootstrap") {
          await route.fulfill({
            contentType: "text/html",
            body: dashboardHtml,
          });
        } else if (surfacePath === "/assets/dashboard.js") {
          await route.fulfill({
            contentType: "application/javascript",
            body: dashboardScript,
          });
        } else if (surfacePath === "/assets/data/dashboard.json") {
          await route.fulfill({ json: { label: "nested asset loaded" } });
        } else if (surfacePath === "/events") {
          await route.fulfill({
            headers: {
              "Cache-Control": "no-cache",
              "Content-Type": "text/event-stream",
            },
            body: "event: dashboard\ndata: SSE connected\n\n",
          });
        } else if (surfacePath === "/reports/daily") {
          await route.fulfill({
            contentType: "text/html",
            body: '<h1 id="deep-report">Daily report deep link</h1><a id="redirect-link" href="/go/latest">Follow redirect</a>',
          });
        } else if (surfacePath === "/go/latest") {
          await route.fulfill({
            contentType: "text/html",
            body: '<!doctype html><meta http-equiv="refresh" content="0;url=/reports/latest">',
          });
        } else if (surfacePath === "/reports/latest") {
          await route.fulfill({
            contentType: "text/html",
            body: '<h1 id="redirect-report">Latest report after redirect</h1>',
          });
        } else {
          await route.fulfill({ status: 404, body: "not found" });
        }
      },
    );
    await page.routeWebSocket(
      /^ws:\/\/s-[^.]+\.localhost:5173\/socket$/,
      (socket) => {
        socket.send("WebSocket connected");
      },
    );

    await page.goto("/workspace/ws-1");
    const controls = page.getByTestId("live-app-controls");
    await expect(controls.getByRole("status")).toContainText("failed");
    await expect(controls.getByRole("status")).toContainText(
      "exited unexpectedly",
    );
    await controls
      .getByRole("button", { name: "View application logs" })
      .click();
    await expect(controls.getByRole("log")).toContainText(
      "exited unexpectedly",
    );

    await controls.getByRole("button", { name: "Retry application" }).click();
    await expect(controls.getByRole("status")).toContainText("ready");
    await controls
      .getByRole("button", { name: "Check application health" })
      .click();
    await expect(controls.getByRole("note")).toContainText("healthy");
    await controls.getByRole("button", { name: "Restart application" }).click();
    await expect(controls.getByRole("status")).toContainText("ready");

    await page.getByTestId("surface-open-panel").click();
    const panel = page.frameLocator('iframe[title="Shareable app"]');
    await expect(panel.locator("#dashboard-title")).toHaveText(
      "FastAPI operations dashboard",
    );
    await expect(panel.locator("#nested-asset")).toHaveText(
      "nested asset loaded",
    );
    await expect(panel.locator("#sse-status")).toHaveText("SSE connected");
    await expect(panel.locator("#websocket-status")).toHaveText(
      "WebSocket connected",
    );
    await panel.locator("#deep-link").click();
    await expect(panel.locator("#deep-report")).toHaveText(
      "Daily report deep link",
    );
    await panel.locator("#redirect-link").click();
    await expect
      .poll(() =>
        page
          .frames()
          .map((frame) => frame.url())
          .join("\n"),
      )
      .toContain("/reports/latest");

    const popupPromise = context.waitForEvent("page");
    await page.getByTestId("surface-open-browser").click();
    const popup = await popupPromise;
    await expect(popup.locator("#dashboard-title")).toHaveText(
      "FastAPI operations dashboard",
    );

    await page.getByTestId("surface-stop-application").click();
    await expect(controls.getByRole("status")).toContainText("stopped");
    await expect(page.locator('iframe[title="Shareable app"]')).toHaveCount(0);
    expect(operations).toEqual(["retry", "restart", "stop"]);
  });
});
