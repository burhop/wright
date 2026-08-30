import AxeBuilder from "@axe-core/playwright";
import { expect, test } from "@playwright/test";

import {
  liveSurface,
  mockWorkspaceShell,
  previewAppHtml,
  workspaceSurfaceOrigin,
} from "./presentation-fixture";

test.describe("workspace surface keyboard and accessibility", () => {
  test.beforeEach(async ({ page }) => {
    await page.setViewportSize({ width: 1280, height: 900 });
    await mockWorkspaceShell(page, [liveSurface()]);
    await page.route("**/api/workspace/surfaces/surface-app/presentations", (route) =>
      route.fulfill({
        status: 201,
        json: {
          presentationId: "presentation-panel",
          instanceId: "instance-shared",
          generation: 3,
          kind: "panel",
          absoluteBootstrapUrl: `${workspaceSurfaceOrigin("s-panel.localhost")}/__wright/bootstrap#abcdefghijklmnopqrstuvwxyz012345`,
          expiresAt: "2026-07-30T12:01:00Z",
        },
      }),
    );
    await page.route(`${workspaceSurfaceOrigin("s-panel.localhost")}/**`, (route) =>
      route.fulfill({ contentType: "text/html", body: previewAppHtml }),
    );
    await page.goto("/workspace/ws-1");
  });

  test("supports keyboard-only tabs, divider, F6 regions, and frame return", async ({ page }) => {
    const tab = page.getByTestId("surface-tab-surface-app");
    await tab.focus();
    await expect(tab).toBeFocused();
    await page.keyboard.press("Enter");
    await expect(tab).toHaveAttribute("aria-selected", "true");

    const separator = page.getByRole("separator", { name: "Resize chat and surface" });
    await separator.focus();
    const focusStyle = await separator.evaluate((element) =>
      getComputedStyle(element).boxShadow,
    );
    expect(focusStyle).not.toBe("none");
    await page.keyboard.press("PageUp");
    await expect(separator).toHaveAttribute("aria-valuenow", /\d+/);

    await page.getByTestId("composer-input").press("F6");
    await expect(tab).toBeFocused();

    await page.getByTestId("surface-open-panel").click();
    await expect(page.locator('iframe[title="Shareable app"]')).toBeVisible();
    await page.getByTestId("surface-enter-frame").click();
    await expect(page.locator('iframe[title="Shareable app"]')).toBeFocused();
    await page.getByTestId("surface-return-host").click();
    await expect(page.getByTestId("surface-focus")).toBeFocused();
    await expect(page.getByTestId("surface-frame-unverified")).toContainText(
      /open.*browser/i,
    );
  });

  test("has semantic host roles and zero serious or critical axe violations", async ({ page }) => {
    await expect(page.getByRole("tablist", { name: "Workspace surfaces" })).toBeVisible();
    await expect(page.getByRole("tabpanel", { name: "Shareable app" })).toBeVisible();
    await expect(page.getByRole("separator")).toHaveAttribute("aria-valuemin");
    await expect(page.getByRole("separator")).toHaveAttribute("aria-valuemax");
    await expect(page.getByRole("separator")).toHaveAttribute("aria-valuenow");

    const results = await new AxeBuilder({ page })
      .include('[data-testid="workspace-panel"]')
      .exclude("iframe")
      .analyze();
    const blocking = results.violations.filter(
      (violation) => violation.impact === "critical" || violation.impact === "serious",
    );
    expect(blocking, JSON.stringify(blocking, null, 2)).toEqual([]);
  });
});
