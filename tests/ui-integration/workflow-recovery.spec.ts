import { expect, test } from "@playwright/test";
import AxeBuilder from "@axe-core/playwright";

import {
  mockRecoveryWorkspace,
  openRecoveryEditor,
  publicWorkflowSource,
} from "./fixtures/workflow-recovery";

test("automatically creates the default workflow when Workflows is opened", async ({ page }) => {
  const state = await mockRecoveryWorkspace(page, { source: null });
  await openRecoveryEditor(page);

  await expect(page.getByTestId("workflow-recovery-concept")).toBeVisible();
  await expect(page.getByTestId("workflow-recovery-filebar")).toContainText("mounting-bracket.workflow.wflow · Saved in workspace");
  await expect(page.getByTestId("workflow-source-missing")).toHaveCount(0);
  await expect(page.getByTestId("workflow-source-create")).toHaveCount(0);
  expect(state.missingReadCount()).toBe(1);
  expect(state.createCount()).toBe(1);
  expect(state.current()?.source).toBe(publicWorkflowSource);
});

test("loads and saves the workspace workflow with its current CAS identity", async ({ page }) => {
  const state = await mockRecoveryWorkspace(page);
  await openRecoveryEditor(page);

  await page.getByTestId("workflow-recovery-block-block.generate-geometry").click();
  await page.getByLabel("Thickness (mm)").fill("8");
  await page.getByTestId("workflow-recovery-config-apply").click();
  await expect(page.getByTestId("workflow-recovery-filebar")).toContainText("Unsaved changes");
  await page.getByTestId("workflow-recovery-save").click();

  await expect(page.getByTestId("workflow-recovery-save-status")).toContainText("Saved in workspace");
  expect(state.updateCount()).toBe(1);
  expect(state.current()?.storage_revision).toBe(2);
  expect(state.current()?.definition_revision).toBe(3);
  expect(state.current()?.source).toContain('settings: {"inside_radius_mm":4,"thickness_mm":8}');
});

test("binds decision and revision edges to explicit typed routing handles", async ({ page }) => {
  const missingHandleDiagnostics: string[] = [];
  page.on("console", (message) => {
    if (message.text().includes("Couldn't create edge for") && message.text().includes("handle id")) {
      missingHandleDiagnostics.push(message.text());
    }
  });
  await mockRecoveryWorkspace(page);
  await openRecoveryEditor(page);

  const revisionEdge = page.getByTestId("workflow-recovery-edge-rel.specification-revise");
  await expect(revisionEdge).toBeVisible();
  await expect(revisionEdge).toHaveAttribute(
    "data-source-handle",
    "routing.feedback.source.block.create-design-specification",
  );
  await expect(revisionEdge).toHaveAttribute(
    "data-target-handle",
    "routing.feedback.target.block.design-intent",
  );
  await expect(page.getByTestId("workflow-recovery-routing-handle-feedback-source-block.create-design-specification"))
    .toHaveAttribute("data-handleid", "routing.feedback.source.block.create-design-specification");
  await expect(page.getByTestId("workflow-recovery-routing-handle-feedback-target-block.design-intent"))
    .toHaveAttribute("data-handleid", "routing.feedback.target.block.design-intent");

  const decisionEdge = page.getByTestId("workflow-recovery-edge-rel.specification-accepted");
  await expect(decisionEdge).toBeVisible();
  await expect(decisionEdge).toHaveAttribute(
    "data-source-handle",
    "routing.flow.source.block.create-design-specification",
  );
  await expect(decisionEdge).toHaveAttribute(
    "data-target-handle",
    "routing.flow.target.block.generate-geometry",
  );
  expect(missingHandleDiagnostics).toEqual([]);
});

test("keeps the engineer's local edit visible when a CAS save conflicts", async ({ page }) => {
  const state = await mockRecoveryWorkspace(page);
  await openRecoveryEditor(page);

  await page.getByTestId("workflow-recovery-view-code").click();
  const editor = page.getByTestId("workflow-recovery-source-editor");
  await editor.fill((await editor.inputValue()).replace("Create bracket CAD model", "Create bracket CAD model locally"));
  await page.getByTestId("workflow-recovery-source-apply").click();
  state.conflictNextUpdate();
  await page.getByTestId("workflow-recovery-save").click();

  await expect(page.getByTestId("workflow-recovery-save-status")).toContainText("changed elsewhere");
  await expect(page.getByTestId("workflow-recovery-save-status")).toContainText("local edits are still here");
  await expect(page.getByTestId("workflow-recovery-filebar")).toContainText("Unsaved changes");
  await expect(editor).toHaveValue(/Create bracket CAD model locally/);
  expect(state.updateCount()).toBe(1);
  expect(state.current()?.source).toBe(publicWorkflowSource);
});

test("keeps the recovery editor bounded and three-column at 1070 by 791", async ({ page }) => {
  await mockRecoveryWorkspace(page);
  await openRecoveryEditor(page);
  await page.setViewportSize({ width: 1070, height: 791 });
  const surfacePane = page.getByTestId("workspace-pane-surface");
  if (await surfacePane.isVisible()) await surfacePane.click();

  await expect(page.locator(".app-sidebar")).toHaveCount(0);

  const palette = page.getByTestId("workflow-recovery-palette");
  const canvas = page.getByTestId("workflow-recovery-canvas");
  const inspector = page.getByTestId("workflow-recovery-inspector");
  const [paletteBox, canvasBox, inspectorBox] = await Promise.all([
    palette.boundingBox(),
    canvas.boundingBox(),
    inspector.boundingBox(),
  ]);

  expect(paletteBox).not.toBeNull();
  expect(canvasBox).not.toBeNull();
  expect(inspectorBox).not.toBeNull();
  expect(paletteBox!.y).toBe(inspectorBox!.y);
  expect(paletteBox!.x + paletteBox!.width).toBeLessThanOrEqual(canvasBox!.x + 1);
  expect(canvasBox!.x + canvasBox!.width).toBeLessThanOrEqual(inspectorBox!.x + 1);
  expect(canvasBox!.width).toBeGreaterThanOrEqual(500);
  expect(inspectorBox!.y + inspectorBox!.height).toBeLessThanOrEqual(791);

  const overflow = await page.evaluate(() => {
    const select = (selector: string) => document.querySelector<HTMLElement>(selector)!;
    const metric = (element: HTMLElement) => ({
      clientHeight: element.clientHeight,
      scrollHeight: element.scrollHeight,
      overflowY: getComputedStyle(element).overflowY,
    });
    return {
      document: metric(document.documentElement),
      body: metric(document.body),
      main: metric(select(".app-shell__main")),
      workspace: metric(select('[data-testid="workspace-panel"]')),
      page: metric(select('[data-testid="page-workflow-recovery"]')),
      concept: metric(select('[data-testid="workflow-recovery-concept"]')),
      workbench: metric(select(".recovery-workbench")),
      palette: metric(select('[data-testid="workflow-recovery-palette"]')),
      inspector: metric(select('[data-testid="workflow-recovery-inspector"]')),
    };
  });

  for (const container of [overflow.document, overflow.body, overflow.main, overflow.workspace, overflow.page, overflow.concept, overflow.workbench]) {
    expect(container.scrollHeight).toBeLessThanOrEqual(container.clientHeight);
  }
  expect(overflow.workspace.overflowY).toBe("hidden");
  expect(overflow.palette.overflowY).toBe("auto");
  expect(overflow.inspector.overflowY).toBe("auto");
  expect(overflow.palette.scrollHeight).toBeGreaterThan(overflow.palette.clientHeight);
});

test("expands a reusable component without adding search clutter to a small graph", async ({ page }) => {
  await mockRecoveryWorkspace(page);
  await openRecoveryEditor(page);

  const concept = page.getByTestId("workflow-recovery-concept");
  const revision = await concept.getAttribute("data-revision");
  const digest = await concept.getAttribute("data-semantic-digest");
  const component = page.getByTestId("workflow-recovery-block-block.review-design");
  await expect(component).toHaveAttribute("data-component-collapsed", "true");
  await expect(component).toContainText("Grouped review step · 4 technical items");
  await expect(component).toContainText("1 review item needs attention");
  await expect(page.getByTestId("workflow-recovery-component-addresses-block.review-design")).toHaveCount(0);

  await page.getByTestId("workflow-recovery-component-toggle-block.review-design").click();
  await expect(component).toHaveAttribute("data-component-collapsed", "false");
  await expect(page.getByTestId("workflow-recovery-component-addresses-block.review-design"))
    .toContainText("Accept the reviewed design");

  await expect(page.getByTestId("workflow-recovery-find-input")).toHaveCount(0);
  await page.getByTestId("workflow-recovery-block-block.export-step").click();
  await expect(page.getByTestId("workflow-recovery-inspector")).toContainText("Export approved STEP file");
  await expect(concept).toHaveAttribute("data-revision", revision ?? "2");
  await expect(concept).toHaveAttribute("data-semantic-digest", digest ?? "");
});

test("keeps overlapping edge labels behind blocks without losing keyboard edge selection", async ({ page }) => {
  await mockRecoveryWorkspace(page);
  await openRecoveryEditor(page);

  const edgeLabel = page.getByTestId("workflow-recovery-edge-select-rel.report-to-review");
  await edgeLabel.focus();
  await edgeLabel.press("Enter");
  await expect(page.getByTestId("workflow-recovery-disconnect-rel.report-to-review")).toBeVisible();

  const manufacturingNode = page.getByTestId("workflow-recovery-block-block.check-manufacturability");
  await manufacturingNode.click();
  await expect(manufacturingNode).toHaveAttribute("data-selected", "true");
  await expect(page.getByTestId("workflow-recovery-inspector")).toContainText("Run manufacturing checks");
});

test("keeps one accepted definition across canvas, source, AI review, and simulation", async ({ page }) => {
  await mockRecoveryWorkspace(page);
  await openRecoveryEditor(page);

  const concept = page.getByTestId("workflow-recovery-concept");
  await expect(concept).toBeVisible();
  await expect(page.getByTestId("workflow-recovery-canvas")).toBeVisible();
  await expect(concept).toHaveAttribute("data-revision", "2");
  await expect(page.getByText("PROVISIONAL · NOT PRODUCTION")).toBeVisible();
  await expect(page.getByText("SIMULATION", { exact: true })).toBeVisible();
  const filebar = page.getByTestId("workflow-recovery-filebar");
  await expect(filebar).toContainText("mounting-bracket.workflow.wflow · Saved in workspace");
  expect((await filebar.boundingBox())?.height).toBeLessThanOrEqual(72);
  await expect(page.getByText(/Build and review the work as a diagram/)).toHaveCount(0);
  await expect(page.locator(".react-flow__node")).toHaveCount(9);
  await expect(page.getByTestId("workflow-recovery-input-source-reference-images")).toContainText("Engineer upload");
  await expect(page.getByTestId("workflow-recovery-attachment-artifact.design-intent")).toContainText("Typed text or common document");
  await expect(page.getByTestId("workflow-recovery-input-source-company-context")).toContainText("Company knowledge library");
  await expect(page.getByTestId("workflow-recovery-block-block.create-design-specification")).toContainText("Create and review design specification");
  await expect(page.getByTestId("workflow-recovery-palette-context-hint")).toContainText("Tolerances come from the reviewed design specification");
  await expect(page.getByTestId("workflow-recovery-palette-search")).toHaveCount(0);

  const designSpecification = page.getByTestId("workflow-recovery-block-block.create-design-specification");
  await designSpecification.focus();
  await designSpecification.press("Enter");
  await expect(page.getByTestId("workflow-recovery-inspector")).toContainText("AI drafts; engineer reviews");
  await expect(page.getByTestId("workflow-recovery-inspector")).toContainText("AI prompt");
  await expect(page.getByTestId("workflow-recovery-inspector")).toContainText("Engineer approval checklist");
  await page.getByTestId("workflow-recovery-block-review-toggle-block.create-design-specification").click();
  await expect(page.getByTestId("workflow-recovery-block-review-block.create-design-specification")).toHaveValue(/Accept when: An engineer accepted the design specification/);
  await expect(page.getByTestId("workflow-recovery-inspector")).toContainText("These criteria come from this step's accept and revise paths");

  await page.getByRole("button", { name: "Connection style preview" }).click();
  await expect(page.getByTestId("workflow-port-lab-dot")).toBeVisible();
  await expect(page.getByTestId("workflow-port-lab-terminal")).toBeVisible();
  await expect(page.getByTestId("workflow-port-lab-hybrid")).toHaveClass(/is-selected/);
  await page.getByRole("button", { name: "dot connect socket" }).click();
  await expect(page.getByTestId("workflow-port-lab-dot")).toContainText("Connection started");
  await page.getByRole("button", { name: "dot open CAD model" }).click();
  await expect(page.getByTestId("workflow-port-lab-dot")).toContainText("Approved CAD model opened separately");
  await page.getByTestId("workflow-port-lab-terminal").getByRole("button", { name: "Use this style" }).click();
  await expect(page.getByTestId("workflow-recovery-canvas")).toHaveAttribute("data-port-treatment", "terminal");
  await page.getByRole("button", { name: "Close dialog" }).click();

  await page.getByTestId("workflow-recovery-block-block.generate-geometry").click();
  await expect(page.getByTestId("workflow-recovery-palette-search")).toHaveCount(0);
  await page.getByTestId("workflow-recovery-palette-item-tolerance").click();
  await expect(concept).toHaveAttribute("data-revision", "3");
  await expect(page.getByTestId("workflow-recovery-block-block.tolerance-1")).toBeVisible();
  await page.getByTestId("workflow-recovery-undo").click();
  await expect(concept).toHaveAttribute("data-revision", "4");
  await expect(page.getByTestId("workflow-recovery-block-block.tolerance-1")).toHaveCount(0);
  await page.getByTestId("workflow-recovery-redo").click();
  await expect(concept).toHaveAttribute("data-revision", "5");
  await expect(page.getByTestId("workflow-recovery-block-block.tolerance-1")).toBeVisible();
  await page.getByTestId("workflow-recovery-block-block.tolerance-1").click();
  await page.getByTestId("workflow-recovery-delete").click();
  await expect(concept).toHaveAttribute("data-revision", "6");
  await expect(page.getByTestId("workflow-recovery-block-block.tolerance-1")).toHaveCount(0);

  await expect(page.getByTestId("workflow-recovery-attachment-artifact.design-intent")).toContainText("Not added yet");
  await expect(page.getByTestId("workflow-recovery-run-start")).toBeDisabled();
  await page.getByTestId("workflow-recovery-attachment-attach-artifact.design-intent").click();
  await expect(page.getByTestId("workflow-recovery-attachment-artifact.design-intent")).toContainText("mounting-bracket-design-intent.docx");
  await page.getByTestId("workflow-recovery-attachment-preview-artifact.design-intent").click();
  await expect(page.getByRole("heading", { name: "Wall-mounted equipment bracket" })).toBeVisible();
  await page.getByRole("button", { name: "Close dialog" }).click();
  await page.getByTestId("workflow-recovery-attachment-replace-artifact.design-intent").click();
  await expect(page.getByTestId("workflow-recovery-attachment-artifact.design-intent")).toContainText("mounting-bracket-design-intent.txt");
  await expect(concept).toHaveAttribute("data-revision", "6");

  await page.getByTestId("workflow-recovery-block-block.generate-geometry").click();
  await page.getByLabel("Thickness (mm)").fill("8");
  await page.getByTestId("workflow-recovery-config-apply").click();
  await expect(concept).toHaveAttribute("data-revision", "7");
  await page.getByTestId("workflow-recovery-edge-select-rel.review-revise").click();
  await page.getByLabel("Condition or reason").fill("A requirement or manufacturability warning requires revision");
  await page.getByTestId("workflow-recovery-relationship-apply-rel.review-revise").click();
  await expect(concept).toHaveAttribute("data-revision", "8");
  await page.getByTestId("workflow-recovery-block-block.generate-geometry").click();

  await page.getByTestId("workflow-recovery-view-split").click();
  const synchronizedSource = page.getByTestId("workflow-recovery-source-editor");
  await expect(synchronizedSource).toHaveValue(/thickness_mm/);
  const graphSelection = await synchronizedSource.evaluate((element) => {
    const editor = element as HTMLTextAreaElement;
    return editor.value.slice(editor.selectionStart, editor.selectionEnd);
  });
  expect(graphSelection).toContain("task generate_geometry");
  await synchronizedSource.evaluate((element) => {
    const editor = element as HTMLTextAreaElement;
    const offset = editor.value.indexOf("task export_step") + 8;
    editor.focus();
    editor.setSelectionRange(offset, offset);
  });
  await synchronizedSource.press("ArrowRight");
  await expect(page.getByTestId("workflow-recovery-inspector")).toContainText("Export approved STEP file");
  const revisionBeforeInvalid = await concept.getAttribute("data-revision");
  const source = synchronizedSource;
  await source.fill("workflow mounting_bracket\n  revision: 99\nend\n");
  await page.getByTestId("workflow-recovery-source-apply").click();
  await expect(page.getByTestId("workflow-recovery-diagnostic-WFR-SOURCE-FIELD-MANAGED")).toBeVisible();
  await expect(concept).toHaveAttribute("data-revision", revisionBeforeInvalid ?? "8");
  await expect(page.getByTestId("workflow-recovery-run-start")).toBeDisabled();
});

test("uses real typed handles and preserves revision during a simulated run", async ({ page }) => {
  const canvasDiagnostics: string[] = [];
  const recordCanvasDiagnostic = (text: string) => {
    if (
      text.includes("trying to drag a node that is not initialized")
      || text.includes("Couldn't create edge for")
      || text.includes("ResizeObserver loop")
    ) {
      canvasDiagnostics.push(text);
    }
  };
  page.on("console", (message) => recordCanvasDiagnostic(`console ${message.type()}: ${message.text()}`));
  page.on("pageerror", (error) => recordCanvasDiagnostic(`pageerror: ${error.message}`));
  await mockRecoveryWorkspace(page);
  await openRecoveryEditor(page);
  const concept = page.getByTestId("workflow-recovery-concept");

  await expect(concept).toHaveAttribute("data-semantic-digest", /^sha256:[a-f0-9]{64}$/);
  await expect(concept).toHaveAttribute("data-layout-digest", /^sha256:[a-f0-9]{64}$/);
  await page.getByTestId("workflow-recovery-attachment-attach-artifact.design-intent").click();
  const semanticBeforeDrag = await concept.getAttribute("data-semantic-digest");
  const layoutBeforeDrag = await concept.getAttribute("data-layout-digest");
  const draggable = page.locator('.react-flow__node[data-id="block.generate-geometry"]');
  const dragBox = await draggable.boundingBox();
  expect(dragBox).not.toBeNull();
  await page.mouse.move(dragBox!.x + dragBox!.width / 2, dragBox!.y + 45);
  await page.mouse.down();
  await page.mouse.move(dragBox!.x + dragBox!.width / 2 + 80, dragBox!.y + 75, { steps: 10 });
  await expect.poll(async () => (await draggable.boundingBox())?.x ?? dragBox!.x).toBeGreaterThan(dragBox!.x + 40);
  await expect(concept).toHaveAttribute("data-revision", "2");
  await expect(concept).toHaveAttribute("data-semantic-digest", semanticBeforeDrag!);
  await expect(concept).toHaveAttribute("data-layout-digest", layoutBeforeDrag!);
  await page.mouse.up();
  await expect(concept).toHaveAttribute("data-revision", "2");
  await expect(concept).toHaveAttribute("data-semantic-digest", semanticBeforeDrag!);
  await expect.poll(() => concept.getAttribute("data-layout-digest")).not.toBe(layoutBeforeDrag);
  await page.waitForTimeout(100);
  expect(canvasDiagnostics).toEqual([]);

  const revision = await concept.getAttribute("data-revision");
  await page.getByTestId("workflow-recovery-run-start").click();
  await expect(page.getByTestId("workflow-recovery-run-mode")).toContainText("Workflow version 2 · waiting");
  await page.getByTestId("workflow-recovery-run-advance").click();
  await expect(page.getByTestId("workflow-recovery-block-block.create-design-specification")).toHaveAttribute("data-active", "true");
  await expect(page.getByTestId("workflow-recovery-edge-select-rel.design-intent-to-specification")).toContainText("Active flow");
  await expect(concept).toHaveAttribute("data-revision", revision ?? "2");

  await page.reload();
  await expect(concept).toHaveAttribute("data-revision", "2");
  const exportNode = page.locator('.react-flow__node[data-id="block.export-step"]');
  await exportNode.focus();
  await exportNode.press("Enter");
  await expect(page.getByTestId("workflow-recovery-inspector")).toContainText("Export approved STEP file");

  await page.getByTestId("workflow-recovery-edge-select-rel.review-to-export").click();
  await expect(page.getByTestId("workflow-recovery-disconnect-rel.review-to-export")).toBeVisible();
  await page.getByTestId("workflow-recovery-disconnect-rel.review-to-export").click();
  await expect(concept).toHaveAttribute("data-revision", "3");

  const sourceHandle = page.getByTestId("workflow-recovery-handle-port.approved-geometry-out");
  const targetHandle = page.getByTestId("workflow-recovery-handle-port.approved-geometry-in");
  // Move the non-semantic overview out of pointer hit-testing so this case targets the typed sockets.
  await page.locator(".react-flow__minimap").evaluate((element) => {
    (element as HTMLElement).style.pointerEvents = "none";
  });
  await sourceHandle.dragTo(targetHandle);
  await expect(page.getByTestId("workflow-recovery-edge-rel.review-to-export")).toBeVisible();
  await expect(concept).toHaveAttribute("data-revision", "4");

  await page.getByTestId("workflow-recovery-edge-select-rel.review-to-export").click();
  await page.getByTestId("workflow-recovery-disconnect-rel.review-to-export").click();
  await expect(concept).toHaveAttribute("data-revision", "5");
  await sourceHandle.focus();
  await sourceHandle.press("Enter");
  await expect(page.getByRole("status").filter({ hasText: "Connection started" })).toContainText("Connection started");
  await targetHandle.focus();
  await targetHandle.press("Enter");
  await expect(page.getByTestId("workflow-recovery-edge-rel.review-to-export")).toBeVisible();
  await expect(concept).toHaveAttribute("data-revision", "6");
});

test("promotes valid source and reviewed AI commands, recovers a run, and exposes lineage", async ({ page }) => {
  await mockRecoveryWorkspace(page);
  await openRecoveryEditor(page);
  const concept = page.getByTestId("workflow-recovery-concept");
  await page.getByTestId("workflow-recovery-attachment-attach-artifact.design-intent").click();

  await page.getByTestId("workflow-recovery-view-code").click();
  const editor = page.getByTestId("workflow-recovery-source-editor");
  const source = await editor.inputValue();
  expect(source).toContain("Create bracket CAD model");
  await editor.fill(source.replace("Create bracket CAD model", "Create bracket CAD model v2"));
  await page.getByTestId("workflow-recovery-source-apply").click();
  await expect(concept).toHaveAttribute("data-revision", "3");
  await page.getByTestId("workflow-recovery-view-diagram").click();
  await expect(page.getByTestId("workflow-recovery-block-block.generate-geometry")).toContainText("Create bracket CAD model v2");

  await page.getByTestId("workflow-recovery-ai-request").click();
  await expect(page.getByTestId("workflow-recovery-proposal")).toHaveAttribute("data-base-revision", "3");
  await expect(page.getByTestId("workflow-recovery-proposal-preview")).toContainText("Create manufacturing drawing");
  await page.getByTestId("workflow-recovery-proposal-reject").click();
  await expect(concept).toHaveAttribute("data-revision", "3");
  await expect(page.getByTestId("workflow-recovery-block-block.create-inspection-drawing")).toHaveCount(0);

  await page.getByTestId("workflow-recovery-ai-request").click();
  await page.getByTestId("workflow-recovery-block-block.create-inspection-drawing").click();
  await expect(page.getByTestId("workflow-recovery-candidate-readonly")).toBeVisible();
  await page.getByTestId("workflow-recovery-proposal-accept").click();
  await expect(concept).toHaveAttribute("data-revision", "4");
  await expect(page.getByTestId("workflow-recovery-block-block.create-inspection-drawing")).toBeAttached();
  await expect(page.getByTestId("workflow-recovery-block-block.review-inspection-drawing")).toBeAttached();
  await expect(page.getByTestId("workflow-recovery-simulation-issue")).toContainText("nine-step mounting-bracket example");
  await expect(page.getByTestId("workflow-recovery-run-start")).toBeDisabled();
  await page.getByTestId("workflow-recovery-undo").click();
  await expect(concept).toHaveAttribute("data-revision", "5");
  await expect(page.getByTestId("workflow-recovery-block-block.create-inspection-drawing")).toHaveCount(0);
  await expect(page.getByTestId("workflow-recovery-simulation-issue")).toContainText("exact mounting-bracket fixture facts");
  await page.getByTestId("workflow-recovery-undo").click();
  await expect(concept).toHaveAttribute("data-revision", "6");
  await expect(page.getByTestId("workflow-recovery-block-block.generate-geometry")).toContainText("Create bracket CAD model");

  await page.getByTestId("workflow-recovery-run-start").click();
  await expect(page.getByTestId("workflow-recovery-run-mode")).toContainText("Workflow version 2 · waiting");
  await page.getByTestId("workflow-recovery-run-advance").click();
  await page.getByTestId("workflow-recovery-run-advance").click();
  await expect(page.getByTestId("workflow-recovery-run-mode")).toContainText("Workflow version 2 · needs input");
  await expect(page.getByTestId("workflow-recovery-block-block.review-design")).toHaveAttribute("data-run-state", "blocked");
  await page.getByTestId("workflow-recovery-run-recover").click();
  await expect(page.getByTestId("workflow-recovery-run-mode")).toContainText("running");
  for (let index = 0; index < 6; index += 1) {
    await page.getByTestId("workflow-recovery-run-advance").click();
  }
  await expect(page.getByTestId("workflow-recovery-run-mode")).toContainText("Workflow version 2 · complete");
  await expect(concept).toHaveAttribute("data-revision", "6");

  await page.getByTestId("workflow-recovery-block-block.export-step").click();
  await page.getByTestId("workflow-recovery-inspector-tab-outputs").click();
  await page.getByTestId("workflow-recovery-output-artifact.step").click();
  await expect(page.getByRole("heading", { name: "Mounting bracket STEP file" })).toBeVisible();
  await expect(page.getByAltText("Isometric L-shaped mounting bracket with four holes")).toBeVisible();
  await expect(page.getByText(/^Demo STEP file\./)).toBeVisible();
  await expect(page.getByText(/File sha256:bf316fa511f5e6a3312f03cb5b36184d91109185730defc41542b8805884be83/)).toBeVisible();
  await expect(page.getByTestId("workflow-recovery-output-lineage")).toContainText("Design intent + reference images + company standards and context");
  const reportPromise = page.waitForEvent("popup");
  await page.getByTestId("workflow-recovery-output-open-artifact.step").click();
  const report = await reportPromise;
  await report.waitForLoadState();
  await expect(report).toHaveTitle("Simulated manufacturability report");
  await report.close();
  const downloadPromise = page.waitForEvent("download");
  await page.getByTestId("workflow-recovery-output-download-artifact.step").click();
  const download = await downloadPromise;
  expect(download.suggestedFilename()).toBe("mounting-bracket-simulated-fixture.step");
  await page.getByRole("button", { name: "Close dialog" }).click();
  await page.getByTestId("workflow-recovery-run-project-failed").click();
  await page.getByTestId("workflow-recovery-block-block.export-step").click();
  await page.getByTestId("workflow-recovery-inspector-tab-outputs").click();
  await expect(page.getByTestId("workflow-recovery-output-artifact.step")).toHaveCount(0);
  await expect(page.getByTestId("workflow-recovery-block-block.release-package")).toHaveAttribute("data-run-state", "blocked");
  await expect(concept).toHaveAttribute("data-revision", "6");
});

test("keeps paired edits and the run overlay inside the local one-second feedback bound", async ({ page }) => {
  await mockRecoveryWorkspace(page);
  await openRecoveryEditor(page);
  await page.getByTestId("workflow-recovery-attachment-attach-artifact.design-intent").click();
  await page.getByTestId("workflow-recovery-view-split").click();
  const source = page.getByTestId("workflow-recovery-source-editor");

  await page.getByTestId("workflow-recovery-block-block.generate-geometry").click();
  await page.getByTestId("workflow-recovery-block-thickness-block.generate-geometry").fill("8");
  const graphStarted = Date.now();
  await page.getByTestId("workflow-recovery-config-apply").click();
  await expect(source).toHaveValue(/"thickness_mm":8/, { timeout: 1000 });
  const graphToTextMs = Date.now() - graphStarted;
  expect(graphToTextMs).toBeLessThan(1000);

  const current = await source.inputValue();
  await source.fill(current.replace("Create bracket CAD model", "Create bracket CAD model paired"));
  const textStarted = Date.now();
  await page.getByTestId("workflow-recovery-source-apply").click();
  await expect(page.getByTestId("workflow-recovery-block-block.generate-geometry")).toContainText("Create bracket CAD model paired", { timeout: 1000 });
  const textToGraphMs = Date.now() - textStarted;
  expect(textToGraphMs).toBeLessThan(1000);

  await page.getByTestId("workflow-recovery-undo").click();
  await page.getByTestId("workflow-recovery-undo").click();
  await page.getByTestId("workflow-recovery-run-start").click();
  const overlayStarted = Date.now();
  await page.getByTestId("workflow-recovery-run-advance").click();
  await expect(page.getByTestId("workflow-recovery-block-block.create-design-specification")).toHaveAttribute("data-active", "true", { timeout: 1000 });
  const runOverlayMs = Date.now() - overlayStarted;
  expect(runOverlayMs).toBeLessThan(1000);

  test.info().annotations.push({ type: "latency", description: `graph→text=${graphToTextMs}ms; text→graph=${textToGraphMs}ms; run-overlay=${runOverlayMs}ms; bound<1000ms` });
});

test("keeps concept states accessible, reduced-motion legible, and mobile-contained", async ({ page }) => {
  await page.emulateMedia({ reducedMotion: "reduce" });
  await mockRecoveryWorkspace(page);
  await openRecoveryEditor(page);
  await expect(page.getByTestId("workflow-recovery-concept")).toBeVisible();
  await page.getByTestId("workflow-recovery-attachment-attach-artifact.design-intent").click();

  const serious = async () => (await new AxeBuilder({ page }).include('[data-testid="workflow-recovery-concept"]').analyze())
    .violations.filter((violation) => violation.impact === "serious" || violation.impact === "critical")
    .map((violation) => ({
      id: violation.id,
      targets: violation.nodes.flatMap((node) => node.target.map(String)),
    }));
  expect(await serious()).toEqual([]);

  await page.getByRole("button", { name: "Connection style preview" }).click();
  expect(await serious()).toEqual([]);
  await page.getByRole("button", { name: "Close dialog" }).click();

  await page.getByTestId("workflow-recovery-run-start").click();
  await page.getByTestId("workflow-recovery-run-advance").click();
  const activeEdge = page.getByTestId("workflow-recovery-edge-rel.design-intent-to-specification");
  await expect(activeEdge).toHaveAttribute("data-active", "true");
  const animationDuration = await activeEdge.locator("path.react-flow__edge-path").evaluate((element) => getComputedStyle(element).animationDuration);
  expect(["0s", "0.000001s", "1e-06s"]).toContain(animationDuration);
  await expect(page.getByTestId("workflow-recovery-edge-select-rel.design-intent-to-specification")).toContainText("Active flow");

  await page.setViewportSize({ width: 390, height: 844 });
  await page.reload();
  await page.getByTestId("workspace-pane-surface").click();
  await expect(page.getByTestId("workflow-recovery-concept")).toBeVisible();
  const overflow = await page.evaluate(() => ({ width: document.documentElement.scrollWidth, viewport: document.documentElement.clientWidth }));
  expect(overflow.width).toBeLessThanOrEqual(overflow.viewport);
  await expect(page.getByTestId("workflow-recovery-palette")).toBeVisible();
  await expect(page.getByTestId("workflow-recovery-inspector")).toBeVisible();
});
