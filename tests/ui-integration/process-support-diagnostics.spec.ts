import { expect, test } from "@playwright/test";
import type { SupportDiagnosticPreview } from "../../apps/web/src/services/workspace-service";
import {
  fixtureRunId,
  mockCommonProcessWorkspace,
} from "./fixtures/process-common-view";

test("reviews and locally exports exact source-run diagnostics from the working view", async ({
  page,
}, testInfo) => {
  const fixture = await mockCommonProcessWorkspace(page);
  const hash = `sha256:${"a".repeat(64)}`;
  const preview: SupportDiagnosticPreview = {
    snapshot: {
      schema_version: "1.0",
      snapshot_id: "snapshot_browser_1",
      created_at: "2026-10-23T12:00:00Z",
      expires_at: "2099-10-23T12:05:00Z",
      workspace_id: fixture.process.workspace_id,
      principal_digest: hash,
      scope: { source_run_id: fixtureRunId },
      summary: {
        status: "degraded",
        reason: "FAILURES_RECORDED",
        next_action: "INSPECT_RECOVERY",
      },
      providers: [],
      state_inventory: {
        schema_version: "1.0",
        data_schema: 1,
        catalog_snapshot: {
          channel: "bundled",
          sequence: 0,
          digest: hash,
          state: "bundled",
        },
        counts: {},
        digests: {},
        storage: [],
      },
      failures: [
        {
          stage: "source-run",
          provider_kind: "runtime",
          reason: "SOURCE_RUN_FAILED",
          cleanup: "unknown",
          recovery: "INSPECT_BEFORE_RETRY",
        },
      ],
      categories: [
        {
          name: "raw-engineering-payloads",
          disposition: "omitted",
          item_count: 0,
          reason: "PROPRIETARY_CONTENT_FORBIDDEN",
        },
      ],
      source_run: {
        run_id: fixtureRunId,
        source_digest: `sha256:${fixture.process.source_digest}`,
        record_digest: hash,
        recorded_status: "failed",
        event_count: 2,
        events_truncated: false,
        metadata_omitted: false,
        started_at: "2026-10-23T12:00:00Z",
        ended_at: "2026-10-23T12:00:05Z",
        events: [
          {
            sequence: 2,
            kind: "step_diagnostic",
            step_id: "first",
            at: "2026-10-23T12:00:05Z",
            reason: "INTERACTION_NOT_DECLARED",
          },
        ],
      },
      snapshot_digest: hash,
    },
    snapshot_digest: hash,
    confirmation_token: "browser-preview-only-token",
    expires_at: "2099-10-23T12:05:00Z",
    filename: "wright-support-browser.json",
  };
  let previews = 0;
  let exports = 0;
  await page.route("**/api/workspace/support-diagnostics/**", async (route) => {
    const request = route.request();
    expect(request.method()).toBe("POST");
    if (request.url().endsWith("/preview")) {
      previews += 1;
      expect(request.postDataJSON()).toEqual({
        workspace_id: fixture.process.workspace_id,
        scope: { source_run_id: fixtureRunId },
      });
      return route.fulfill({ json: preview });
    }
    expect(request.url()).toMatch(/\/export$/);
    exports += 1;
    expect(request.postDataJSON()).toEqual({
      workspace_id: fixture.process.workspace_id,
      snapshot_digest: hash,
      confirmation_token: preview.confirmation_token,
    });
    return route.fulfill({
      json: preview.snapshot,
      headers: {
        "content-disposition":
          'attachment; filename="wright-support-browser.json"',
      },
    });
  });
  await page.goto(`/workspace/${fixture.process.workspace_id}`);
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
  await expect(page.getByTestId("workflow-recovery-canvas")).toBeVisible();
  await page.getByTestId("workflow-working-view-open").click();
  await page
    .getByLabel("Design request (required)")
    .fill("Controlled diagnostic browser proof.");
  await page
    .getByRole("button", { name: "Prepare and check inputs", exact: true })
    .click();
  await page
    .getByRole("button", { name: "Start workflow", exact: true })
    .click();
  await expect(page.getByTestId("workspace-process-view")).toHaveAttribute(
    "data-run-id",
    fixtureRunId,
  );
  fixture.failWithUndeclaredInput();
  await page.getByRole("button", { name: "Refresh view", exact: true }).click();
  const common = page.getByTestId("common-process-view");
  await expect(
    common.getByText(
      "Create test report: additional user input was requested in an unattended step.",
      { exact: true },
    ),
  ).toBeVisible();
  await common.getByText("Diagnose this run", { exact: true }).click();
  expect(previews).toBe(0);
  expect(exports).toBe(0);
  const panel = page.getByTestId("support-diagnostics-panel");
  await panel.getByRole("button", { name: "Preview support file" }).click();
  await expect(panel.getByText(/recorded status: failed/)).toBeVisible();
  await expect(
    panel.getByRole("button", { name: "Inspect step first" }),
  ).toBeVisible();
  await expect(panel.getByTestId("support-diagnostics-export")).toBeDisabled();
  expect(exports).toBe(0);
  await panel.scrollIntoViewIfNeeded();
  await page.screenshot({
    path: testInfo.outputPath("local-diagnostic-preview.png"),
    fullPage: true,
  });
  await panel.getByTestId("support-diagnostics-confirm").check();
  const downloaded = page.waitForEvent("download");
  await panel.getByTestId("support-diagnostics-export").click();
  expect((await downloaded).suggestedFilename()).toBe(
    "wright-support-browser.json",
  );
  expect(exports).toBe(1);
  await expect(panel.getByTestId("support-diagnostics-export")).toBeDisabled();
  await panel.getByRole("button", { name: "Inspect step first" }).click();
  await expect(page.getByTestId("workflow-recovery-inspector")).toContainText(
    "Use the supplied test request to prepare a report.",
  );
  expect(fixture.navigations().at(-1)).toEqual({
    kind: "block",
    block_id: "first",
    run_id: fixtureRunId,
  });
  expect(fixture.starts()).toBe(1);
  expect(fixture.cancellations()).toBe(0);
  expect(fixture.editor.updateCount()).toBe(0);
  await testInfo.attach("scope.json", {
    contentType: "application/json",
    body: JSON.stringify({
      served_frontend: true,
      controlled_http_contracts: true,
      live_backend: false,
      live_tools: false,
      previews,
      exports,
      run_id: fixtureRunId,
    }),
  });
});
