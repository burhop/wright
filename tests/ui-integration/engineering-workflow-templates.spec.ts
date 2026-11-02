import { expect, test } from "@playwright/test";

import {
  mockRecoveryWorkspace,
  openNewRecoveryEditor,
} from "./fixtures/workflow-recovery";

async function openTemplateEditor(
  page: import("@playwright/test").Page,
): Promise<void> {
  await openNewRecoveryEditor(page);
}

test("explores a supplied starter from Workflows without starting or replacing a process", async ({
  page,
}, testInfo) => {
  const workspace = await mockRecoveryWorkspace(page);
  const starter = {
    template_id: "replacement-drawer-handle",
    version: "1.0.0",
    title: "Replace a drawer handle",
    summary:
      "Prepare an inspectable print package from a measured handle design.",
    discipline: "Mechanical repair",
    preview: {
      asset: "previews/handle.svg",
      alt: "Supplied drawer handle sketch",
    },
    provided_inputs: [
      { name: "Original fictional sketch with 96 mm bolt spacing" },
    ],
    requested_inputs: [{ name: "Review the supplied measurements" }],
    expected_outputs: [{ name: "Measured mesh and 3MF print package" }],
    external_effects: [],
    source_digest: "d".repeat(64),
    readiness: {
      state: "setup_required",
      definition_valid: true,
      configured: false,
      qualified: false,
      available: false,
      verified_run: false,
      facts: [],
      blocking_reasons: ["Qualify geometry and slicing tools before running."],
    },
    exploration: {
      preview_kind: "supplied_sketch",
      preview_caption:
        "Original fictional sample; no physical repair is claimed.",
      outcome_status: "pending",
      outcome_summary:
        "A recorded measured handle outcome is not yet available.",
      stages: [
        {
          title: "Prepare the print package",
          tool: "Independent slicer",
          contribution: "Compare orientations and support contacts.",
          input: "Measured handle mesh",
          output: "3MF package and support preview",
        },
      ],
      limitations: ["Physical fit and strength remain unverified."],
    },
  };
  await page.route("**/api/workspace/workflow-source-templates", (route) =>
    route.fulfill({ json: { catalog_version: "1.0.0", templates: [starter] } }),
  );
  await page.route(
    "**/api/workspace/workflow-source-templates/replacement-drawer-handle?*",
    (route) =>
      route.fulfill({
        json: {
          template: {
            ...starter,
            capability_requirements: [
              {
                title: "Handle slicing",
                operation: "slice_with_supports",
                qualification: "required",
              },
            ],
          },
        },
      }),
  );
  await openTemplateEditor(page);
  const originalSource = workspace.current()?.source;
  const originalCreates = workspace.createCount();
  const writes: string[] = [];
  page.on("request", (request) => {
    if (request.method() !== "GET" && request.url().includes("/api/"))
      writes.push(`${request.method()} ${new URL(request.url()).pathname}`);
  });

  await page.getByTestId("workflow-explore-example").click();
  await expect(
    page.getByText("Supplied sketch", { exact: true }),
  ).toBeVisible();
  await expect(page.getByTestId("workflow-template-outcome")).toContainText(
    "Recorded outcome pending",
  );
  await expect(page.getByTestId("workflow-template-create")).toBeInViewport();
  await page.screenshot({
    path: testInfo.outputPath("starter-exploration.png"),
  });
  await page.getByTestId("workflow-template-setup").click();
  await expect(page.getByText("Handle slicing", { exact: true })).toBeVisible();
  await expect(
    page.getByRole("region", { name: "Setup requirements" }),
  ).toContainText("Prepare and check inputs");
  await expect(
    page.getByRole("heading", { name: "Start from an engineering workflow" }),
  ).toBeInViewport();
  await expect(page.getByTestId("workflow-template-create")).toBeInViewport();
  const setupScreenshot = testInfo.outputPath("starter-setup.png");
  await page.screenshot({ path: setupScreenshot });
  await testInfo.attach("starter-exploration", {
    path: setupScreenshot,
    contentType: "image/png",
  });
  await page.getByTestId("workflow-template-cancel").click();

  await expect(page.getByTestId("workflow-recovery-canvas")).toBeVisible();
  await expect(page.getByTestId("workflow-explore-example")).toBeFocused();
  expect(workspace.current()?.source).toBe(originalSource);
  expect(workspace.createCount()).toBe(originalCreates);
  expect(workspace.runCount()).toBe(0);
  expect(writes).toEqual([]);
});

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
  ).toContainText("Bracket development");
  await expect(
    createdEditor.getByTestId("workflow-recovery-canvas"),
  ).toBeVisible();
  await expect(
    createdEditor.getByTestId("workflow-recovery-save"),
  ).toBeVisible();
  await expect(
    createdEditor.getByTestId("workflow-recovery-template-readiness-issue"),
  ).toContainText("Setup required");
  await expect(
    createdEditor.getByTestId("workflow-recovery-view-code"),
  ).toBeVisible();
});
