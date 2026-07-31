import { expect, test } from "@playwright/test";

import { liveSurface, mockWorkspaceShell } from "./presentation-fixture";

test("framing refusal remains truthful and the browser fallback stays usable", async ({
  page,
  context,
}) => {
  await mockWorkspaceShell(page, [liveSurface()]);
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
  await context.route("http://s-*.localhost:5173/**", (route) =>
    route.fulfill({
      contentType: "text/html",
      headers: {
        "X-Frame-Options": "DENY",
        "Content-Security-Policy": "frame-ancestors 'none'",
      },
      body: "<!doctype html><title>Framing denied</title><p>Open in browser works.</p>",
    }),
  );
  await page.goto("/workspace/ws-1");
  await page.getByTestId("surface-open-panel").click();
  await expect(page.getByTestId("surface-status")).toContainText(
    /embedding.*blocked/i,
  );
  const popupPromise = context.waitForEvent("page");
  await page.getByTestId("surface-open-browser").click();
  const popup = await popupPromise;
  await expect(popup.getByText("Open in browser works.")).toBeVisible();
});
