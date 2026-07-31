import { expect, test } from "@playwright/test";

import {
  liveSurface,
  mockWorkspaceShell,
  previewAppHtml,
} from "./presentation-fixture";

test.describe("panel and browser presentation choice", () => {
  test("shares state, remembers choice, and closes a view without stopping", async ({
    page,
    context,
  }) => {
    await mockWorkspaceShell(page, [liveSurface()]);
    let counter = 0;
    const createBodies: Record<string, unknown>[] = [];
    await context.route("**/shared/value", (route) =>
      route.fulfill({ json: { value: counter } }),
    );
    await context.route("**/shared/increment", (route) => {
      counter += 1;
      return route.fulfill({ json: { value: counter } });
    });
    await context.route(
      "http://s-*.localhost:5173/__wright/bootstrap",
      (route) =>
        route.fulfill({ contentType: "text/html", body: previewAppHtml }),
    );
    let presentation = 0;
    await page.route(
      "**/api/workspace/surfaces/surface-app/presentations",
      async (route) => {
        const body = route.request().postDataJSON() as Record<string, unknown>;
        createBodies.push(body);
        presentation += 1;
        const kind = String(body.kind);
        await route.fulfill({
          status: 201,
          json: {
            presentationId: `presentation-${presentation}`,
            instanceId: "instance-shared",
            generation: 3,
            kind,
            absoluteBootstrapUrl: `http://s-${kind}-${presentation}.localhost:5173/__wright/bootstrap#abcdefghijklmnopqrstuvwxyz012345`,
            expiresAt: "2026-07-30T12:01:00Z",
          },
        });
      },
    );
    await page.route(
      "**/api/workspace/surfaces/surface-app/presentations/*",
      (route) => route.fulfill({ status: 204, body: "" }),
    );

    await page.goto("/workspace/ws-1");
    await page.getByLabel("Remember this presentation choice").check();
    await page.getByTestId("surface-open-panel").click();
    const panel = page.frameLocator('iframe[title="Shareable app"]');
    await expect(panel.locator("#count")).toHaveText("0");
    await panel.locator("#increment").click();
    await expect(panel.locator("#count")).toHaveText("1");

    const popupPromise = context.waitForEvent("page");
    await page.getByTestId("surface-open-browser").click();
    const popup = await popupPromise;
    await expect(popup.locator("#count")).toHaveText("1");
    expect(createBodies).toEqual([
      expect.objectContaining({ kind: "panel", rememberPreference: true }),
      expect.objectContaining({ kind: "browser", rememberPreference: true }),
    ]);
    await expect(
      page.getByText(/preferred presentation: browser/i),
    ).toBeVisible();

    await page.getByTestId("surface-close-panel").click();
    await expect(page.locator('iframe[title="Shareable app"]')).toHaveCount(0);
    await expect(popup.locator("#count")).toHaveText("1");
    await expect(page.getByTestId("surface-stop-application")).toBeVisible();
    await expect(
      page.getByText(/closing this view keeps.*running/i),
    ).toBeVisible();
  });

  test("browser-open failure preserves an already active panel", async ({
    page,
  }) => {
    await mockWorkspaceShell(page, [liveSurface()]);
    await page.addInitScript(() => {
      window.open = () => null;
    });
    await page.route(
      "**/api/workspace/surfaces/surface-app/presentations",
      async (route) => {
        const kind = String(
          (route.request().postDataJSON() as { kind: string }).kind,
        );
        await route.fulfill({
          status: 201,
          json: {
            presentationId: `presentation-${kind}`,
            instanceId: "instance-shared",
            generation: 3,
            kind,
            absoluteBootstrapUrl: `http://s-${kind}.localhost:5173/__wright/bootstrap#abcdefghijklmnopqrstuvwxyz012345`,
            expiresAt: "2026-07-30T12:01:00Z",
          },
        });
      },
    );
    await page.route("http://s-panel.localhost:5173/**", (route) =>
      route.fulfill({ contentType: "text/html", body: previewAppHtml }),
    );
    await page.route("**/presentations/*", (route) =>
      route.fulfill({ status: 204 }),
    );
    await page.goto("/workspace/ws-1");
    await page.getByTestId("surface-open-panel").click();
    await expect(page.locator('iframe[title="Shareable app"]')).toBeVisible();
    await page.getByTestId("surface-open-browser").click();
    await expect(page.getByTestId("surface-presentation-error")).toContainText(
      /refused to open/i,
    );
    await expect(page.locator('iframe[title="Shareable app"]')).toBeVisible();
  });
});
