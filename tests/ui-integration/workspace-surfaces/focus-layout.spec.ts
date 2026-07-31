import { expect, test } from "@playwright/test";

import { liveSurface, mockWorkspaceShell } from "./presentation-fixture";

test.describe("workspace surface adaptive layout", () => {
  test("keeps chat live through focus, resize, tab switch, and restoration", async ({ page }) => {
    await page.setViewportSize({ width: 1280, height: 900 });
    await mockWorkspaceShell(page, [
      liveSurface(),
      liveSurface("ready", { surfaceId: "surface-secondary" }),
    ]);
    await page.goto("/workspace/ws-1");

    const workspace = page.getByTestId("workspace-panel");
    await expect(workspace).toHaveAttribute("data-layout-mode", "normal");
    await page.locator('[data-testid="surface-enter-focus"]:visible').click();
    await expect(workspace).toHaveAttribute("data-layout-mode", "focus");
    await expect(page.getByTestId("composer-input")).toBeVisible();
    await expect(page.getByTestId("workspace-sidebar")).toBeHidden();

    const separator = page.getByRole("separator", { name: "Resize chat and surface" });
    const before = Number(await separator.getAttribute("aria-valuenow"));
    await separator.focus();
    await page.keyboard.press("ArrowRight");
    await expect(separator).toHaveAttribute("aria-valuenow", String(before + 2));

    await page.getByTestId("surface-tab-surface-secondary").click();
    await expect(page.locator("#surface-panel-surface-secondary")).toBeVisible();
    await page.getByTestId("surface-tab-surface-app").click();
    await expect(page.getByRole("tabpanel", { name: "Shareable app" })).toBeVisible();

    await page.getByTestId("surface-exit-focus").click();
    await expect(workspace).toHaveAttribute("data-layout-mode", "normal");
    await expect(page.getByTestId("workspace-sidebar")).toBeVisible();
  });

  test("uses an explicit reversible Chat and Surface switcher when narrow", async ({ page }) => {
    await page.setViewportSize({ width: 700, height: 900 });
    await mockWorkspaceShell(page, [liveSurface()]);
    await page.goto("/workspace/ws-1");

    const workspace = page.getByTestId("workspace-panel");
    await expect(workspace).toHaveAttribute("data-layout-mode", "narrow");
    await expect(page.getByRole("navigation", { name: "Workspace pane" })).toBeVisible();
    await expect(page.getByTestId("composer-input")).toBeVisible();

    await page.getByTestId("workspace-pane-surface").click();
    await expect(page.getByTestId("workspace-surface-pane")).toBeVisible();
    await expect(page.getByTestId("surface-deck")).toBeVisible();

    await page.getByTestId("workspace-pane-chat").click();
    await expect(page.getByTestId("composer-input")).toBeVisible();

    await page.setViewportSize({ width: 1280, height: 900 });
    await expect(workspace).toHaveAttribute("data-layout-mode", "normal");
    await expect(page.getByRole("separator", { name: "Resize chat and surface" })).toBeVisible();
  });
});
