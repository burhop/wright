/** Opt-in qualification: controlled workspace chrome, actual model/build/preview.
 * This is a software integration proof, not an engineering or physical run.
 */
import { readFileSync, writeFileSync } from "node:fs";
import type { AuthoringJob, InterfaceRevision } from "@wright/process-client";
import { expect, test, type Page } from "@playwright/test";
import { commonViewSource } from "./fixtures/process-common-view";
import { mockRecoveryWorkspace, openRecoveryEditor } from "./fixtures/workflow-recovery";

const contextFile = process.env.WRIGHT_PROCESS_UI_PROOF_CONTEXT;
const resumeJobId = process.env.WRIGHT_PROCESS_UI_PROOF_JOB;
const diagnostics = new WeakMap<Page, {errors: string[]; requests: Array<{path: string; status: number}>; console: string[]}>();
const ownedViews = new WeakMap<Page, Array<{surface_id: string; presentation_id: string}>>();
test.afterEach(async ({page, context}, info) => {
  try {
  if (!page.isClosed()) {
  await page.screenshot({path: info.outputPath("final-browser-state.png"), fullPage: true, timeout: 15_000});
  const frames = await Promise.all(page.frames().filter(frame => frame !== page.mainFrame()).map(async frame => ({
    // Bootstrap credentials and cookies never enter the public report.
    origin: new URL(frame.url()).origin,
    body: await frame.locator("body").innerText({timeout: 2000}).catch(() => "Frame document unavailable"),
    asset_probe: await frame.evaluate(async () => {
      const asset = await fetch("/app.js", {signal: AbortSignal.timeout(5000)});
      return {status: asset.status, media: asset.headers.get("content-type")};
    }).catch(() => null),
  })));
  const reportPath = info.outputPath("browser-diagnostics.json");
  writeFileSync(reportPath, JSON.stringify({
    ...diagnostics.get(page), frames, resumed_job: resumeJobId ?? null,
  }, null, 2));
  await info.attach("browser-diagnostics.json", {contentType: "application/json", path: reportPath});
  }
  } finally {
  if (contextFile) {
    const proof = JSON.parse(readFileSync(contextFile, "utf8"));
    const closures = [];
    for (const view of ownedViews.get(page) ?? []) {
      try {
      const response = await context.request.post(proof.api_url + "/api/workspace/process-interfaces/presentations/close", {data: {...proof.query, ...view}, timeout: 30_000});
      closures.push({presentation_id: view.presentation_id, status: response.status()});
      } catch {
        // Playwright request error logs include cookies. Keep failures locatable
        // without publishing headers; the private owner can reconcile cleanup.
        closures.push({presentation_id: view.presentation_id, status: 0});
      }
    }
    writeFileSync(info.outputPath("owned-view-cleanup.json"), JSON.stringify({closures, process_cancelled: false}, null, 2));
    expect(closures.every(value => value.status === 204)).toBe(true);
  }
  }
});
test("authors, previews, saves and reopens through the workspace @live", async ({ page, context }, info) => {
  test.skip(!contextFile, "Needs an explicitly started isolated managed-process qualification harness.");
  test.setTimeout(780_000);
  page.setDefaultTimeout(30_000);
  page.setDefaultNavigationTimeout(30_000);
  const stage = (name: string) => writeFileSync(info.outputPath("progress.json"), JSON.stringify({stage: name, recorded_at: new Date().toISOString()}));
  const proof = JSON.parse(readFileSync(contextFile!, "utf8"));
  expect(proof.workspace_id).toBe("ws-recovery");
  await context.addCookies([{name: "wright_session", value: proof.browser_cookie,
    url: proof.frontend_url + "/api", httpOnly: true, sameSite: "Strict"}]);
  await mockRecoveryWorkspace(page, {source: commonViewSource});
  // Only chrome/accepted-source discovery is controlled. Do not stub any
  // process/authoring API, preview bootstrap, bridge, worker or browser message.
  await page.route("**/api/workspace/process-interfaces/**", route => route.continue());
  const errors: string[] = [], requests: Array<{path: string; status: number}> = [], messages: string[] = [];
  diagnostics.set(page, {errors, requests, console: messages});
  ownedViews.set(page, []);
  page.on("console", message => {
    if (message.type() === "error") messages.push(message.text().replace(/#[^\s]+/g, "#[redacted]"));
  });
  page.on("pageerror", error => errors.push(error.message));
  page.on("response", async response => {
    const url = new URL(response.url());
    if (url.pathname.startsWith("/api/workspace/process-interfaces/") || url.hostname.startsWith("s-"))
      requests.push({path: url.pathname, status: response.status()});
    if (response.status() === 200 && response.request().method() === "POST" && /\/(preview|present)$/.test(url.pathname)) {
      const value = await response.json();
      ownedViews.get(page)!.push({surface_id: value.descriptor.surfaceId, presentation_id: value.binding.presentation_id});
    }
  });
  await openRecoveryEditor(page);
  await page.getByTestId("workflow-working-view-open").click();
  await expect(page.getByTestId("common-process-view")).toBeVisible();
  const commonTab = await page.getByTestId("editor-tabs-container").locator('[role="tab"][aria-selected="true"]').getAttribute("data-testid");
  expect(commonTab).toBeTruthy();
  let accepted: AuthoringJob;
  let retainedRevision: Pick<InterfaceRevision, "manifest" | "build" | "previewed_at"> | undefined;
  let retainedActive: string | undefined;
  if (resumeJobId) {
    const response = await context.request.get(proof.api_url + "/api/workspace/process-interfaces/authoring-jobs/" + resumeJobId +
      "?" + new URLSearchParams(proof.query));
    expect(response.status()).toBe(200);
    const retained = await response.json();
    accepted = retained.job;
    if (accepted!.state === "saved") {retainedRevision = retained.preview; retainedActive = retained.preview.active_revision;}
    const viewId = commonTab!.split("/").at(-1)!;
    await page.evaluate(({process, sessionId, viewId, job}) => {
      const key = "wright.process-ui-authoring/1:" + JSON.stringify([process.workspace_id, process.source_path, process.source_digest, sessionId, viewId]);
      localStorage.setItem(key, JSON.stringify({version: "1", process, job_id: job.job_id,
        request: {request_id: job.request_id, instruction: "Recover the exact existing qualification job without regeneration.", title: "UI qualification comparison"}}));
    }, {process: accepted.process, sessionId: proof.query.session_id, viewId, job: accepted});
  }
  await page.getByRole("button", {name: "Create or choose interface", exact: true}).click();
  if (!resumeJobId) {
  await page.getByRole("textbox", {name: "Interface title", exact: true}).fill("UI qualification comparison");
  await page.getByRole("textbox", {name: "How should this interface help the user?", exact: true}).fill(
    "Build a concise read-only comparison dashboard using the public Wright kit. " +
    "Show backend process status, declared inputs, exact outputs, diagnostics and findings. " +
    "Use a two-column layout with titled sections, a useful empty-results message and accessible controls. " +
    "This is an isolated software qualification, not an engineering result. " +
    "Do not start any process or add review/action/start controls. Retain the supplied exact manifest and bindings. " +
    "Use safe optional-array defaults. Return the required source/manifest JSON."
  );
  const creation = page.waitForResponse(response => response.request().method() === "POST" &&
    new URL(response.url()).pathname.endsWith("/authoring-jobs"));
  await expect(page.getByRole("button", {name: "Create interface", exact: true})).toBeEnabled();
  await page.getByRole("button", {name: "Create interface", exact: true}).click();
  const response = await creation;
  expect(response.status()).toBe(202);
  accepted = await response.json();
  await expect(page.getByRole("region", {name: "Interface creation progress"})).toBeVisible();
  await page.screenshot({path: info.outputPath("creating-interface.png"), fullPage: true});
  }
  await expect(page.getByRole("heading", {name: retainedRevision ? "Interface saved" : "Preview ready", exact: true})).toBeVisible({timeout: 330_000});
  const open = page.waitForResponse(response => response.request().method() === "POST" &&
    new URL(response.url()).pathname.endsWith("/preview"));
  await page.getByRole("button", {name: "Open preview", exact: true}).click();
  const previewResponse = await open;
  expect(previewResponse.status(), previewResponse.ok() ? "" : await previewResponse.text()).toBe(200);
  const presentation = await previewResponse.json();
  await expect(page).toHaveURL(/processUIKind=preview/);
  // Workspace tabs retain hidden frames. Only inspect the active document.
  const frame = page.locator('[data-testid="surface-panel-host"]:visible').frameLocator("iframe");
  await expect(frame.getByText("Preview - process controls are read-only.", {exact: true})).toBeVisible({timeout: 25_000});
  await expect(frame.locator("#wright-process-ui")).not.toContainText("Interface unavailable");
  await expect(frame.locator("#wright-process-ui")).not.toBeEmpty();
  await page.screenshot({path: info.outputPath("managed-preview.png"), fullPage: true});
  await page.getByTestId(commonTab!).click();
  let revision: Pick<InterfaceRevision, "manifest" | "build" | "previewed_at">;
  if (retainedRevision) {
    revision = retainedRevision;
    await page.getByRole("combobox", {name: "Saved interface", exact: true}).selectOption(revision.manifest.ui_id);
    if (retainedActive !== revision.manifest.revision_id) {
      await page.getByRole("combobox", {name: "Saved revision", exact: true}).selectOption(revision.manifest.revision_id);
      await expect(page.getByRole("button", {name: "Use this revision", exact: true})).toBeEnabled();
      const restored = page.waitForResponse(response => response.request().method() === "POST" && new URL(response.url()).pathname.endsWith("/activate"));
      await page.getByRole("button", {name: "Use this revision", exact: true}).click();
      expect((await restored).status()).toBe(200);
      await expect(page.getByRole("button", {name: "Use this revision", exact: true})).toBeDisabled();
    }
  } else {
  await expect(page.getByRole("button", {name: "Save interface", exact: true})).toBeEnabled({timeout: 15_000});
  const savedResponse = page.waitForResponse(response => response.request().method() === "POST" &&
    new URL(response.url()).pathname.endsWith("/save"));
  await page.getByRole("button", {name: "Save interface", exact: true}).click();
  const saved = await savedResponse;
  expect(saved.status()).toBe(200);
  revision = await saved.json();
  await expect(page.getByRole("heading", {name: "Interface saved", exact: true})).toBeVisible();
  }
  const authoringPosts = requests.filter(value => value.path.endsWith("/authoring-jobs")).length;
  const presentResponse = page.waitForResponse(response => response.request().method() === "POST" &&
    new URL(response.url()).pathname.endsWith("/present"));
  await expect(page.getByRole("button", {name: "Open saved interface", exact: true})).toBeEnabled();
  await page.getByRole("button", {name: "Open saved interface", exact: true}).click();
  const working = await presentResponse;
  expect(working.status()).toBe(200);
  await expect(page).toHaveURL(/processUIKind=working/);
  await expect(frame.getByText("Connected to Wright.", {exact: true})).toBeVisible({timeout: 25_000});
  await expect(frame.locator("#wright-process-ui")).not.toContainText("Interface unavailable");
  await page.screenshot({path: info.outputPath("saved-working-interface.png"), fullPage: true});
  expect(requests.filter(value => value.path.endsWith("/authoring-jobs")).length).toBe(authoringPosts);
  stage("theme update");
  await page.evaluate(() => document.documentElement.style.setProperty("--color-primary", "#bfeaff"));
  await expect.poll(() => frame.locator("html").evaluate(element => getComputedStyle(element).getPropertyValue("--color-primary").trim()))
    .toBe("#bfeaff");
  const reconnected = page.waitForResponse(response => new URL(response.url()).pathname.endsWith("/__wright/process/context"));
  stage("frame reload");
  await frame.locator("html").evaluate(() => location.reload());
  expect((await reconnected).status()).toBe(200);
  await expect(frame.getByText("Connected to Wright.", {exact: true})).toBeVisible({timeout: 25_000});
  await expect.poll(() => frame.locator("html").evaluate(element => getComputedStyle(element).getPropertyValue("--color-primary").trim()))
    .toBe("#bfeaff");
  const modelCallsBeforeUpdate = requests.filter(value => value.path.endsWith("/authoring-jobs")).length;
  expect(modelCallsBeforeUpdate).toBe(authoringPosts);
  stage("focused update request");

  await page.getByTestId(commonTab!).click();
  await page.getByRole("textbox", {name: "How should this interface help the user?", exact: true}).fill(
    "Refine the existing saved read-only comparison interface. Keep the same exact manifest identity, bindings, public kit and process client. " +
    "Put backend findings and diagnostics first and add a concise note explaining that an empty result is not engineering acceptance. " +
    "Preserve all existing sections and accessible semantics. This is presentation only; do not start work or add controls. Return the required source/manifest JSON."
  );
  const updateAccepted = page.waitForResponse(response => response.request().method() === "POST" &&
    new URL(response.url()).pathname.endsWith("/authoring-jobs"));
  await expect(page.getByRole("button", {name: "Update selected interface", exact: true})).toBeEnabled();
  await page.getByRole("button", {name: "Update selected interface", exact: true}).click();
  const updatedResponse = await updateAccepted;
  expect(updatedResponse.status()).toBe(202);
  const updatedJob: AuthoringJob = await updatedResponse.json();
  stage("focused update generation");
  expect(updatedJob.base_revision).toBe(revision.manifest.revision_id);
  await expect(page.getByRole("heading", {name: "Preview ready", exact: true})).toBeVisible({timeout: 330_000});
  const updatePreviewed = page.waitForResponse(response => response.request().method() === "POST" && new URL(response.url()).pathname.endsWith("/preview"));
  await page.getByRole("button", {name: "Open preview", exact: true}).click();
  expect((await updatePreviewed).status()).toBe(200);
  await expect(frame.getByText("Preview - process controls are read-only.", {exact: true})).toBeVisible({timeout: 25_000});
  await page.screenshot({path: info.outputPath("updated-preview.png"), fullPage: true});
  stage("save focused update");
  await page.getByTestId(commonTab!).click();
  await expect(page.getByRole("button", {name: "Save interface", exact: true})).toBeEnabled({timeout: 15_000});
  const updateSaved = page.waitForResponse(response => response.request().method() === "POST" && new URL(response.url()).pathname.endsWith("/save"));
  await page.getByRole("button", {name: "Save interface", exact: true}).click();
  const updatedSaved = await updateSaved;
  expect(updatedSaved.status()).toBe(200);
  const updatedRevision = await updatedSaved.json();
  expect(updatedRevision.manifest.ui_id).toBe(revision.manifest.ui_id);
  expect(updatedRevision.manifest.revision_id).not.toBe(revision.manifest.revision_id);
  await expect(page.getByRole("heading", {name: "Interface saved", exact: true})).toBeVisible();
  await expect(page.getByRole("combobox", {name: "Saved revision", exact: true})).toHaveValue(updatedRevision.manifest.revision_id);
  await expect.poll(() => page.getByRole("combobox", {name: "Saved revision", exact: true}).locator("option").count()).toBeGreaterThanOrEqual(3);
  await page.getByRole("combobox", {name: "Saved revision", exact: true}).selectOption(revision.manifest.revision_id);
  stage("rollback saved revision");
  await expect(page.getByRole("button", {name: "Use this revision", exact: true})).toBeEnabled();
  const rollback = page.waitForResponse(response => response.request().method() === "POST" && new URL(response.url()).pathname.endsWith("/activate"));
  await page.getByRole("button", {name: "Use this revision", exact: true}).click();
  const activated = await rollback;
  expect(activated.status()).toBe(200);
  expect((await activated.json()).active_revision).toBe(revision.manifest.revision_id);
  await page.screenshot({path: info.outputPath("revision-rollback.png"), fullPage: true});
  expect(requests.some(value => /\/runs$/.test(value.path))).toBe(false);
  expect(errors).toEqual([]);
  const scopePath = info.outputPath("checked-scope.json");
  writeFileSync(scopePath, JSON.stringify({
    job_id: accepted!.job_id, role_resolution: accepted!.role_resolution,
    generation_requested_in_this_browser: !resumeJobId,
    ui_id: revision.manifest.ui_id, revision_id: revision.manifest.revision_id,
    build: presentation.build, previewed_at: revision.previewed_at,
    workspace_chrome_controlled: true, accepted_source: proof.query,
    native_process_authoring: true, actual_configured_model: true,
    actual_compiler: true, actual_managed_worker: true, actual_browser_bootstrap_and_bridge: true,
    saved_interface_reused_without_generation: true, process_execution: false,
    focused_update_job_id: updatedJob.job_id, updated_revision_id: updatedRevision.manifest.revision_id,
    updated_build: updatedRevision.build, rollback_revision_id: revision.manifest.revision_id,
    frame_reload_without_generation: true, theme_observed_in_frame_before_and_after_reload: true,
    live_mcp: false, engineering_verification: false, physical_effect: false, user_acceptance: false,
    requests, errors,
  }, null, 2));
  await info.attach("checked-scope.json", {contentType: "application/json", path: scopePath});
});
