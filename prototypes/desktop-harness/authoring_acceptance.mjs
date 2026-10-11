// Current hosted editor checks, registered in Wright's existing capture harness.
// No route mocks, runs, model calls, or changes to original engineering examples.
import { writeFileSync } from "node:fs";
import path from "node:path";

export function registerDesktopAuthoring({ add, getPage, tid, click, fill, capture, expect, args, root, connect, sourceText, diagnostics, unlock }) {
  let savedSource, savedLayout, originalSource, url, page;
  const input = "block.text-input-1";
  const document = "block.document-1";
  async function addObject(group, template, id) {
    await click(`workflow-recovery-create-group-${group}`);
    await click(`workflow-recovery-create-template-${template}`);
    await expect(tid(`workflow-recovery-block-${id}`)).toBeVisible();
  }
  async function rename(id, name, target = page) {
    await target.getByTestId(`workflow-recovery-block-${id}`).locator("h3").dblclick();
    const field = target.getByTestId(`workflow-recovery-rename-${id}`);
    await field.fill(name); await field.press("Enter");
    await expect(target.getByTestId(`workflow-recovery-block-${id}`)).toContainText(name);
  }
  add("desktop-entry", "Enter through workspace Workflows", "Open the ordinary hosted workspace and click Workflows.", "The current four-group editor opens without Wright chat or agent API calls.", async () => {
    page = getPage();
    await page.goto(args.url); await unlock();
    await page.getByRole("button", { name: /^Workflows?$/ }).click();
    await expect(tid("workflow-recovery-canvas")).toBeVisible({ timeout: 30000 });
    if (args["continue-workflow"]) {
      const selected = new URL(page.url());
      selected.searchParams.set("workflowPath", args["continue-workflow"]);
      await page.goto(selected.href); await expect(tid("workflow-recovery-canvas")).toBeVisible({ timeout: 30000 });
      expect(new URL(page.url()).searchParams.get("workflowPath")).toBe(args["continue-workflow"]);
      if (!args.session) throw new Error("A continuation requires the exact fixture session scope");
      const response = await page.request.get(new URL("/api/workspace/workflow-sources", page.url()).href, { params: { session_id: args.session, path: args["continue-workflow"] } });
      expect(response.ok()).toBe(true);
      const stored = await response.json(); expect(stored.path).toBe(args["continue-workflow"]);
      expect(await sourceText()).toBe(stored.source);
      writeFileSync(path.join(root, "selected-source-readback.json"), JSON.stringify(stored, null, 2));
    }
    await expect(page.locator(".recovery-create-group")).toHaveCount(4);
    for (const group of ["input", "document", "tool", "more"]) await expect(tid(`workflow-recovery-create-group-${group}`)).toBeVisible();
    await expect(tid("agent-sidebar")).toHaveCount(0); await expect(tid("agent-sidebar-toggle")).toHaveCount(0);
    url = page.url(); originalSource = await sourceText();
    savedSource = originalSource;
    writeFileSync(path.join(root, "original-editor-source.wflow"), originalSource);
  });
  add("desktop-text", "Configure a supplied text input", "Create a Text input and enter the supplied inspection dimensions.", "Exact supplied values are authored in the fresh workflow without tool execution.", async () => {
    await addObject("input", "text-input", input);
    await rename(input, "Inspection requirements");
    await fill(`workflow-recovery-input-text-${input}`, "Length 120 mm; width 80 mm; thickness 6 mm; four holes of diameter 8 mm. Hole positions and tolerances remain unspecified.");
    await expect(tid(`workflow-recovery-input-text-${input}`)).toHaveValue(/Length 120 mm/);
  });
  add("desktop-document", "Configure a document step", "Create Engineering document and enter its inspection instructions.", "Document authoring remains available; the task is not executed or represented as engineering acceptance.", async () => {
    await addObject("document", "document", document);
    await rename(document, "Inspection plan");
    await fill(`workflow-recovery-block-instructions-${document}`, "Preserve the supplied dimensions. List unspecified hole locations and tolerances. Do not claim measurement or manufacturing release.");
  });
  add("desktop-connect", "Connect exact typed endpoints", "Connect the text output to the document's text input using keyboard sockets.", "One exact typed connection is retained in the accepted source.", async () => {
    await click("workflow-recovery-inspector-close"); await click("workflow-recovery-canvas-fit");
    await connect("port.text-input-1-text-out", "port.document-1-text-in", "rel.user-text-input-1-text-out-to-document-1-text-in");
  });
  add("desktop-mismatch", "Reject a mismatched connection", "Attempt text output to reference-file input.", "The incompatible connection is rejected without changing accepted semantics.", async () => {
    const digest = await tid("workflow-recovery-concept").getAttribute("data-semantic-digest");
    await tid("workflow-recovery-handle-port.text-input-1-text-out").focus(); await page.keyboard.press("Enter");
    await tid("workflow-recovery-handle-port.document-1-file-in").focus(); await page.keyboard.press("Enter");
    await expect(page.locator(".recovery-keyboard-connection")).toContainText(/type|compatible|accept/i);
    await expect(tid("workflow-recovery-concept")).toHaveAttribute("data-semantic-digest", digest);
    await page.keyboard.press("Escape");
  });
  add("desktop-drag", "Drag, pan and zoom the canvas", "Drag the document, pan empty canvas space and use zoom controls.", "Pointer movement and canvas controls work in the hosted workspace.", async () => {
    const node = tid(`workflow-recovery-block-${document}`);
    const before = await node.boundingBox(); const title = await node.locator("h3").boundingBox();
    expect(title).toBeTruthy();
    await page.mouse.move(title.x + title.width / 2, title.y + title.height / 2); await page.mouse.down();
    await page.mouse.move(title.x + title.width / 2 + 80, title.y + title.height / 2 + 40, { steps: 10 });
    const during = await node.boundingBox(); expect(Math.abs(during.x - before.x)).toBeGreaterThan(20); await page.mouse.up();
    const viewport = page.locator(".react-flow__viewport");
    const transform = await viewport.evaluate(element => element.style.transform);
    await click("workflow-recovery-canvas-zoom-out");
    await expect.poll(() => viewport.evaluate(element => element.style.transform)).not.toBe(transform);
    await click("workflow-recovery-canvas-zoom-in");
    await page.waitForTimeout(400);
    const pane = await page.locator(".react-flow__pane").boundingBox();
    const beforePan = await viewport.evaluate(element => element.style.transform);
    await page.mouse.move(pane.x + 80, pane.y + 150); await page.mouse.down();
    await page.mouse.move(pane.x + 130, pane.y + 175, { steps: 8 }); await page.mouse.up();
    await expect.poll(() => viewport.evaluate(element => element.style.transform)).not.toBe(beforePan);
    writeFileSync(path.join(root, "canvas-pointer-measurements.json"), JSON.stringify({ node_before: before, node_during_drag: during, transform_before_zoom: transform, transform_before_pan: beforePan, transform_after_pan: await viewport.evaluate(element => element.style.transform) }, null, 2));
    await click("workflow-recovery-canvas-fit");
  });
  add("desktop-undo", "Undo and redo a configured edit", "Append a missing-datum instruction, undo and redo.", "Undo restores previous instructions; redo restores the edit without dropping the connection.", async () => {
    await click(`workflow-recovery-block-${document}`);
    const instructions = tid(`workflow-recovery-block-instructions-${document}`);
    const previous = await instructions.inputValue();
    await instructions.fill(previous + " Identify missing datums.");
    await click("workflow-recovery-undo"); await expect(instructions).toHaveValue(previous);
    await click("workflow-recovery-redo"); await expect(instructions).toHaveValue(previous + " Identify missing datums.");
    await expect(tid("workflow-recovery-edge-rel.user-text-input-1-text-out-to-document-1-text-in")).toHaveCount(1);
  });
  add("desktop-save", "Save and reopen accepted source and layout", "Save the current workflow and reload it.", "Exact authored source and layout identity survive; no run is started.", async () => {
    savedSource = await sourceText();
    if (await tid("workflow-recovery-save").isEnabled()) await click("workflow-recovery-save");
    await expect(tid("workflow-recovery-save-status")).toHaveAttribute("aria-label", "Saved in workspace");
    savedLayout = await tid("workflow-recovery-concept").getAttribute("data-layout-digest");
    await page.reload(); await expect(tid("workflow-recovery-canvas")).toBeVisible({ timeout: 30000 });
    expect(await sourceText()).toBe(savedSource);
    await expect(tid("workflow-recovery-concept")).toHaveAttribute("data-layout-digest", savedLayout);
    writeFileSync(path.join(root, "accepted-editor-source.wflow"), savedSource);
    if (await tid("workflow-recovery-inspector").count()) await click("workflow-recovery-inspector-close");
    await capture("desktop-saved-source-and-layout");
  });
  add("desktop-invalid-source", "Contain an invalid Source edit", "Add a counterfeit managed revision in Source, apply, then restore the saved source.", "Invalid source remains a draft; accepted semantics and the saved document are retained.", async () => {
    const digest = await tid("workflow-recovery-concept").getAttribute("data-semantic-digest");
    await click("workflow-recovery-view-code");
    const invalid = savedSource.replace(/^(workflow [^\n]+\n)/m, "$1  revision: 999\n");
    expect(invalid).not.toBe(savedSource);
    await fill("workflow-recovery-source-editor", invalid);
    await click("workflow-recovery-source-apply");
    await expect(page.locator(".recovery-diagnostics")).toContainText("WFR-SOURCE-FIELD-MANAGED");
    await expect(tid("workflow-recovery-concept")).toHaveAttribute("data-semantic-digest", digest);
    await fill("workflow-recovery-source-editor", savedSource); await click("workflow-recovery-source-apply");
    await expect(page.locator(".recovery-diagnostics")).toHaveCount(0);
    await click("workflow-recovery-view-diagram");
  });
  add("desktop-cas", "Protect a stale editor save", "Open the same workflow in another tab, save a name change, and attempt a conflicting original-tab change.", "A real save conflict retains local work; explicit comparison and reload reconcile the newer document.", async () => {
    const other = await page.context().newPage();
    try {
      await other.goto(page.url()); await expect(other.getByTestId("workflow-recovery-canvas")).toBeVisible({ timeout: 30000 });
      await rename(document, "Inspection plan stored update", other);
      await other.getByTestId("workflow-recovery-save").click();
      await expect(other.getByTestId("workflow-recovery-save-status")).toHaveAttribute("aria-label", "Saved in workspace");
      await rename(document, "Inspection plan local draft"); await click("workflow-recovery-save");
      await expect(tid("workflow-recovery-conflict-actions")).toBeVisible();
      await click("workflow-recovery-conflict-compare");
      await expect(tid("workflow-recovery-source-comparison-local")).toHaveValue(/Inspection plan local draft/);
      await expect(tid("workflow-recovery-source-comparison-stored")).toHaveValue(/Inspection plan stored update/);
      await capture("desktop-protected-save-conflict");
      await click("workflow-recovery-modal-close"); await click("workflow-recovery-conflict-reload"); await click("workflow-recovery-conflict-reload-confirm");
      await expect(tid(`workflow-recovery-block-${document}`)).toContainText("Inspection plan stored update");
      await expect(tid("workflow-recovery-conflict-actions")).toHaveCount(0);
    } finally { await other.close(); }
  });
  add("desktop-compact", "Inspect compact hosted layout", "Resize to 768 by 512 and open/close the Create menu.", "Editor controls remain reachable with no Wright chat and no page overflow.", async () => {
    await page.setViewportSize({ width: 768, height: 512 });
    await click("workflow-recovery-create-group-input"); await expect(page.locator(".recovery-create-popover")).toBeVisible(); await page.keyboard.press("Escape");
    const size = await page.evaluate(() => ({ width: innerWidth, height: innerHeight, scrollWidth: document.documentElement.scrollWidth, scrollHeight: document.documentElement.scrollHeight }));
    expect(size.scrollWidth).toBeLessThanOrEqual(size.width + 1); expect(size.scrollHeight).toBeLessThanOrEqual(size.height + 1);
    await page.setViewportSize({ width: 1537, height: 791 });
    const forbidden = diagnostics.apiRequests.filter(item => /^\/api\/(agent|inference)/.test(item.path) || /process-interfaces\/runs/.test(item.path));
    expect(forbidden).toEqual([]);
    writeFileSync(path.join(root, "hosted-authoring-boundary.json"), JSON.stringify({ url, scope: "current browser authoring; installed desktop and full legacy acceptance separate", original_source_preserved_in_report: true, saved_layout_digest: savedLayout, requests: diagnostics.apiRequests, forbidden_requests: forbidden, no_engineering_runs: true }, null, 2));
  });
}
