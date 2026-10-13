import { expect, test } from "@playwright/test";
import AxeBuilder from "@axe-core/playwright";
import { createHash } from "node:crypto";
import {
  fixtureRunId,
  commonViewSource,
  mockCommonProcessWorkspace,
} from "./fixtures/process-common-view";
import { openRecoveryEditor } from "./fixtures/workflow-recovery";
import { processWalkthrough } from "./fixtures/process-walkthrough";

test("prepares an uploaded reference image with a real thumbnail and follows observed progress through workspace tabs", async ({page}, testInfo) => {
  const source = commonViewSource + `input reference
  name: "Reference image"
  purpose: "Provide an optional reference bitmap."
  group: null
  step_type: work
  provided_by: engineer
  inputs: []
  outputs: [{"key":"reference_out","kind":"engineering_document","name":"Reference","required":false,"item":null,"quantity":"one","description":"Supplied bitmap"}]
  instructions: "Choose an optional reference image."
  settings: {"input_mode":"file"}
  tool: null
  reusable_step: null
end
`;
  const fixture = await mockCommonProcessWorkspace(page, {source, includeImage: true, holdImageUpload: true});
  const walk = processWalkthrough(page, testInfo);
  const common = page.getByTestId("common-process-view");
  const prepare = page.getByRole("button", {name: "Prepare and check inputs", exact: true});
  const start = page.getByRole("button", {name: "Start process", exact: true});
  await walk.step({id:"S01", label:"Normal workspace and accepted process", purpose:"Use Wright's existing authoring entry.", action:"Open the isolated workspace and click Workflows.", controls:["Workflows"], expected:"The accepted process opens in the existing editor.", actual:"The normal workspace editor opens; no run is submitted."},
    () => openRecoveryEditor(page), async () => {expect(fixture.starts()).toBe(0);});
  await walk.step({id:"S02", label:"Common working tab", purpose:"Inspect the optional shared interface on the same process.", action:"Click Use saved process.", controls:["Use saved process"], expected:"Inputs and preparation controls open in a workspace tab.", actual:"The common view shows Design request and Reference image; starting is disabled."},
    async () => {await page.getByTestId("workflow-working-view-open").click();},
    async () => {await expect(common).toBeVisible(); await expect(page.getByLabel("Reference image", {exact:true})).toBeVisible(); await expect(start).toBeDisabled();});
  await walk.step({id:"S03", label:"Provide the design request", purpose:"Gather the declared user input before execution.", action:"Enter Make a small test part using the reference image in Design request.", controls:["Design request (required)"], expected:"The draft is entered without starting or editing source.", actual:"The typed draft stays in the working view and no dispatch occurs."},
    async () => {await page.getByLabel("Design request (required)").fill("Make a small test part using the reference image.");},
    async () => {expect(fixture.starts()).toBe(0); expect(fixture.editor.updateCount()).toBe(0);});
  const bitmap = Buffer.from("iVBORw0KGgoAAAANSUhEUgAAAGAAAABgCAYAAADimHc4AAABjElEQVR4nO3cMQ7CQAwFUQ7BYTk2NwC52CYlSzL+zozkHv1XouzjY2gP+gfcPQHgBIATAE4AOAHgBIATAE4AOAHgBIATAE4AOAHgBIATAE4AOAHgBIATAC4C4P16/nzdawmwM3gaSCuAM4fvCtEC4Mrhu0GgAOTwXSAwAHrwLggIAD10J4RLAehxO0JcBkAP2hXhEgB6yM4IpwPQA3ZHEGAyAD1cAsJpAPRgKQinANBDJSEIMA2AHigNQYBJAPQwiQgCTAGgB0lFEECA3PtHAkwAoIdIRhBAgOzbTQABsm83AQTIvt0EECD7dhNAgOzbTQABsm83AQTIvt38PwAcvxJAgNz7RwJMAajoQdLGrwSYBFDRwySNXwkwDaCiB0oZvxJgIkBFD5UwfuVXkuD4ld8Jg+NXAkwHqOgBu45f+VoKOH7le0Hg+JUvZkHDr3wzDhy/8tVEcPzKd0PhWgCs7jT8qhXA6g7Dr1oCHJs0+LEIgMkJACcAnABwAsAJACcAnABwAsAJACcAnABwAsAJACcAnABwX9ubo0DKXBqyAAAAAElFTkSuQmCC", "base64");
  await walk.step({id:"S04", label:"Uploaded bitmap and pending transfer", purpose:"Show the actual selected file and prevent early preparation.", action:"Choose reference.png in Reference image.", controls:["Reference image"], expected:"A decoded thumbnail and file-transfer progress are visible; preparation/start remain disabled.", actual:"The 96 by 96 bitmap decodes, Preparing file is visible and no process can start while upload is pending."},
    async () => {await page.getByLabel("Reference image", {exact:true}).setInputFiles({name:"reference.png", mimeType:"image/png", buffer:bitmap});},
    async () => {
      const image = common.getByRole("img", {name:"Selected reference: reference.png"});
      await expect(image).toBeVisible();
      await expect.poll(() => image.evaluate(element => ({width:(element as HTMLImageElement).naturalWidth, height:(element as HTMLImageElement).naturalHeight}))).toEqual({width:96,height:96});
      await image.scrollIntoViewIfNeeded();
      // IntersectionObserver rounds fractional CSS pixels differently across hosts.
      // Keep the complete thumbnail inside the viewport within one CSS pixel.
      await expect(image).toBeInViewport({ratio:0.999});
      const bounds = await image.boundingBox(); const viewport = page.viewportSize();
      expect(bounds).not.toBeNull(); expect(viewport).not.toBeNull();
      expect(bounds!.x).toBeGreaterThanOrEqual(-1); expect(bounds!.y).toBeGreaterThanOrEqual(-1);
      expect(bounds!.x + bounds!.width).toBeLessThanOrEqual(viewport!.width + 1);
      expect(bounds!.y + bounds!.height).toBeLessThanOrEqual(viewport!.height + 1);
      await expect(common.getByText("Preparing file…", {exact:true})).toBeVisible();
      await expect(prepare).toBeDisabled(); await expect(start).toBeDisabled(); expect(fixture.starts()).toBe(0);
    });
  await walk.step({id:"S05", label:"Transfer finishes before preparation", purpose:"Retain an exact scoped file reference.", action:"Wait for the file upload to complete.", controls:["Prepare and check inputs"], expected:"Preparation becomes available after the scoped upload reply.", actual:"The upload's original SHA-256 and process scope are retained; the thumbnail stays visible."},
    async () => {fixture.releaseImageUpload();},
    async () => {await expect(prepare).toBeEnabled(); await expect(common.getByText("Preparing file…",{exact:true})).toHaveCount(0); await expect(common.getByRole("alert")).toHaveCount(0); expect(fixture.uploads()).toHaveLength(1); expect(fixture.uploads()[0].sha256).toBe(createHash("sha256").update(bitmap).digest("hex"));});
  await walk.step({id:"S06", label:"Check all supplied inputs", purpose:"Prepare immutable run inputs before starting.", action:"Click Prepare and check inputs.", controls:["Prepare and check inputs"], expected:"The exact prompt and file binding are prepared, then start becomes permitted.", actual:"Prepared inputs contain the same uploaded reference and Start process is enabled."},
    async () => {await prepare.click();},
    async () => {await expect(start).toBeEnabled(); expect(fixture.preparedInput()?.bindings?.find(value => value.input_id === "reference")).toMatchObject({kind:"file",reference:fixture.uploads()[0]});});
  await walk.step({id:"S07", label:"Observe the recorded run", purpose:"Show backend-supplied activity, progress and observation provenance.", action:"Click Start process and open Observation details.", controls:["Start process","Observation details"], expected:"The returned run is attached once and the observed activity/percentage/provider are shown.", actual:"The exact run attaches; 20 percent observed completion and the controlled provider/activity are visible without guessed completion."},
    async () => {await start.click(); await common.getByText("Observation details",{exact:true}).click();},
    async () => {await expect(page.getByTestId("workspace-process-view")).toHaveAttribute("data-run-id",fixtureRunId); await expect(common.getByRole("progressbar",{name:"Observed completion"})).toHaveAttribute("value","20"); await expect(common.getByText("Preparing the controlled fixture report",{exact:true})).toBeVisible(); await expect(common.getByText("Provider: controlled-browser-fixture",{exact:true})).toBeVisible(); expect(fixture.starts()).toBe(1);});
  await walk.step({id:"S08", label:"Inspect completion and scoped accessibility", purpose:"Present a completed recorded result while retaining evidence limits.", action:"Wait for completion, then click Refresh view.", controls:["Refresh view"], expected:"Recorded completion and the exact result appear; common controls pass the scoped automated accessibility scan.", actual:"The saved result and 100 percent last reported are shown. Scoped WCAG A/AA scanning finds zero violations."},
    async () => {fixture.complete(); await common.getByRole("button",{name:"Refresh view",exact:true}).click();},
    async () => {await expect(common.getByText("Process completed",{exact:true})).toBeVisible(); await expect(common.locator("[data-result-id]")).toHaveAttribute("data-result-id",fixture.resultId); await expect(common.getByText("100% last reported",{exact:true})).toBeVisible(); const scan=await new AxeBuilder({page}).include('[data-testid="common-process-view"]').withTags(["wcag2a","wcag2aa","wcag21a","wcag21aa"]).analyze(); expect(scan.violations).toEqual([]);});
  const savedUrl = page.url();
  await walk.step({id:"S09", label:"Reopen without replay", purpose:"Keep run authority with Wright when the tab closes.", action:"Close the working tab, then reopen its saved link.", controls:["Close working tab","Saved run link"], expected:"The same completed run reopens without a second dispatch or cancellation.", actual:"The same exact run/result reopens; one start, zero cancellations and zero accepted-source edits remain."},
    async () => {await page.getByTestId("editor-tabs-container").locator('[data-testid^="editor-tab-close-/.wright/process-views/"]').click(); await expect(common).toHaveCount(0); await page.goto(savedUrl);},
    async () => {await expect(common.getByText("Process completed",{exact:true})).toBeVisible(); await expect(common.locator("[data-result-id]")).toHaveAttribute("data-result-id",fixture.resultId); expect(fixture.starts()).toBe(1); expect(fixture.cancellations()).toBe(0); expect(fixture.editor.updateCount()).toBe(0); expect(walk.diagnostics).toEqual([]);});
});

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

test("shows an unattended-input diagnostic without inventing a form and reopens the same failed run", async ({
  page,
}, testInfo) => {
  const fixture = await mockCommonProcessWorkspace(page);
  await openRecoveryEditor(page);
  await page.getByTestId("workflow-working-view-open").click();
  await page
    .getByLabel("Design request (required)")
    .fill("Controlled diagnostic fixture request.");
  await page
    .getByRole("button", { name: "Prepare and check inputs", exact: true })
    .click();
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
  fixture.failWithUndeclaredInput();
  await page.getByRole("button", { name: "Refresh view", exact: true }).click();
  const common = page.getByTestId("common-process-view");
  const explanation = common.getByText(
    "Create test report: additional user input was requested in an unattended step.",
    { exact: true },
  );
  await expect(explanation).toBeVisible();
  await expect(
    common.getByText(
      "Supply the missing requirement before starting, connect an upstream producer, or declare a human-input step before this task.",
      { exact: true },
    ),
  ).toBeVisible();
  await expect(
    common.getByRole("button", { name: "Submit response", exact: true }),
  ).toHaveCount(0);
  await expect(common.getByRole("combobox")).toHaveCount(0);
  const savedUrl = page.url();
  await explanation.scrollIntoViewIfNeeded();
  await page.screenshot({
    path: testInfo.outputPath("undeclared-input-diagnostic.png"),
    fullPage: true,
  });
  await common
    .getByRole("button", { name: "Open related item", exact: true })
    .click();
  await expect(page.getByTestId("workflow-recovery-inspector")).toContainText(
    "Use the supplied test request to prepare a report.",
  );
  expect(fixture.navigations().at(-1)).toEqual({
    kind: "block",
    block_id: "first",
    run_id: fixtureRunId,
  });
  await page.goto(savedUrl);
  await expect(explanation).toBeVisible();
  expect(fixture.starts()).toBe(1);
  expect(fixture.editor.runCount()).toBe(0);
  expect(fixture.cancellations()).toBe(0);
});

test("uses the normal workspace to prepare, follow and inspect an exact run while retaining source edits", async ({
  page,
}, testInfo) => {
  const fixture = await mockCommonProcessWorkspace(page, {
    disconnectEvents: true,
  });
  await openRecoveryEditor(page);
  // Bind the working tab to the accepted source before leaving an unsaved draft.
  await page.getByTestId("workflow-working-view-open").click();
  const common = page.getByTestId("common-process-view");
  await expect(common).toBeVisible();
  await page.getByRole("tab").filter({ hasText: "mounting-bracket" }).first().click();
  await page.getByTestId("workflow-recovery-view-code").click();
  const source = page.getByTestId("workflow-recovery-source-editor");
  const draft = `${await source.inputValue()}\n# Uncommitted browser source draft\n`;
  await source.fill(draft);
  await expect(page.getByTestId("workflow-working-view-open")).toBeDisabled();
  await page.getByRole("tab").filter({ hasText: "mounting-bracket" }).last().click();
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
    .getByRole("button", { name: "Close file", exact: true })
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
