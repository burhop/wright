import { expect, test } from "@playwright/test";

const surface = (revision: number) => ({
  schemaVersion: 1,
  surfaceId: "surface-loads",
  workspaceId: "ws-1",
  source: {
    kind: "display",
    sourceId: "execution-1:loads",
    sourceVersion: String(revision),
    displayId: "loads",
    revision,
  },
  title: "Measured load",
  lifecycle: "ready",
  presentations: [],
  capabilities: [],
  revision,
  createdAt: "2026-07-30T12:00:00Z",
  updatedAt: `2026-07-30T12:0${revision}:00Z`,
});

const projection = (revision: number, value: number) => ({
  artifactId: `artifact-${revision}`,
  surfaceId: "surface-loads",
  displayId: "loads",
  revision,
  title: "Measured load",
  accessibilityDescription: `Load reaches ${value} N.`,
  durability: "durable",
  representations: [
    {
      mediaType: "application/vnd.plotly.v1+json",
      encoding: "json",
      data: { data: [{ x: [0, 1], y: [10, value] }] },
      fallbackRank: 0,
    },
    {
      mediaType: "application/vnd.wright.table+json",
      encoding: "json",
      data: {
        columns: ["Time", "Load"],
        data: [
          [0, 10],
          [1, value],
        ],
      },
      fallbackRank: 10,
    },
  ],
});

test.describe("Python display journey", () => {
  test.beforeEach(async ({ page }) => {
    await page.addInitScript(() => {
      window.localStorage.setItem("wright.workspaceSurfaces.testEnabled", "1");
    });
    await page.route("**/api/setup/status", (route) =>
      route.fulfill({ json: { is_configured: true, theme: "dark" } }),
    );
    await page.route("**/api/health", (route) =>
      route.fulfill({ json: { status: "ok" } }),
    );
    await page.route("**/api/agent/health", (route) =>
      route.fulfill({ json: { status: "ok" } }),
    );
    await page.route("**/api/inference/health", (route) =>
      route.fulfill({ json: { status: "ok" } }),
    );
    await page.route("**/api/mcp/servers", (route) =>
      route.fulfill({ json: [] }),
    );
    await page.route("**/api/mcp/tools", (route) =>
      route.fulfill({ json: [] }),
    );
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
          workspace_name: "Graphs",
          local_path: "/tmp/graphs",
        },
      }),
    );
    await page.route("**/api/workspace/activate", (route) =>
      route.fulfill({
        json: {
          success: true,
          session_id: "session-1",
          workspace_path: "/tmp/graphs",
        },
      }),
    );
    await page.route("**/api/agent/sessions/session-1/history", (route) =>
      route.fulfill({ json: { messages: [] } }),
    );
    await page.route("**/api/workspace/files?*", (route) =>
      route.fulfill({
        json: {
          workspace: {
            name: "graphs",
            path: "/",
            type: "directory",
            children: [],
          },
        },
      }),
    );
    await page.route("**/api/workspace/surfaces", (route) =>
      route.fulfill({ json: { items: [surface(1)] } }),
    );
    await page.route("**/api/workspace/surfaces/events", (route) =>
      route.fulfill({
        contentType: "text/event-stream",
        body: ": keepalive\n\n",
      }),
    );
    await page.route(
      "**/api/workspace/surfaces/surface-loads/display*",
      async (route) => {
        if (route.request().method() === "DELETE") {
          await route.fulfill({
            json: {
              deleted: true,
              recoverable: false,
              retentionStatus: "payload_cleanup_scheduled",
            },
          });
          return;
        }
        const revision = new URL(route.request().url()).searchParams.get(
          "surfaceRevision",
        );
        await route.fulfill({
          json: revision === "2" ? projection(2, 18) : projection(1, 15),
        });
      },
    );
    await page.route(
      "**/api/workspace/surfaces/surface-loads/history",
      (route) =>
        route.fulfill({
          json: {
            items: [
              {
                artifactId: "artifact-1",
                revision: 1,
                current: false,
                createdAt: "2026-07-30T12:00:00Z",
              },
              {
                artifactId: "artifact-2",
                revision: 2,
                current: true,
                createdAt: "2026-07-30T12:01:00Z",
              },
            ],
          },
        }),
    );
    await page.route(
      "**/api/workspace/surfaces/surface-loads/verification",
      (route) =>
        route.fulfill({
          json: {
            mode: "agent_generated",
            prompt: "Graph the measured load.",
            no_prompt: false,
            effective_constraints: { offline: true },
            script: "import wright\nwright.line(...)\n",
            script_revision: 2,
            task_id: "file-run-graph",
            execution_id: "execution-2",
            trace_id: "aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa",
          },
        }),
    );
  });

  test("shows, updates, preserves history, and discloses destructive retention", async ({
    page,
  }) => {
    let releaseEvent: () => void = () => undefined;
    const released = new Promise<void>((resolve) => {
      releaseEvent = resolve;
    });
    await page.route("**/api/workspace/surfaces/events", async (route) => {
      await released;
      await route.fulfill({
        contentType: "text/event-stream",
        body: [
          "id: display-event-2",
          "event: surface.display.updated",
          `data: ${JSON.stringify(surface(2))}`,
          "",
          "",
        ].join("\n"),
      });
    });
    await page.goto("/workspace/ws-1");
    await expect(page.getByTestId("surface-tab-surface-loads")).toHaveText(
      "Measured load",
    );
    await expect(
      page.getByRole("img", { name: "Load reaches 15 N." }),
    ).toBeVisible();

    releaseEvent();
    await expect(
      page.getByRole("img", { name: "Load reaches 18 N." }),
    ).toBeVisible();
    await expect(page.getByTestId("surface-tab-surface-loads")).toHaveCount(1);

    await page.getByTestId("surface-history").click();
    const history = page.getByRole("dialog", {
      name: "Display revision history",
    });
    await expect(history.getByText("Revision 1")).toBeVisible();
    await expect(history.getByText("Revision 2 (current)")).toBeVisible();
    await page.getByRole("button", { name: "Close history" }).click();
    await page.getByTestId("surface-verification").click();
    const verification = page.getByRole("dialog", {
      name: "Artifact verification",
    });
    await expect(verification).toContainText("Graph the measured load.");
    await expect(verification).toContainText('"offline": true');
    await expect(verification).toContainText("wright.line(...)");
    await expect(verification).toContainText("Script revision 2");
    await verification
      .getByRole("button", { name: "Close verification" })
      .click();
    await page.getByTestId("surface-delete-output").click();
    await expect(page.getByRole("dialog")).toContainText(
      /cannot be recovered/i,
    );
    await page.getByRole("button", { name: "Delete output" }).click();
    await expect(page.getByText(/payload cleanup scheduled/i)).toBeVisible();
  });

  test("shows a stable actionable renderer error", async ({ page }) => {
    await page.route("**/api/workspace/surfaces", (route) =>
      route.fulfill({
        json: {
          items: [
            {
              ...surface(1),
            },
          ],
        },
      }),
    );
    await page.route(
      "**/api/workspace/surfaces/surface-loads/display*",
      (route) =>
        route.fulfill({
          json: {
            ...projection(1, 15),
            accessibilityDescription: "Invalid graph",
            representations: [],
          },
        }),
    );
    await page.goto("/workspace/ws-1");
    await expect(page.getByTestId("surface-display-error")).toContainText(
      /display.*unavailable/i,
    );
    await expect(page.getByTestId("surface-diagnostics")).toBeVisible();
  });

  test(
    "live installed-wheel display path",
    { tag: "@live" },
    async ({ page }) => {
      await page.goto("/workspace/ws-1");
      await expect(page.getByTestId("surface-deck")).toBeVisible();
    },
  );
});
