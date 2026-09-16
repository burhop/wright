import { expect, test } from "@playwright/test";

import { mockRecoveryWorkspace } from "./fixtures/workflow-recovery";

test("opens the supported workflow composer from the workspace Workflows control", async ({
  page,
}) => {
  await mockRecoveryWorkspace(page);
  await page.goto("/workspace/ws-recovery");
  await page.getByTestId("activity-bar-workflows-btn").click();

  await expect(page).toHaveURL(/\/workspace\/ws-recovery\?workflow=canonical$/);
  await expect(page.getByTestId("workflow-recovery-canvas")).toBeVisible();
  await expect(page.getByTestId("workflow-recovery-save")).toBeVisible();
});
