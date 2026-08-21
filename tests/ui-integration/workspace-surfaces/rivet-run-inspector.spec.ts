import { expect, test } from "@playwright/test";

import { mockRivetRunInspector } from "./fixtures/rivet-run-inspector";

test.describe("Rivet Run Inspector", () => {
  test("runs immediately, shows complete safe outputs, focuses a step, and reattaches after refresh", async ({ page }) => {
    const browserErrors: string[] = [];
    page.on("console", (message) => { if (message.type() === "error") browserErrors.push(message.text()); });
    page.on("pageerror", (error) => browserErrors.push(error.message));
    const state = await mockRivetRunInspector(page);
    await page.goto("/workspace/ws-1");
    await page.getByTestId("activity-bar-workflows-btn").click();
    await expect(page.getByTestId("direct-rivet-run")).toBeVisible();
    await page.getByTestId("direct-rivet-run").click();
    await expect(page.getByTestId("direct-rivet-run-panel")).toHaveCount(0);
    await expect(page.getByTestId("rivet-run-state-succeeded")).toBeVisible();
    await expect(page.getByTestId("rivet-run-result-output")).toContainText("complete");
    await expect(page.getByTestId("rivet-run-result-output")).toContainText("Redacted");
    expect(state.startCount()).toBe(1);

    await page.getByRole("button", { name: "Steps", exact: true }).click();
    await page.getByRole("button", { name: /Inspect CAD/ }).click();
    const frame = page.frameLocator('iframe[title="Rivet graph canvas"]');
    await expect(frame.getByTestId("focused-node")).toHaveText("node-1");
    await expect(frame.getByTestId("node-1")).toHaveAttribute("data-run-state", "succeeded");

    await page.getByRole("button", { name: /Run Inspector/ }).click();
    await expect(page.getByTestId("rivet-run-inspector")).toHaveClass(/is-collapsed/);
    await page.reload();
    await page.getByTestId("activity-bar-workflows-btn").click();
    await expect(page.getByTestId("rivet-run-state-succeeded")).toBeVisible();
    expect(state.startCount()).toBe(1);
    expect(browserErrors.join("\n")).not.toMatch(/oauth\/callback|authorization: bearer|access_token|trace-safe/i);
    await expect(page.locator("body")).not.toContainText(/oauth\/callback|authorization: bearer|access_token/i);
  });

  test("auto-opens a failed run with residue truth and safe full-rerun only", async ({ page }) => {
    const state = await mockRivetRunInspector(page, "failed");
    await page.goto("/workspace/ws-1");
    await page.getByTestId("activity-bar-workflows-btn").click();
    await page.getByTestId("direct-rivet-run").click();
    await expect(page.getByTestId("rivet-run-state-failed")).toBeVisible();
    await expect(page.getByText(/connection ended/i)).toBeVisible();
    await expect(page.getByText(/partial change/i)).toBeVisible();
    await expect(page.getByRole("button", { name: /retry step/i })).toHaveCount(0);
    await expect(page.getByRole("button", { name: /run saved revision again/i })).toBeVisible();
    expect(state.startCount()).toBe(1);
  });

  test("keeps controls accessible in narrow and maximized workspace layouts", async ({ page }) => {
    await mockRivetRunInspector(page);
    await page.goto("/workspace/ws-1");
    await page.getByTestId("activity-bar-workflows-btn").click();
    await page.setViewportSize({ width: 760, height: 720 });
    await page.getByTestId("workspace-pane-surface").click();
    await expect(page.getByTestId("direct-rivet-run")).toHaveAccessibleName("Run Rivet workflow");
    await expect(page.getByTestId("direct-rivet-run-options")).toHaveAccessibleName("Run Rivet workflow with options");
    await expect(page.getByTestId("direct-rivet-focus-workflow")).toHaveAccessibleName(/Focus workflow canvas/i);
    await page.getByTestId("direct-rivet-focus-workflow").focus();
    await page.keyboard.press("Enter");
    await expect(page.getByTestId("direct-rivet-status")).toContainText("Workflow canvas focused");
  });
});
