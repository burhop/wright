import { expect, test } from "@playwright/test";

import { liveSurface, mockWorkspaceShell } from "./presentation-fixture";

test("reload accepts only reconciled instance truth and never auto-restarts", async ({
  page,
}) => {
  const stale = liveSurface("ready", {
    instanceId: "stale-instance",
    generation: 1,
  });
  const stopped = liveSurface("stopped");
  await mockWorkspaceShell(page, [stopped]);
  let presentationCreates = 0;
  await page.route(
    "**/api/workspace/surfaces/surface-app/presentations",
    (route) => {
      presentationCreates += 1;
      return route.fulfill({ status: 500, json: {} });
    },
  );
  await page.addInitScript(
    (serialized) => {
      window.localStorage.setItem(
        "wright.workspaceSurfaces.state.ws-1.session-1",
        serialized,
      );
    },
    JSON.stringify({
      version: 2,
      descriptors: [stale],
      tabs: ["surface-app"],
      activeSurfaceId: "surface-app",
      layout: { mode: "normal", chatSize: { unit: "ratio", value: 0.4 } },
    }),
  );

  await page.goto("/workspace/ws-1");
  await expect(page.getByTestId("surface-status")).toContainText(/stopped/i);
  await expect(page.getByTestId("surface-restart-application")).toHaveCount(0);
  expect(presentationCreates).toBe(0);
  await page.reload();
  await expect(page.getByTestId("surface-status")).toContainText(/stopped/i);
  expect(presentationCreates).toBe(0);
});

test("a reconciliation outage never exposes persisted ready authority", async ({
  page,
}) => {
  const stale = liveSurface("ready", {
    instanceId: "persisted-instance",
    generation: 1,
  });
  await mockWorkspaceShell(page, []);
  await page.route("**/api/workspace/surfaces", (route) =>
    route.fulfill({ status: 503, json: { error: "offline" } }),
  );
  await page.addInitScript(
    (serialized) => {
      window.localStorage.setItem(
        "wright.workspaceSurfaces.state.ws-1.session-1",
        serialized,
      );
    },
    JSON.stringify({
      version: 2,
      descriptors: [stale],
      tabs: ["surface-app"],
      activeSurfaceId: "surface-app",
      layout: { mode: "normal", chatSize: { unit: "ratio", value: 0.4 } },
    }),
  );

  await page.goto("/workspace/ws-1");
  await expect(page.getByTestId("surface-restore-status")).toContainText(
    /unable to reconcile/i,
  );
  await expect(page.getByTestId("surface-open-panel")).toHaveCount(0);
});
