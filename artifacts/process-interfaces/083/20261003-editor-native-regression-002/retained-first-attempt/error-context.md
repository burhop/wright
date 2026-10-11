# Instructions

- Following Playwright test failed.
- Explain why, be concise, respect Playwright best practices.
- Provide a snippet of code with the fix, if possible.

# Test info

- Name: workflow-recovery.spec.ts >> persists authored input text and a scoped workspace file reference across reopen
- Location: tests\ui-integration\workflow-recovery.spec.ts:191:5

# Error details

```
Error: expect(locator).toBeDisabled() failed

Locator:  getByTestId('workflow-recovery-run-start')
Expected: disabled
Received: enabled
Timeout:  15000ms

Call log:
  - Expect "toBeDisabled" with timeout 15000ms
  - waiting for getByTestId('workflow-recovery-run-start')
    33 × locator resolved to <button type="button" title="Run the saved workspace workflow" data-testid="workflow-recovery-run-start" class="recovery-button recovery-button--primary">▶ Run</button>
       - unexpected value "enabled"

```

```yaml
- button "▶ Run"
```

# Test source

```ts
  154 |   );
  155 |   await expect(decisionEdge).toHaveAttribute(
  156 |     "data-target-handle",
  157 |     "routing.flow.target.block.generate-geometry",
  158 |   );
  159 |   expect(missingHandleDiagnostics).toEqual([]);
  160 | });
  161 | 
  162 | test("keeps the engineer's local edit visible when a CAS save conflicts", async ({
  163 |   page,
  164 | }) => {
  165 |   const state = await mockRecoveryWorkspace(page);
  166 |   await openRecoveryEditor(page);
  167 | 
  168 |   await page.getByTestId("workflow-recovery-view-code").click();
  169 |   const editor = page.getByTestId("workflow-recovery-source-editor");
  170 |   await editor.fill(
  171 |     (await editor.inputValue()).replace(
  172 |       "Create bracket CAD model",
  173 |       "Create bracket CAD model locally",
  174 |     ),
  175 |   );
  176 |   await page.getByTestId("workflow-recovery-source-apply").click();
  177 |   state.conflictNextUpdate();
  178 |   await page.getByTestId("workflow-recovery-save").click();
  179 | 
  180 |   await expect(page.getByTestId("workflow-recovery-save-status")).toContainText(
  181 |     "changed elsewhere",
  182 |   );
  183 |   await expect(page.getByTestId("workflow-recovery-save-status")).toContainText(
  184 |     "local edits are still here",
  185 |   );
  186 |   await expect(editor).toHaveValue(/Create bracket CAD model locally/);
  187 |   expect(state.updateCount()).toBe(1);
  188 |   expect(state.current()?.source).toBe(publicWorkflowSource);
  189 | });
  190 | 
  191 | test("persists authored input text and a scoped workspace file reference across reopen", async ({
  192 |   page,
  193 | }) => {
  194 |   const state = await mockRecoveryWorkspace(page);
  195 |   await openRecoveryEditor(page);
  196 |   await expect(
  197 |     page.getByTestId("workflow-recovery-inputs-toggle"),
  198 |   ).toContainText("0/3 configured");
  199 |   await page.getByTestId("workflow-recovery-inputs-toggle").click();
  200 |   await page
  201 |     .getByTestId("workflow-recovery-input-navigate-block.design-intent")
  202 |     .click();
  203 |   await expect(
  204 |     page.getByTestId("workflow-recovery-inputs-navigator"),
  205 |   ).toHaveCount(0);
  206 |   await expect(
  207 |     page.getByTestId("workflow-recovery-input-editor"),
  208 |   ).toBeVisible();
  209 |   const instructions =
  210 |     "Support a 15 kg instrument on a wall. Material and mounting conditions require engineer review.";
  211 |   await page
  212 |     .getByTestId("workflow-recovery-input-text-block.design-intent")
  213 |     .fill(instructions);
  214 |   await expect(
  215 |     page.getByTestId("workflow-recovery-inputs-toggle"),
  216 |   ).toContainText("1/3 configured");
  217 |   // Native Run is a preflight affordance, not the former simulation switch.
  218 |   await expect(page.getByTestId("workflow-recovery-run-start")).toBeEnabled();
  219 |   expect(state.runRequestCount()).toBe(0);
  220 |   expect(state.runCount()).toBe(0);
  221 | 
  222 |   await page.getByTestId("workflow-recovery-inputs-toggle").click();
  223 |   await page
  224 |     .getByTestId("workflow-recovery-input-navigate-block.reference-images")
  225 |     .click();
  226 |   await page
  227 |     .getByTestId("workflow-recovery-input-select")
  228 |     .selectOption("references/bracket.png");
  229 |   await expect(
  230 |     page.getByTestId("workflow-recovery-inputs-toggle"),
  231 |   ).toContainText("2/3 configured");
  232 |   await page.getByTestId("workflow-recovery-save").click();
  233 |   await expect(page.getByTestId("workflow-recovery-save-status")).toHaveText(
  234 |     "Saved",
  235 |   );
  236 |   expect(state.current()?.source).toContain(instructions);
  237 |   expect(state.current()?.source).toContain(
  238 |     '"workspace_file":"references/bracket.png"',
  239 |   );
  240 |   expect(state.current()?.layout_status).toBe("current");
  241 | 
  242 |   await page.reload();
  243 |   await expect(
  244 |     page.getByTestId("workflow-recovery-inputs-toggle"),
  245 |   ).toContainText("2/3 configured");
  246 |   await editObject(page, "block.design-intent");
  247 |   await expect(
  248 |     page.getByTestId("workflow-recovery-input-text-block.design-intent"),
  249 |   ).toHaveValue(instructions);
  250 |   await editObject(page, "block.reference-images");
  251 |   await expect(page.getByTestId("workflow-recovery-input-select")).toHaveValue(
  252 |     "references/bracket.png",
  253 |   );
> 254 |   await expect(page.getByTestId("workflow-recovery-run-start")).toBeDisabled();
      |                                                                 ^ Error: expect(locator).toBeDisabled() failed
  255 | });
  256 | 
  257 | test("keeps the canvas-first editor bounded with an optional inspector at 1070 by 791", async ({
  258 |   page,
  259 | }) => {
  260 |   await mockRecoveryWorkspace(page);
  261 |   await openRecoveryEditor(page);
  262 |   await page.setViewportSize({ width: 1070, height: 791 });
  263 |   const surfacePane = page.getByTestId("workspace-pane-surface");
  264 |   if (await surfacePane.isVisible()) await surfacePane.click();
  265 | 
  266 |   await expect(page.locator(".app-sidebar")).toHaveCount(0);
  267 |   await expect(page.getByTestId("workflow-recovery-inspector")).toHaveCount(0);
  268 |   const initialCanvas = await page
  269 |     .getByTestId("workflow-recovery-canvas")
  270 |     .boundingBox();
  271 |   expect(initialCanvas!.width).toBeGreaterThanOrEqual(800);
  272 |   await selectObject(page, "block.generate-geometry");
  273 | 
  274 |   const palette = page.getByTestId("workflow-recovery-palette");
  275 |   const canvas = page.getByTestId("workflow-recovery-canvas");
  276 |   const inspector = page.getByTestId("workflow-recovery-inspector");
  277 |   const [paletteBox, canvasBox, inspectorBox] = await Promise.all([
  278 |     palette.boundingBox(),
  279 |     canvas.boundingBox(),
  280 |     inspector.boundingBox(),
  281 |   ]);
  282 | 
  283 |   expect(paletteBox).not.toBeNull();
  284 |   expect(canvasBox).not.toBeNull();
  285 |   expect(inspectorBox).not.toBeNull();
  286 |   expect(paletteBox!.y).toBe(inspectorBox!.y);
  287 |   expect(paletteBox!.x + paletteBox!.width).toBeLessThanOrEqual(
  288 |     canvasBox!.x + 1,
  289 |   );
  290 |   expect(canvasBox!.x + canvasBox!.width).toBeLessThanOrEqual(
  291 |     inspectorBox!.x + 1,
  292 |   );
  293 |   expect(canvasBox!.width).toBeGreaterThanOrEqual(500);
  294 |   expect(paletteBox!.width).toBeLessThanOrEqual(96);
  295 |   expect(inspectorBox!.y + inspectorBox!.height).toBeLessThanOrEqual(791);
  296 | 
  297 |   const overflow = await page.evaluate(() => {
  298 |     const select = (selector: string) =>
  299 |       document.querySelector<HTMLElement>(selector)!;
  300 |     const metric = (element: HTMLElement) => ({
  301 |       clientHeight: element.clientHeight,
  302 |       scrollHeight: element.scrollHeight,
  303 |       overflowY: getComputedStyle(element).overflowY,
  304 |     });
  305 |     return {
  306 |       document: metric(document.documentElement),
  307 |       body: metric(document.body),
  308 |       main: metric(select(".app-shell__main")),
  309 |       workspace: metric(select('[data-testid="workspace-panel"]')),
  310 |       page: metric(select('[data-testid="page-workflow-recovery"]')),
  311 |       concept: metric(select('[data-testid="workflow-recovery-concept"]')),
  312 |       workbench: metric(select(".recovery-workbench")),
  313 |       palette: metric(select(".recovery-create-buttons")),
  314 |       inspector: metric(select(".recovery-inspector__body")),
  315 |     };
  316 |   });
  317 | 
  318 |   for (const container of [
  319 |     overflow.document,
  320 |     overflow.body,
  321 |     overflow.main,
  322 |     overflow.workspace,
  323 |     overflow.page,
  324 |     overflow.concept,
  325 |     overflow.workbench,
  326 |   ]) {
  327 |     expect(container.scrollHeight).toBeLessThanOrEqual(container.clientHeight);
  328 |   }
  329 |   expect(overflow.workspace.overflowY).toBe("hidden");
  330 |   expect(overflow.palette.overflowY).toBe("auto");
  331 |   expect(overflow.inspector.overflowY).toBe("auto");
  332 |   await closeInspector(page);
  333 |   expect((await canvas.boundingBox())!.width).toBeGreaterThan(canvasBox!.width);
  334 | });
  335 | 
  336 | test("expands a reusable component without adding search clutter to a small graph", async ({
  337 |   page,
  338 | }) => {
  339 |   await mockRecoveryWorkspace(page);
  340 |   await openRecoveryEditor(page);
  341 | 
  342 |   const concept = page.getByTestId("workflow-recovery-concept");
  343 |   await expect(concept).toHaveAttribute(
  344 |     "data-semantic-digest",
  345 |     /^sha256:[a-f0-9]{64}$/,
  346 |   );
  347 |   const revision = await concept.getAttribute("data-revision");
  348 |   const digest = await concept.getAttribute("data-semantic-digest");
  349 |   const component = page.getByTestId(
  350 |     "workflow-recovery-block-block.review-design",
  351 |   );
  352 |   await expect(component).toHaveAttribute("data-component-collapsed", "true");
  353 |   await expect(component).toContainText("Review group");
  354 |   await expect(component).not.toContainText("1 issue");
```