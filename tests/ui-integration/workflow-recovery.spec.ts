import { expect, test, type Page } from "@playwright/test";
import AxeBuilder from "@axe-core/playwright";

import {
  mockRecoveryWorkspace,
  openRecoveryEditor,
  publicWorkflowSource,
} from "./fixtures/workflow-recovery";

async function selectObject(page: Page, id: string): Promise<void> {
  // Keyboard selection remains available when the compact graph is zoomed out.
  const object = page.getByTestId(`workflow-recovery-block-${id}`);
  await object.focus();
  await object.press("Enter");
  await expect(page.getByTestId("workflow-recovery-inspector")).toBeVisible();
}

async function editObject(page: Page, id: string): Promise<void> {
  await selectObject(page, id);
}

async function editThickness(page: Page): Promise<void> {
  await editObject(page, "block.generate-geometry");
  await page
    .getByTestId("workflow-recovery-settings-advanced-block.generate-geometry")
    .click();
}

async function closeInspector(page: Page): Promise<void> {
  const close = page.getByTestId("workflow-recovery-inspector-close");
  if (await close.isVisible()) await close.click();
}

test("automatically creates the default workflow when Workflows is opened", async ({
  page,
}) => {
  const state = await mockRecoveryWorkspace(page, { source: null });
  await openRecoveryEditor(page);

  await expect(page.getByTestId("workflow-recovery-concept")).toBeVisible();
  await expect(page.getByTestId("workflow-recovery-filebar")).toContainText(
    "Mounting bracket development",
  );
  await expect(
    page.getByTestId("workflow-recovery-block-binding-block.generate-geometry"),
  ).toBeVisible();
  await expect(page.getByTestId("workflow-recovery-save-status")).toContainText(
    "Saved",
  );
  await expect(page.getByTestId("workflow-source-missing")).toHaveCount(0);
  await expect(page.getByTestId("workflow-source-create")).toHaveCount(0);
  expect(state.missingReadCount()).toBe(1);
  expect(state.createCount()).toBe(1);
  expect(state.current()?.source.replace(/\r\n/g, "\n")).toBe(
    publicWorkflowSource.replace(/\r\n/g, "\n"),
  );
});

test("loads and saves the workspace workflow with its current CAS identity", async ({
  page,
}) => {
  const state = await mockRecoveryWorkspace(page);
  await openRecoveryEditor(page);

  await editThickness(page);
  await page
    .getByTestId("workflow-recovery-block-thickness-block.generate-geometry")
    .fill("8");
  await expect(page.getByTestId("workflow-recovery-save-status")).toContainText(
    "Unsaved",
  );
  await page.getByTestId("workflow-recovery-save").click();

  await expect(page.getByTestId("workflow-recovery-save-status")).toHaveText(
    "Saved",
  );
  expect(state.updateCount()).toBe(1);
  expect(state.current()?.storage_revision).toBe(2);
  expect(state.current()?.definition_revision).toBe(3);
  expect(state.current()?.source).toContain(
    'settings: {"inside_radius_mm":4,"thickness_mm":8}',
  );
});

test("binds decision and revision edges to explicit typed routing handles", async ({
  page,
}) => {
  const missingHandleDiagnostics: string[] = [];
  page.on("console", (message) => {
    if (
      message.text().includes("Couldn't create edge for") &&
      message.text().includes("handle id")
    ) {
      missingHandleDiagnostics.push(message.text());
    }
  });
  await mockRecoveryWorkspace(page);
  await openRecoveryEditor(page);

  const revisionEdge = page.getByTestId(
    "workflow-recovery-edge-rel.specification-revise",
  );
  await expect(revisionEdge).toBeVisible();
  await expect(revisionEdge).toHaveAttribute(
    "data-source-handle",
    "routing.feedback.source.block.create-design-specification",
  );
  await expect(revisionEdge).toHaveAttribute(
    "data-target-handle",
    "routing.feedback.target.block.design-intent",
  );
  await expect(
    page.getByTestId(
      "workflow-recovery-routing-handle-feedback-source-block.create-design-specification",
    ),
  ).toHaveAttribute(
    "data-handleid",
    "routing.feedback.source.block.create-design-specification",
  );
  await expect(
    page.getByTestId(
      "workflow-recovery-routing-handle-feedback-target-block.design-intent",
    ),
  ).toHaveAttribute(
    "data-handleid",
    "routing.feedback.target.block.design-intent",
  );

  const decisionEdge = page.getByTestId(
    "workflow-recovery-edge-rel.specification-accepted",
  );
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

test("keeps the engineer's local edit visible when a CAS save conflicts", async ({
  page,
}) => {
  const state = await mockRecoveryWorkspace(page);
  await openRecoveryEditor(page);

  await page.getByTestId("workflow-recovery-view-code").click();
  const editor = page.getByTestId("workflow-recovery-source-editor");
  await editor.fill(
    (await editor.inputValue()).replace(
      "Create bracket CAD model",
      "Create bracket CAD model locally",
    ),
  );
  await page.getByTestId("workflow-recovery-source-apply").click();
  state.conflictNextUpdate();
  await page.getByTestId("workflow-recovery-save").click();

  await expect(page.getByTestId("workflow-recovery-save-status")).toContainText(
    "changed elsewhere",
  );
  await expect(page.getByTestId("workflow-recovery-save-status")).toContainText(
    "local edits are still here",
  );
  await expect(editor).toHaveValue(/Create bracket CAD model locally/);
  expect(state.updateCount()).toBe(1);
  expect(state.current()?.source).toBe(publicWorkflowSource);
});

test("persists authored input text and a scoped workspace file reference across reopen", async ({
  page,
}) => {
  const state = await mockRecoveryWorkspace(page);
  await openRecoveryEditor(page);
  await expect(
    page.getByTestId("workflow-recovery-inputs-toggle"),
  ).toContainText("0/3 configured");
  await page.getByTestId("workflow-recovery-inputs-toggle").click();
  await page
    .getByTestId("workflow-recovery-input-navigate-block.design-intent")
    .click();
  await expect(
    page.getByTestId("workflow-recovery-inputs-navigator"),
  ).toHaveCount(0);
  await expect(
    page.getByTestId("workflow-recovery-input-editor"),
  ).toBeVisible();
  const instructions =
    "Support a 15 kg instrument on a wall. Material and mounting conditions require engineer review.";
  await page
    .getByTestId("workflow-recovery-input-text-block.design-intent")
    .fill(instructions);
  await expect(
    page.getByTestId("workflow-recovery-inputs-toggle"),
  ).toContainText("1/3 configured");
  await expect(page.getByTestId("workflow-recovery-run-start")).toBeDisabled();

  await page.getByTestId("workflow-recovery-inputs-toggle").click();
  await page
    .getByTestId("workflow-recovery-input-navigate-block.reference-images")
    .click();
  await page
    .getByTestId("workflow-recovery-input-select")
    .selectOption("references/bracket.png");
  await expect(
    page.getByTestId("workflow-recovery-inputs-toggle"),
  ).toContainText("2/3 configured");
  await page.getByTestId("workflow-recovery-save").click();
  await expect(page.getByTestId("workflow-recovery-save-status")).toHaveText(
    "Saved",
  );
  expect(state.current()?.source).toContain(instructions);
  expect(state.current()?.source).toContain(
    '"workspace_file":"references/bracket.png"',
  );
  expect(state.current()?.layout_status).toBe("current");

  await page.reload();
  await expect(
    page.getByTestId("workflow-recovery-inputs-toggle"),
  ).toContainText("2/3 configured");
  await editObject(page, "block.design-intent");
  await expect(
    page.getByTestId("workflow-recovery-input-text-block.design-intent"),
  ).toHaveValue(instructions);
  await editObject(page, "block.reference-images");
  await expect(page.getByTestId("workflow-recovery-input-select")).toHaveValue(
    "references/bracket.png",
  );
  await expect(page.getByTestId("workflow-recovery-run-start")).toBeDisabled();
});

test("keeps the canvas-first editor bounded with an optional inspector at 1070 by 791", async ({
  page,
}) => {
  await mockRecoveryWorkspace(page);
  await openRecoveryEditor(page);
  await page.setViewportSize({ width: 1070, height: 791 });
  const surfacePane = page.getByTestId("workspace-pane-surface");
  if (await surfacePane.isVisible()) await surfacePane.click();

  await expect(page.locator(".app-sidebar")).toHaveCount(0);
  await expect(page.getByTestId("workflow-recovery-inspector")).toHaveCount(0);
  const initialCanvas = await page
    .getByTestId("workflow-recovery-canvas")
    .boundingBox();
  expect(initialCanvas!.width).toBeGreaterThanOrEqual(800);
  await selectObject(page, "block.generate-geometry");

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
  expect(paletteBox!.x + paletteBox!.width).toBeLessThanOrEqual(
    canvasBox!.x + 1,
  );
  expect(canvasBox!.x + canvasBox!.width).toBeLessThanOrEqual(
    inspectorBox!.x + 1,
  );
  expect(canvasBox!.width).toBeGreaterThanOrEqual(500);
  expect(paletteBox!.width).toBeLessThanOrEqual(96);
  expect(inspectorBox!.y + inspectorBox!.height).toBeLessThanOrEqual(791);

  const overflow = await page.evaluate(() => {
    const select = (selector: string) =>
      document.querySelector<HTMLElement>(selector)!;
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
      palette: metric(select(".recovery-create-buttons")),
      inspector: metric(select(".recovery-inspector__body")),
    };
  });

  for (const container of [
    overflow.document,
    overflow.body,
    overflow.main,
    overflow.workspace,
    overflow.page,
    overflow.concept,
    overflow.workbench,
  ]) {
    expect(container.scrollHeight).toBeLessThanOrEqual(container.clientHeight);
  }
  expect(overflow.workspace.overflowY).toBe("hidden");
  expect(overflow.palette.overflowY).toBe("auto");
  expect(overflow.inspector.overflowY).toBe("auto");
  await closeInspector(page);
  expect((await canvas.boundingBox())!.width).toBeGreaterThan(canvasBox!.width);
});

test("expands a reusable component without adding search clutter to a small graph", async ({
  page,
}) => {
  await mockRecoveryWorkspace(page);
  await openRecoveryEditor(page);

  const concept = page.getByTestId("workflow-recovery-concept");
  await expect(concept).toHaveAttribute(
    "data-semantic-digest",
    /^sha256:[a-f0-9]{64}$/,
  );
  const revision = await concept.getAttribute("data-revision");
  const digest = await concept.getAttribute("data-semantic-digest");
  const component = page.getByTestId(
    "workflow-recovery-block-block.review-design",
  );
  await expect(component).toHaveAttribute("data-component-collapsed", "true");
  await expect(component).toContainText("Review group");
  await expect(component).not.toContainText("1 issue");
  await expect(component).not.toContainText("technical review items");
  await expect(
    page.getByTestId(
      "workflow-recovery-component-addresses-block.review-design",
    ),
  ).toHaveCount(0);

  await page
    .getByTestId("workflow-recovery-component-toggle-block.review-design")
    .click();
  await expect(component).toHaveAttribute("data-component-collapsed", "false");
  await expect(component).toContainText("4 technical review items");
  await expect(
    page.getByTestId(
      "workflow-recovery-component-addresses-block.review-design",
    ),
  ).toContainText("Accept the reviewed design");

  await expect(page.getByTestId("workflow-recovery-find-input")).toHaveCount(0);
  await selectObject(page, "block.export-step");
  await expect(page.getByTestId("workflow-recovery-inspector")).toContainText(
    "Export approved model as STEP AP242",
  );
  await expect(concept).toHaveAttribute("data-revision", revision ?? "2");
  await expect(concept).toHaveAttribute("data-semantic-digest", digest ?? "");
});

test("keeps overlapping edge labels behind blocks without losing keyboard edge selection", async ({
  page,
}) => {
  await mockRecoveryWorkspace(page);
  await openRecoveryEditor(page);

  const edgeLabel = page.getByTestId(
    "workflow-recovery-edge-select-rel.report-to-review",
  );
  await edgeLabel.focus();
  await edgeLabel.press("Enter");
  await expect(
    page.getByTestId("workflow-recovery-disconnect-rel.report-to-review"),
  ).toBeVisible();

  const manufacturingNode = page.getByTestId(
    "workflow-recovery-block-block.check-manufacturability",
  );
  await selectObject(page, "block.check-manufacturability");
  await expect(manufacturingNode).toHaveAttribute("data-selected", "true");
  await expect(page.getByTestId("workflow-recovery-inspector")).toContainText(
    "Run bracket manufacturing checks",
  );
});

test("keeps one accepted definition across canvas, source, and AI review", async ({
  page,
}) => {
  await mockRecoveryWorkspace(page);
  await openRecoveryEditor(page);

  const concept = page.getByTestId("workflow-recovery-concept");
  await expect(concept).toBeVisible();
  await expect(page.getByTestId("workflow-recovery-canvas")).toBeVisible();
  await expect(concept).toHaveAttribute("data-revision", "2");
  const filebar = page.getByTestId("workflow-recovery-filebar");
  await expect(filebar).toContainText("Mounting bracket development");
  await expect(page.getByTestId("workflow-recovery-save-status")).toContainText(
    "Saved",
  );
  expect(
    (await page.locator(".recovery-filebar__identity").boundingBox())?.height,
  ).toBeLessThanOrEqual(72);
  await expect(
    page.getByText(/Build and review the work as a diagram/),
  ).toHaveCount(0);
  await expect(page.locator(".react-flow__node")).toHaveCount(9);
  await expect(
    page.getByTestId("workflow-recovery-inputs-toggle"),
  ).toContainText("0/3 configured");
  await page.getByTestId("workflow-recovery-inputs-toggle").click();
  await expect(
    page.getByTestId("workflow-recovery-inputs-navigator"),
  ).toContainText("Reference images");
  await expect(
    page.getByTestId("workflow-recovery-inputs-navigator"),
  ).toContainText("Design intent");
  await expect(
    page.getByTestId("workflow-recovery-inputs-navigator"),
  ).toContainText("Company standards and context");
  await page.getByTestId("workflow-recovery-inputs-close").click();
  await expect(
    page.getByTestId(
      "workflow-recovery-block-block.create-design-specification",
    ),
  ).toContainText("Create and review design specification");
  await expect(page.getByTestId("workflow-recovery-palette")).toContainText(
    "AI prompt",
  );
  await expect(page.getByTestId("workflow-recovery-palette")).toContainText(
    "MCP servers",
  );
  await expect(
    page.getByTestId("workflow-recovery-palette-search"),
  ).toHaveCount(0);

  await editObject(page, "block.create-design-specification");
  await expect(page.getByTestId("workflow-recovery-inspector")).toContainText(
    "AI prompt",
  );
  await expect(page.getByTestId("workflow-recovery-inspector")).toContainText(
    "Review criteria",
  );
  await page
    .getByTestId(
      "workflow-recovery-block-review-toggle-block.create-design-specification",
    )
    .click();
  await expect(
    page.getByTestId(
      "workflow-recovery-block-review-block.create-design-specification",
    ),
  ).toHaveValue(/Accept when: An engineer accepted the design specification/);
  await expect(page.getByTestId("workflow-recovery-inspector")).toContainText(
    "These criteria come from this step's accept and revise paths",
  );

  await selectObject(page, "block.generate-geometry");
  await expect(
    page.getByTestId("workflow-recovery-palette-search"),
  ).toHaveCount(0);
  await page.getByTestId("workflow-recovery-create-group-input").click();
  await page
    .getByTestId("workflow-recovery-create-template-text-input")
    .click();
  await expect(concept).toHaveAttribute("data-revision", "3");
  const created = page.getByTestId(
    "workflow-recovery-block-block.text-input-1",
  );
  await expect(created).toBeVisible();
  await page.getByTestId("workflow-recovery-undo").click();
  await expect(concept).toHaveAttribute("data-revision", "4");
  await expect(created).toHaveCount(0);
  await page.getByTestId("workflow-recovery-redo").click();
  await expect(concept).toHaveAttribute("data-revision", "5");
  await expect(created).toBeVisible();
  await created.focus();
  await created.press("Delete");
  await expect(page.getByRole("dialog")).toContainText("0 connection(s)");
  await page.getByTestId("workflow-recovery-delete-confirm").click();
  await expect(concept).toHaveAttribute("data-revision", "6");
  await expect(created).toHaveCount(0);

  await editThickness(page);
  await page
    .getByTestId("workflow-recovery-block-thickness-block.generate-geometry")
    .fill("8");
  await expect(concept).toHaveAttribute("data-revision", "7");
  await page
    .getByTestId("workflow-recovery-edge-select-rel.review-revise")
    .focus();
  await page.keyboard.press("Enter");
  await page
    .getByLabel("Condition or reason")
    .fill("A requirement or manufacturability warning requires revision");
  await page
    .getByTestId("workflow-recovery-relationship-apply-rel.review-revise")
    .click();
  await expect(concept).toHaveAttribute("data-revision", "8");
  await selectObject(page, "block.generate-geometry");

  await page.getByTestId("workflow-recovery-view-split").click();
  const synchronizedSource = page.getByTestId(
    "workflow-recovery-source-editor",
  );
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
  await expect(page.getByTestId("workflow-recovery-inspector")).toContainText(
    "Export approved model as STEP AP242",
  );
  const revisionBeforeInvalid = await concept.getAttribute("data-revision");
  const source = synchronizedSource;
  await source.fill("workflow mounting_bracket\n  revision: 99\nend\n");
  await page.getByTestId("workflow-recovery-source-apply").click();
  await expect(
    page.getByTestId("workflow-recovery-diagnostic-WFR-SOURCE-FIELD-MANAGED"),
  ).toBeVisible();
  await expect(concept).toHaveAttribute(
    "data-revision",
    revisionBeforeInvalid ?? "8",
  );
  await expect(page.getByTestId("workflow-recovery-run-start")).toBeDisabled();
});

test("uses real typed handles and preserves source across a layout save", async ({
  page,
}) => {
  const canvasDiagnostics: string[] = [];
  const recordCanvasDiagnostic = (text: string) => {
    if (
      text.includes("trying to drag a node that is not initialized") ||
      text.includes("Couldn't create edge for") ||
      text.includes("ResizeObserver loop")
    ) {
      canvasDiagnostics.push(text);
    }
  };
  page.on("console", (message) =>
    recordCanvasDiagnostic(`console ${message.type()}: ${message.text()}`),
  );
  page.on("pageerror", (error) =>
    recordCanvasDiagnostic(`pageerror: ${error.message}`),
  );
  const state = await mockRecoveryWorkspace(page);
  await openRecoveryEditor(page);
  const concept = page.getByTestId("workflow-recovery-concept");

  await expect(concept).toHaveAttribute(
    "data-semantic-digest",
    /^sha256:[a-f0-9]{64}$/,
  );
  await expect(concept).toHaveAttribute(
    "data-layout-digest",
    /^sha256:[a-f0-9]{64}$/,
  );
  const semanticBeforeDrag = await concept.getAttribute("data-semantic-digest");
  const layoutBeforeDrag = await concept.getAttribute("data-layout-digest");
  const draggable = page.locator(
    '.react-flow__node[data-id="block.generate-geometry"]',
  );
  const dragBox = await draggable.boundingBox();
  expect(dragBox).not.toBeNull();
  await page.mouse.move(
    dragBox!.x + dragBox!.width / 2,
    dragBox!.y + dragBox!.height / 2,
  );
  await page.mouse.down();
  await page.mouse.move(
    dragBox!.x + dragBox!.width / 2 + 80,
    dragBox!.y + dragBox!.height / 2 + 30,
    { steps: 10 },
  );
  await expect
    .poll(async () => (await draggable.boundingBox())?.x ?? dragBox!.x)
    .toBeGreaterThan(dragBox!.x + 40);
  await expect(concept).toHaveAttribute("data-revision", "2");
  await expect(concept).toHaveAttribute(
    "data-semantic-digest",
    semanticBeforeDrag!,
  );
  await expect(concept).toHaveAttribute(
    "data-layout-digest",
    layoutBeforeDrag!,
  );
  await page.mouse.up();
  await expect(concept).toHaveAttribute("data-revision", "2");
  await expect(concept).toHaveAttribute(
    "data-semantic-digest",
    semanticBeforeDrag!,
  );
  await expect
    .poll(() => concept.getAttribute("data-layout-digest"))
    .not.toBe(layoutBeforeDrag);
  await page.waitForTimeout(100);
  expect(canvasDiagnostics).toEqual([]);

  await page.getByTestId("workflow-recovery-save").click();
  await expect(page.getByTestId("workflow-recovery-save-status")).toHaveText(
    "Saved",
  );
  await expect.poll(() => state.current()?.layout_revision).toBe(1);
  expect(state.current()?.definition_revision).toBe(2);
  expect(state.current()?.source.replace(/\r\n/g, "\n")).toBe(
    publicWorkflowSource.replace(/\r\n/g, "\n"),
  );
  const storedDefinitionRevision = state.current()?.definition_revision;
  expect(storedDefinitionRevision).toBeDefined();

  await page.reload();
  await expect(concept).toHaveAttribute(
    "data-revision",
    String(storedDefinitionRevision),
  );
  const exportNode = page.locator(
    '.react-flow__node[data-id="block.export-step"]',
  );
  await exportNode.focus();
  await exportNode.press("Enter");
  await expect(page.getByTestId("workflow-recovery-inspector")).toContainText(
    "Export approved model as STEP AP242",
  );

  await page
    .getByTestId("workflow-recovery-edge-select-rel.review-to-export")
    .focus();
  await page.keyboard.press("Enter");
  await expect(
    page.getByTestId("workflow-recovery-disconnect-rel.review-to-export"),
  ).toBeVisible();
  await page
    .getByTestId("workflow-recovery-disconnect-rel.review-to-export")
    .click();
  await expect(concept).toHaveAttribute(
    "data-revision",
    String(storedDefinitionRevision! + 1),
  );

  const sourceHandle = page.getByTestId(
    "workflow-recovery-handle-port.approved-geometry-out",
  );
  const targetHandle = page.getByTestId(
    "workflow-recovery-handle-port.approved-geometry-in",
  );
  // Move the non-semantic overview out of pointer hit-testing so this case targets the typed sockets.
  await page.locator(".react-flow__minimap").evaluate((element) => {
    (element as HTMLElement).style.pointerEvents = "none";
  });
  await sourceHandle.dragTo(targetHandle);
  await expect(
    page.getByTestId("workflow-recovery-edge-rel.review-to-export"),
  ).toBeVisible();
  await expect(concept).toHaveAttribute(
    "data-revision",
    String(storedDefinitionRevision! + 2),
  );

  await page
    .getByTestId("workflow-recovery-edge-select-rel.review-to-export")
    .focus();
  await page.keyboard.press("Enter");
  await page
    .getByTestId("workflow-recovery-disconnect-rel.review-to-export")
    .click();
  await expect(concept).toHaveAttribute(
    "data-revision",
    String(storedDefinitionRevision! + 3),
  );
  await sourceHandle.focus();
  await sourceHandle.press("Enter");
  await expect(
    page.getByRole("status").filter({ hasText: "Connection started" }),
  ).toContainText("Connection started");
  await targetHandle.focus();
  await targetHandle.press("Enter");
  await expect(
    page.getByTestId("workflow-recovery-edge-rel.review-to-export"),
  ).toBeVisible();
  await expect(concept).toHaveAttribute(
    "data-revision",
    String(storedDefinitionRevision! + 4),
  );
});

test("promotes valid source and reviewed AI commands while production execution remains fail-closed", async ({
  page,
}) => {
  await mockRecoveryWorkspace(page);
  await openRecoveryEditor(page);
  const concept = page.getByTestId("workflow-recovery-concept");

  await page.getByTestId("workflow-recovery-view-code").click();
  const editor = page.getByTestId("workflow-recovery-source-editor");
  const source = await editor.inputValue();
  expect(source).toContain("Create bracket CAD model");
  await editor.fill(
    source.replace("Create bracket CAD model", "Create bracket CAD model v2"),
  );
  await page.getByTestId("workflow-recovery-source-apply").click();
  await expect(concept).toHaveAttribute("data-revision", "3");
  await page.getByTestId("workflow-recovery-view-diagram").click();
  await expect(
    page.getByTestId("workflow-recovery-block-block.generate-geometry"),
  ).toContainText("Create bracket CAD model v2");

  await page.getByTestId("workflow-recovery-ai-request").click();
  await expect(page.getByTestId("workflow-recovery-proposal")).toHaveAttribute(
    "data-base-revision",
    "3",
  );
  await expect(
    page.getByTestId("workflow-recovery-proposal-preview"),
  ).toContainText("Create manufacturing drawing");
  await page.getByTestId("workflow-recovery-proposal-reject").click();
  await expect(concept).toHaveAttribute("data-revision", "3");
  await expect(
    page.getByTestId("workflow-recovery-block-block.create-inspection-drawing"),
  ).toHaveCount(0);

  await page.getByTestId("workflow-recovery-ai-request").click();
  await editObject(page, "block.create-inspection-drawing");
  await expect(
    page.getByTestId("workflow-recovery-candidate-readonly"),
  ).toBeVisible();
  await page.getByTestId("workflow-recovery-proposal-accept").click();
  await expect(concept).toHaveAttribute("data-revision", "4");
  await expect(
    page.getByTestId("workflow-recovery-block-block.create-inspection-drawing"),
  ).toBeAttached();
  await expect(
    page.getByTestId("workflow-recovery-block-block.review-inspection-drawing"),
  ).toBeAttached();

  await page.getByTestId("workflow-recovery-undo").click();
  await expect(
    page.getByTestId("workflow-recovery-block-block.create-inspection-drawing"),
  ).toHaveCount(0);
  await page.getByTestId("workflow-recovery-undo").click();
  await expect(
    page.getByTestId("workflow-recovery-block-block.generate-geometry"),
  ).toContainText("Create bracket CAD model");

  await expect(page.getByTestId("workflow-recovery-run-start")).toBeDisabled();
  await expect(page.getByTestId("workflow-recovery-run-mode")).toHaveCount(0);
  await expect(page.getByTestId("workflow-recovery-run-advance")).toHaveCount(
    0,
  );
});
test("keeps paired diagram and source edits inside the local one-second feedback bound", async ({
  page,
}) => {
  await mockRecoveryWorkspace(page);
  await openRecoveryEditor(page);
  await editThickness(page);
  await page.getByTestId("workflow-recovery-view-split").click();
  const source = page.getByTestId("workflow-recovery-source-editor");

  await page
    .getByTestId("workflow-recovery-block-thickness-block.generate-geometry")
    .fill("8");
  const graphStarted = Date.now();
  await expect(source).toHaveValue(/"thickness_mm":8/, { timeout: 1000 });
  const graphToTextMs = Date.now() - graphStarted;
  expect(graphToTextMs).toBeLessThan(1000);

  const current = await source.inputValue();
  await source.fill(
    current.replace(
      "Create bracket CAD model",
      "Create bracket CAD model paired",
    ),
  );
  const textStarted = Date.now();
  await page.getByTestId("workflow-recovery-source-apply").click();
  await expect(
    page.getByTestId("workflow-recovery-block-block.generate-geometry"),
  ).toContainText("Create bracket CAD model paired", { timeout: 1000 });
  const textToGraphMs = Date.now() - textStarted;
  expect(textToGraphMs).toBeLessThan(1000);

  await expect(page.getByTestId("workflow-recovery-run-start")).toBeDisabled();

  test.info().annotations.push({
    type: "latency",
    description: `graph→text=${graphToTextMs}ms; text→graph=${textToGraphMs}ms; bound<1000ms`,
  });
});
test("keeps production readiness accessible, reduced-motion legible, and mobile-contained", async ({
  page,
}) => {
  await page.emulateMedia({ reducedMotion: "reduce" });
  await mockRecoveryWorkspace(page);
  await openRecoveryEditor(page);
  await expect(page.getByTestId("workflow-recovery-concept")).toBeVisible();

  const serious = async () =>
    (
      await new AxeBuilder({ page })
        .include('[data-testid="workflow-recovery-concept"]')
        .analyze()
    ).violations
      .filter(
        (violation) =>
          violation.impact === "serious" || violation.impact === "critical",
      )
      .map((violation) => ({
        id: violation.id,
        targets: violation.nodes.flatMap((node) => node.target.map(String)),
      }));
  expect(await serious()).toEqual([]);

  await expect(page.getByTestId("workflow-recovery-run-start")).toBeDisabled();
  await expect(page.getByTestId("workflow-recovery-run-mode")).toHaveCount(0);

  await page.setViewportSize({ width: 390, height: 844 });
  await page.reload();
  await page.getByTestId("workspace-pane-surface").click();
  await expect(page.getByTestId("workflow-recovery-concept")).toBeVisible();
  const overflow = await page.evaluate(() => ({
    width: document.documentElement.scrollWidth,
    viewport: document.documentElement.clientWidth,
  }));
  expect(overflow.width).toBeLessThanOrEqual(overflow.viewport);
  await expect(page.getByTestId("workflow-recovery-palette")).toBeVisible();
  await expect(page.getByTestId("workflow-recovery-inspector")).toHaveCount(0);
  await page.getByTestId("workflow-recovery-inputs-toggle").click();
  await page
    .getByTestId("workflow-recovery-input-navigate-block.design-intent")
    .click();
  await expect(page.getByTestId("workflow-recovery-inspector")).toBeVisible();
  await expect(
    page.getByTestId("workflow-recovery-inspector-close"),
  ).toBeVisible();
  expect(await serious()).toEqual([]);
});
