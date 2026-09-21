import { mkdirSync } from "node:fs";

import { expect, test } from "@playwright/test";

import {
  mockRecoveryWorkspace,
  openRecoveryEditor,
} from "./fixtures/workflow-recovery";

test("retains a review screenshot of the workflow canvas", async ({ page }) => {
  await mockRecoveryWorkspace(page);
  await openRecoveryEditor(page);
  const canvas = page.getByTestId("workflow-recovery-canvas");
  const before = await canvas.boundingBox();
  await page.getByTestId("workflow-recovery-run-readiness-toggle").click();
  const after = await canvas.boundingBox();
  expect(after?.height).toBe(before?.height);
  expect(after?.y).toBe(before?.y);
  mkdirSync("artifacts/qa/workflow-recovery-20260918", { recursive: true });
  await page.screenshot({
    path: "artifacts/qa/workflow-recovery-20260918/canvas-readiness.png",
    fullPage: true,
  });
});

test("keeps expanded readiness contained on mobile without shrinking the canvas", async ({
  page,
}) => {
  await mockRecoveryWorkspace(page);
  await openRecoveryEditor(page);
  await page.setViewportSize({ width: 390, height: 844 });
  await page.reload();
  await page.getByTestId("workspace-pane-surface").click();
  await expect(page.getByTestId("workflow-recovery-concept")).toBeVisible();
  const run = await page
    .getByTestId("workflow-recovery-run-start")
    .boundingBox();
  expect(run!.x).toBeGreaterThanOrEqual(0);
  expect(run!.x + run!.width).toBeLessThanOrEqual(390);
  const canvas = page.getByTestId("workflow-recovery-canvas");
  const before = await canvas.boundingBox();
  await page.getByTestId("workflow-recovery-run-readiness-toggle").click();
  const panel = page.locator(".recovery-run-readiness__body");
  await expect(panel).toBeVisible();
  const box = await panel.boundingBox();
  expect(box!.x).toBeGreaterThanOrEqual(0);
  expect(box!.x + box!.width).toBeLessThanOrEqual(390);
  expect((await canvas.boundingBox())?.height).toBe(before?.height);
  expect(
    await panel.evaluate(
      (element) => element.scrollWidth <= element.clientWidth,
    ),
  ).toBe(true);
  await page.screenshot({
    path: "test-results/pr133-readiness-mobile.png",
    fullPage: true,
  });
});
