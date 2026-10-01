import { expect, test } from "@playwright/test";
import {
  fixtureRunId,
  mockCommonProcessWorkspace,
} from "./fixtures/process-common-view";
import { openRecoveryEditor } from "./fixtures/workflow-recovery";

test.afterEach(async ({ page, browser }, testInfo) => {
  if (!page.isClosed()) {
    await page.screenshot({
      path: testInfo.outputPath("workspace-final-state.png"),
      fullPage: true,
      timeout: 10_000,
    });
    await testInfo.attach("checked-scope.json", {
      contentType: "application/json",
      body: Buffer.from(
        JSON.stringify(
          {
            browser: browser.version(),
            url: page.url(),
            viewport: page.viewportSize(),
            served_frontend: true,
            controlled_http_contracts: true,
            live_backend: false,
            live_model: false,
            live_mcp: false,
            physical_operation: false,
            user_acceptance: false,
          },
          null,
          2,
        ),
      ),
    });
  }
});

test("uses the normal workspace to prepare, follow and inspect an exact run while retaining source edits", async ({
  page,
}, testInfo) => {
  const fixture = await mockCommonProcessWorkspace(page, {
    disconnectEvents: true,
  });
  await openRecoveryEditor(page);
  await page.getByTestId("workflow-recovery-view-code").click();
  const source = page.getByTestId("workflow-recovery-source-editor");
  const draft = `${await source.inputValue()}\n# Uncommitted browser source draft\n`;
  await source.fill(draft);
  await page.getByTestId("workflow-working-view-open").click();
  const common = page.getByTestId("common-process-view");
  await expect(common).toBeVisible();
  await expect(
    page.getByRole("button", { name: "Start process", exact: true }),
  ).toBeDisabled();
  expect(fixture.starts()).toBe(0);
  await page
    .getByRole("button", { name: "Prepare and check inputs", exact: true })
    .click();
  await expect(
    common.getByText("Provide the design request before starting.", {
      exact: true,
    }),
  ).toBeVisible();
  await expect(
    page.getByRole("button", { name: "Start process", exact: true }),
  ).toBeDisabled();
  await page
    .getByLabel("Design request (required)")
    .fill("Use the exact controlled request.");
  await page
    .getByRole("button", { name: "Prepare and check inputs", exact: true })
    .click();
  await expect(
    page.getByRole("button", { name: "Preparing and checking…", exact: true }),
  ).toBeVisible();
  await expect(
    page.getByRole("button", { name: "Start process", exact: true }),
  ).toBeEnabled();
  await page
    .getByRole("button", { name: "Start process", exact: true })
    .click();
  await expect(page.getByTestId("workspace-process-view")).toHaveAttribute(
    "data-run-id",
    fixtureRunId,
  );
  await expect(
    common.getByText("Preparing the controlled fixture report", {
      exact: true,
    }),
  ).toBeVisible();
  await expect.poll(fixture.eventReads).toBeGreaterThan(1);
  expect(fixture.starts()).toBe(1);
  expect(fixture.editor.runCount()).toBe(0);
  fixture.complete();
  await page.getByRole("button", { name: "Refresh view", exact: true }).click();
  await expect(
    common.getByText("Process completed", { exact: true }),
  ).toBeVisible();
  const result = common.locator("[data-result-id]");
  await expect(result).toHaveAttribute("data-result-id", fixture.resultId);
  await result
    .getByRole("button", { name: "Open assessment", exact: true })
    .click();
  const evidence = common.getByText(/Controlled assessment evidence/);
  await expect(evidence).toBeVisible();
  await evidence.scrollIntoViewIfNeeded();
  await expect(evidence).toBeInViewport();
  expect(fixture.representations().at(-1)?.result_id).toBe(
    `${fixtureRunId}:validator:assessment`,
  );
  await page.screenshot({
    path: testInfo.outputPath("exact-assessment.png"),
    fullPage: true,
  });
  await page
    .getByRole("button", { name: "Close representation", exact: true })
    .click();
  await result
    .getByRole("button", { name: "Open producing step", exact: true })
    .click();
  await expect(page.getByTestId("workflow-recovery-inspector")).toBeVisible();
  await expect(page.getByTestId("workflow-recovery-inspector")).toContainText(
    "Use the supplied test request to prepare a report.",
  );
  await expect(source).toHaveValue(draft);
  expect(fixture.editor.updateCount()).toBe(0);
  await page.screenshot({
    path: testInfo.outputPath("retained-editor-draft.png"),
    fullPage: true,
  });
  const runTab = page
    .getByRole("tab")
    .filter({ hasText: "mounting-bracket" })
    .last();
  await runTab.click();
  await expect(common).toBeVisible();
  const savedUrl = page.url();
  expect(savedUrl).toContain(`processRun=${fixtureRunId}`);
  // The working view carries its run; the document-strip close target is its virtual path.
  const workingClose = page
    .getByTestId("editor-tabs-container")
    .locator('[data-testid^="editor-tab-close-/.wright/process-views/"]');
  await workingClose.click();
  await expect(common).toHaveCount(0);
  expect(fixture.cancellations()).toBe(0);
  await page.goto(savedUrl);
  await expect(page.getByTestId("workspace-process-view")).toHaveAttribute(
    "data-run-id",
    fixtureRunId,
  );
  await expect(
    page
      .getByTestId("common-process-view")
      .getByText("Process completed", { exact: true }),
  ).toBeVisible();
  await expect(
    page
      .getByTestId("common-process-view")
      .getByText("100% last reported", { exact: true }),
  ).toBeVisible();
  expect(fixture.starts()).toBe(1);
  expect(fixture.cancellations()).toBe(0);
  await page.screenshot({
    path: testInfo.outputPath("reopened-exact-run.png"),
    fullPage: true,
  });
});

test("reconciles a lost start acknowledgement after reload using the original request identity", async ({
  page,
}, testInfo) => {
  const fixture = await mockCommonProcessWorkspace(page, {
    loseStartAcknowledgement: true,
  });
  await openRecoveryEditor(page);
  await page.getByTestId("workflow-working-view-open").click();
  await page
    .getByLabel("Design request (required)")
    .fill("Controlled lost acknowledgement fixture.");
  await page
    .getByRole("button", { name: "Prepare and check inputs", exact: true })
    .click();
  await expect(
    page.getByRole("button", { name: "Start process", exact: true }),
  ).toBeEnabled();
  await page
    .getByRole("button", { name: "Start process", exact: true })
    .click();
  await expect(
    page.getByRole("button", { name: "Reconcile start request", exact: true }),
  ).toBeVisible();
  expect(fixture.starts()).toBe(1);
  await page.reload();
  await expect(
    page.getByRole("button", { name: "Reconcile start request", exact: true }),
  ).toBeVisible();
  await expect(
    page.getByRole("button", { name: "Start process", exact: true }),
  ).toBeDisabled();
  expect(fixture.starts()).toBe(1);
  await page
    .getByRole("button", { name: "Reconcile start request", exact: true })
    .click();
  await expect(page.getByTestId("workspace-process-view")).toHaveAttribute(
    "data-run-id",
    fixtureRunId,
  );
  expect(fixture.starts()).toBe(2);
  expect(new Set(fixture.requests()).size).toBe(1);
  expect(fixture.accepted()?.request_id).toBe(fixture.requests()[0]);
  fixture.complete();
  await page.getByRole("button", { name: "Refresh view", exact: true }).click();
  await expect(
    page
      .getByTestId("common-process-view")
      .getByText("Process completed", { exact: true }),
  ).toBeVisible();
  expect(fixture.editor.runCount()).toBe(0);
  await page.screenshot({
    path: testInfo.outputPath("reconciled-start.png"),
    fullPage: true,
  });
});
