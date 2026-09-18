import { mkdirSync } from "node:fs";

import { test } from "@playwright/test";

import {
  mockRecoveryWorkspace,
  openRecoveryEditor,
} from "./fixtures/workflow-recovery";

test("retains a review screenshot of the workflow canvas", async ({ page }) => {
  await mockRecoveryWorkspace(page);
  await openRecoveryEditor(page);
  await page.getByTestId("workflow-recovery-run-readiness-toggle").click();
  mkdirSync("artifacts/qa/workflow-recovery-20260918", { recursive: true });
  await page.screenshot({
    path: "artifacts/qa/workflow-recovery-20260918/canvas-readiness.png",
    fullPage: true,
  });
});
