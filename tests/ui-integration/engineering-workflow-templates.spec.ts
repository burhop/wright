import { expect, test } from "@playwright/test";

import { mockRecoveryWorkspace } from "./fixtures/workflow-recovery";

async function openTemplateEditor(
  page: import("@playwright/test").Page,
): Promise<void> {
  await page.goto("/workspace/ws-recovery");
  await page.getByTestId("activity-bar-workflows-btn").click();
  await expect(page).toHaveURL(/\/workspace\/ws-recovery\?workflow=canonical$/);
  await expect(page.getByTestId("workflow-recovery-canvas")).toBeVisible();
  const collapseAgent = page.getByTitle("Collapse Agent Console");
  if (await collapseAgent.isVisible()) await collapseAgent.click();
}

test("opens ten engineering templates from the workspace Workflows control", async ({
  page,
}) => {
  await mockRecoveryWorkspace(page);
  await openTemplateEditor(page);

  await page.getByTestId("workflow-file-menu").click();
  await expect(page.getByTestId("workflow-file-new")).toBeVisible();
  await expect(page.getByTestId("workflow-file-open")).toBeVisible();
  await page.getByTestId("workflow-start-template").click();

  await expect(
    page.getByTestId("workflow-template-list").getByRole("option"),
  ).toHaveCount(10);
  await expect(page.getByTestId("workflow-template-details")).toContainText(
    "3D Printed Replacement Part",
  );
  await expect(page.getByTestId("workflow-template-readiness")).toContainText(
    "Setup required",
  );
  await expect(
    page.getByTestId("workflow-template-details").getByRole("img"),
  ).toBeVisible();

  await page.getByTestId("workflow-template-cancel").click();
  await expect(page.getByTestId("workflow-recovery-canvas")).toBeVisible();
  await expect(page.getByTestId("workflow-recovery-save")).toBeVisible();
  await expect(page.getByTestId("workflow-template-list")).toBeHidden();
  await expect(page.getByTestId("workflow-file-menu")).toBeFocused();
});

test("creates a fresh template copy and opens it in the established editor", async ({
  page,
}) => {
  await mockRecoveryWorkspace(page);
  await openTemplateEditor(page);

  await page.getByTestId("workflow-file-menu").click();
  await page.getByTestId("workflow-start-template").click();
  await expect(
    page.getByTestId("workflow-template-list").getByRole("option"),
  ).toHaveCount(10);
  await page
    .getByTestId("workflow-template-name")
    .fill("Replacement Knob Demo");
  await page.getByTestId("workflow-template-create").click();

  await expect(page).toHaveURL(
    /workflowPath=workflows%2Freplacement-knob-demo\.workflow\.wflow/,
  );
  const createdEditor = page.getByRole("region", {
    name: /workflow workflows\/replacement-knob-demo\.workflow\.wflow/,
  });
  await expect(createdEditor).toBeVisible();
  await expect(
    createdEditor.getByTestId("workflow-recovery-filebar"),
  ).toContainText("Mounting bracket development");
  await expect(
    createdEditor.getByTestId("workflow-recovery-canvas"),
  ).toBeVisible();
  await expect(
    createdEditor.getByTestId("workflow-recovery-save"),
  ).toBeVisible();
  await expect(
    createdEditor.getByTestId("workflow-recovery-view-code"),
  ).toBeVisible();
});
