import { expect, test } from "@playwright/test";

import {
  mockRecoveryWorkspace,
  openNewRecoveryEditor,
} from "./fixtures/workflow-recovery";

test("opens the supported workflow composer from the workspace Workflows control", async ({
  page,
}) => {
  await mockRecoveryWorkspace(page);
  await openNewRecoveryEditor(page);
  await expect(page.getByTestId("workflow-recovery-canvas")).toBeVisible();
  await expect(page.getByTestId("workflow-recovery-save")).toBeVisible();
});
