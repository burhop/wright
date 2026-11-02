import { expect, test } from "@playwright/test";
import { mockRecoveryWorkspace } from "./fixtures/workflow-recovery";
import { commonViewSource } from "./fixtures/process-common-view";

test("a saved starter revision reaches backend preflight while retaining template lineage", async ({
  page,
}, testInfo) => {
  const workspace = await mockRecoveryWorkspace(page, {
    source: commonViewSource,
  });
  const initialDigest = workspace.current()!.storage_digest;
  let preflightRequests = 0;
  await page.route(
    "**/api/workspace/workflow-sources/readiness?*",
    async (route) => {
      const current = workspace.current()!;
      const revised = current.storage_digest !== initialDigest;
      return route.fulfill({
        json: {
          state: revised ? "revised" : "setup_required",
          template_id: "replacement-drawer-handle",
          template_version: "1.0.0",
          source_digest: "c".repeat(64),
          layout_digest: "d".repeat(64),
          accepted_source_digest: current.storage_digest,
          definition_revision: current.definition_revision,
          definition_valid: revised ? null : true,
          configured: revised ? null : false,
          qualified: revised ? null : false,
          available: revised ? null : false,
          verified_run: revised ? null : false,
          facts: [],
          blocking_reasons: revised
            ? []
            : ["Qualify the supplied starter's tools."],
          message: revised
            ? "Check this accepted revision's current inputs, tools, model and authority in the working view before starting."
            : null,
        },
      });
    },
  );
  await page.route("**/api/workspace/workflow-sources/run", async (route) => {
    preflightRequests += 1;
    expect(route.request().postDataJSON().expected_storage_digest).toBe(
      workspace.current()!.storage_digest,
    );
    return route.fulfill({
      status: 409,
      json: {
        error_code: "workflow_not_ready",
        message: "Current tool qualification is missing.",
        details: { correction: "Check inputs and tools in the working view." },
      },
    });
  });
  await page.goto("/workspace/ws-recovery");
  const files = page.getByTestId("activity-bar-explorer-btn");
  await expect(files).toBeVisible();
  if ((await files.getAttribute("aria-expanded")) !== "true")
    await files.click();
  const navigation = page.getByRole("region", { name: "Workspace navigation" });
  const savedFile = navigation.getByText("mounting-bracket.workflow.wflow", {
    exact: true,
  });
  if (!(await savedFile.isVisible()))
    await navigation.getByText("bracket-development", { exact: true }).click();
  await savedFile.click();
  await page.getByTestId("workflow-recovery-run-readiness-toggle").click();
  await expect(page.getByText("Setup required", { exact: true })).toBeVisible();
  await page.getByTestId("workflow-recovery-run-start").click();
  await expect(page.getByTestId("workflow-native-run-summary")).toContainText(
    "Run blocked before prompt dispatch",
  );
  expect(preflightRequests).toBe(0);

  await page
    .getByRole("textbox", { name: "Workflow name", exact: true })
    .fill("Revised example with current setup");
  await page
    .getByRole("textbox", { name: "Workflow name", exact: true })
    .press("Enter");
  await page.getByTestId("workflow-recovery-save").click();
  await expect.poll(() => workspace.updateCount()).toBe(1);
  await expect(
    page.getByText("Revised · preflight required", { exact: true }),
  ).toBeVisible();
  const issue = page.getByTestId("workflow-recovery-template-readiness-issue");
  await expect(issue).toContainText("replacement-drawer-handle");
  await expect(issue).toContainText(
    "current inputs, tools, model and authority",
  );
  expect(workspace.current()!.storage_digest).not.toBe(initialDigest);
  await issue.scrollIntoViewIfNeeded();
  await page.screenshot({
    path: testInfo.outputPath("revised-template-preflight.png"),
    fullPage: true,
  });
  await page.getByTestId("workflow-recovery-run-start").click();
  await expect.poll(() => preflightRequests).toBe(1);
  await expect(page.getByTestId("workflow-native-run-summary")).toContainText(
    "Current tool qualification is missing",
  );
  expect(workspace.runCount()).toBe(0);
  await testInfo.attach("scope.json", {
    contentType: "application/json",
    body: JSON.stringify({
      served_frontend: true,
      controlled_http_contracts: true,
      live_backend: false,
      live_engineering_tools: false,
      accepted_source_digest: workspace.current()!.storage_digest,
      preflight_requests: preflightRequests,
      runs: workspace.runCount(),
    }),
  });
});
