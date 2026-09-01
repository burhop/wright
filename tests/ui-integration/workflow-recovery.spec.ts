import { expect, test, type Page } from "@playwright/test";
import AxeBuilder from "@axe-core/playwright";

async function mockRecoveryShell(page: Page): Promise<void> {
  await page.route("**/api/**", async (route) => {
    const path = new URL(route.request().url()).pathname;
    if (path === "/api/auth/session/status") {
      await route.fulfill({ json: { auth_required: false, authenticated: true } });
      return;
    }
    if (path === "/api/setup/status") {
      await route.fulfill({ json: { is_configured: true, active_agent: "hermes", theme: "dark" } });
      return;
    }
    if (path === "/api/mcp/servers") {
      await route.fulfill({ json: { servers: [] } });
      return;
    }
    if (path === "/api/mcp/tools") {
      await route.fulfill({ json: { tools: [] } });
      return;
    }
    if (path === "/api/agent/sessions") {
      await route.fulfill({ json: { sessions: [] } });
      return;
    }
    if (path === "/api/workspace/recent" || path === "/api/workspace/list") {
      await route.fulfill({ json: { workspaces: [] } });
      return;
    }
    if (path.endsWith("/health")) {
      await route.fulfill({ json: { state: "connected", latencyMs: 1 } });
      return;
    }
    await route.fulfill({ status: 404, json: { detail: "Unmocked recovery-shell API" } });
  });
}

test("expands a reusable component and focuses stable identities without changing the accepted subject", async ({ page }) => {
  await mockRecoveryShell(page);
  await page.goto("/workflow-recovery");

  const concept = page.getByTestId("workflow-recovery-concept");
  const revision = await concept.getAttribute("data-revision");
  const digest = await concept.getAttribute("data-semantic-digest");
  const component = page.getByTestId("workflow-recovery-block-block.review-design");
  await expect(component).toHaveAttribute("data-component-collapsed", "true");
  await expect(component).toContainText("4 stable internal addresses");
  await expect(page.getByTestId("workflow-recovery-component-addresses-block.review-design")).toHaveCount(0);

  await page.getByTestId("workflow-recovery-component-toggle-block.review-design").click();
  await expect(component).toHaveAttribute("data-component-collapsed", "false");
  await expect(page.getByTestId("workflow-recovery-component-addresses-block.review-design"))
    .toContainText("component.review-cell.relationship.accept");

  await page.getByTestId("workflow-recovery-find-input").fill("block.export-step");
  await page.getByTestId("workflow-recovery-find-submit").click();
  await expect(page.getByRole("status").filter({ hasText: "Focused Export STEP" })).toBeVisible();
  await expect(page.getByTestId("workflow-recovery-inspector")).toContainText("block.export-step");
  await expect(concept).toHaveAttribute("data-revision", revision ?? "1");
  await expect(concept).toHaveAttribute("data-semantic-digest", digest ?? "");
});

test("keeps one accepted definition across canvas, source, AI review, and simulation", async ({ page }) => {
  await mockRecoveryShell(page);
  await page.goto("/workflow-recovery");

  const concept = page.getByTestId("workflow-recovery-concept");
  await expect(concept).toBeVisible();
  await expect(page.getByTestId("workflow-recovery-canvas")).toBeVisible();
  await expect(concept).toHaveAttribute("data-revision", "1");
  await expect(page.getByText("PROVISIONAL · NOT PRODUCTION")).toBeVisible();
  await expect(page.getByText("SIMULATED", { exact: true })).toBeVisible();
  await expect(page.locator(".react-flow__node")).toHaveCount(6);

  await page.getByRole("button", { name: "Port lab" }).click();
  await expect(page.getByTestId("workflow-port-lab-dot")).toBeVisible();
  await expect(page.getByTestId("workflow-port-lab-terminal")).toBeVisible();
  await expect(page.getByTestId("workflow-port-lab-hybrid")).toHaveClass(/is-selected/);
  await page.getByRole("button", { name: "dot connect socket" }).click();
  await expect(page.getByTestId("workflow-port-lab-dot")).toContainText("Connection started");
  await page.getByRole("button", { name: "dot inspect artifact" }).click();
  await expect(page.getByTestId("workflow-port-lab-dot")).toContainText("Artifact inspected separately");
  await page.getByTestId("workflow-port-lab-terminal").getByRole("button", { name: "Select treatment" }).click();
  await expect(page.getByTestId("workflow-recovery-canvas")).toHaveAttribute("data-port-treatment", "terminal");
  await page.getByRole("button", { name: "Close dialog" }).click();

  await page.getByTestId("workflow-recovery-palette-search").fill("tolerance");
  await page.getByTestId("workflow-recovery-palette-item-tolerance").click();
  await expect(concept).toHaveAttribute("data-revision", "2");
  await expect(page.getByTestId("workflow-recovery-block-block.tolerance-1")).toBeVisible();
  await page.getByTestId("workflow-recovery-undo").click();
  await expect(concept).toHaveAttribute("data-revision", "3");
  await expect(page.getByTestId("workflow-recovery-block-block.tolerance-1")).toHaveCount(0);
  await page.getByTestId("workflow-recovery-redo").click();
  await expect(concept).toHaveAttribute("data-revision", "4");
  await expect(page.getByTestId("workflow-recovery-block-block.tolerance-1")).toBeVisible();
  await page.getByTestId("workflow-recovery-block-block.tolerance-1").click();
  await page.getByTestId("workflow-recovery-delete").click();
  await expect(concept).toHaveAttribute("data-revision", "5");
  await expect(page.getByTestId("workflow-recovery-block-block.tolerance-1")).toHaveCount(0);

  await expect(page.getByTestId("workflow-recovery-attachment-artifact.brief")).toContainText("No source attached");
  await expect(page.getByTestId("workflow-recovery-run-start")).toBeDisabled();
  await page.getByTestId("workflow-recovery-attachment-attach-artifact.brief").click();
  await expect(page.getByTestId("workflow-recovery-attachment-artifact.brief")).toContainText("bracket-requirements-r3.pdf");
  await page.getByTestId("workflow-recovery-attachment-preview-artifact.brief").click();
  await expect(page.getByRole("heading", { name: "L-bracket mounting interface" })).toBeVisible();
  await page.getByRole("button", { name: "Close dialog" }).click();
  await page.getByTestId("workflow-recovery-attachment-replace-artifact.brief").click();
  await expect(page.getByTestId("workflow-recovery-attachment-artifact.brief")).toContainText("bracket-requirements-r4.pdf");
  await expect(concept).toHaveAttribute("data-revision", "5");

  await page.getByTestId("workflow-recovery-block-block.generate-geometry").click();
  await page.getByLabel("Thickness (mm)").fill("8");
  await page.getByTestId("workflow-recovery-config-apply").click();
  await expect(concept).toHaveAttribute("data-revision", "6");
  await page.getByTestId("workflow-recovery-edge-select-rel.review-revise").click();
  await page.getByLabel("Condition or reason").fill("A requirement or manufacturability warning requires revision");
  await page.getByTestId("workflow-recovery-relationship-apply-rel.review-revise").click();
  await expect(concept).toHaveAttribute("data-revision", "7");
  await page.getByTestId("workflow-recovery-block-block.generate-geometry").click();

  await page.getByTestId("workflow-recovery-view-split").click();
  const synchronizedSource = page.getByTestId("workflow-recovery-source-editor");
  await expect(synchronizedSource).toHaveValue(/thickness_mm/);
  const graphSelection = await synchronizedSource.evaluate((element) => {
    const editor = element as HTMLTextAreaElement;
    return editor.value.slice(editor.selectionStart, editor.selectionEnd);
  });
  expect(graphSelection).toContain("block block.generate-geometry");
  await synchronizedSource.evaluate((element) => {
    const editor = element as HTMLTextAreaElement;
    const offset = editor.value.indexOf("block block.export-step") + 8;
    editor.focus();
    editor.setSelectionRange(offset, offset);
  });
  await synchronizedSource.press("ArrowRight");
  await expect(page.getByTestId("workflow-recovery-inspector")).toContainText("Export STEP");
  const revisionBeforeInvalid = await concept.getAttribute("data-revision");
  const source = synchronizedSource;
  await source.fill("workflow workflow.mounting-bracket\n  schemaVersion: \"2.0.0-recovery.1\"\n");
  await page.getByTestId("workflow-recovery-source-apply").click();
  await expect(page.locator('[data-testid^="workflow-recovery-diagnostic-"]')).toBeVisible();
  await expect(concept).toHaveAttribute("data-revision", revisionBeforeInvalid ?? "7");
  await expect(page.getByTestId("workflow-recovery-run-start")).toBeDisabled();
});

test("uses real typed handles and preserves revision during a simulated run", async ({ page }) => {
  await mockRecoveryShell(page);
  await page.goto("/workflow-recovery");
  const concept = page.getByTestId("workflow-recovery-concept");

  await expect(concept).toHaveAttribute("data-semantic-digest", "sha256:57ed2b7caacc9b3a779d9e960a681a9b8fe6dc1cfc9c3d48fa6ddd5e184be889");
  await page.getByTestId("workflow-recovery-attachment-attach-artifact.brief").click();
  const semanticBeforeDrag = await concept.getAttribute("data-semantic-digest");
  const layoutBeforeDrag = await concept.getAttribute("data-layout-digest");
  const draggable = page.locator('.react-flow__node[data-id="block.generate-geometry"]');
  const dragBox = await draggable.boundingBox();
  expect(dragBox).not.toBeNull();
  await page.mouse.move(dragBox!.x + dragBox!.width / 2, dragBox!.y + 45);
  await page.mouse.down();
  await page.mouse.move(dragBox!.x + dragBox!.width / 2 + 80, dragBox!.y + 75, { steps: 10 });
  await page.mouse.up();
  await expect(concept).toHaveAttribute("data-revision", "1");
  await expect(concept).toHaveAttribute("data-semantic-digest", semanticBeforeDrag!);
  await expect.poll(() => concept.getAttribute("data-layout-digest")).not.toBe(layoutBeforeDrag);

  const exportNode = page.locator('.react-flow__node[data-id="block.export-step"]');
  await exportNode.focus();
  await exportNode.press("Enter");
  await expect(page.getByTestId("workflow-recovery-inspector")).toContainText("Export STEP");

  await page.getByTestId("workflow-recovery-edge-select-rel.review-to-export").click();
  await expect(page.getByTestId("workflow-recovery-disconnect-rel.review-to-export")).toBeVisible();
  await page.getByTestId("workflow-recovery-disconnect-rel.review-to-export").click();
  await expect(concept).toHaveAttribute("data-revision", "2");

  const sourceHandle = page.getByTestId("workflow-recovery-handle-port.approved-geometry-out");
  const targetHandle = page.getByTestId("workflow-recovery-handle-port.approved-geometry-in");
  const sourceBox = await sourceHandle.boundingBox();
  const targetBox = await targetHandle.boundingBox();
  expect(sourceBox).not.toBeNull();
  expect(targetBox).not.toBeNull();
  await page.mouse.move(sourceBox!.x + sourceBox!.width / 2, sourceBox!.y + sourceBox!.height / 2);
  await page.mouse.down();
  await page.mouse.move(targetBox!.x + targetBox!.width / 2, targetBox!.y + targetBox!.height / 2, { steps: 12 });
  await page.mouse.up();
  await expect(page.getByTestId("workflow-recovery-edge-rel.review-to-export")).toBeVisible();
  await expect(concept).toHaveAttribute("data-revision", "3");

  await page.getByTestId("workflow-recovery-edge-select-rel.review-to-export").click();
  await page.getByTestId("workflow-recovery-disconnect-rel.review-to-export").click();
  await expect(concept).toHaveAttribute("data-revision", "4");
  await sourceHandle.focus();
  await sourceHandle.press("Enter");
  await expect(page.getByRole("status")).toContainText("Connection started");
  await targetHandle.focus();
  await targetHandle.press("Enter");
  await expect(page.getByTestId("workflow-recovery-edge-rel.review-to-export")).toBeVisible();
  await expect(concept).toHaveAttribute("data-revision", "5");

  const revision = await concept.getAttribute("data-revision");
  await page.getByTestId("workflow-recovery-run-start").click();
  await expect(page.getByTestId("workflow-recovery-run-mode")).toContainText("SIMULATED RUN");
  await page.getByTestId("workflow-recovery-run-advance").click();
  await expect(page.getByTestId("workflow-recovery-block-block.generate-geometry")).toHaveAttribute("data-active", "true");
  await expect(page.getByTestId("workflow-recovery-edge-select-rel.brief-to-geometry")).toContainText("Active flow");
  await expect(concept).toHaveAttribute("data-revision", revision ?? "3");
});

test("promotes valid source and reviewed AI commands, recovers a run, and exposes lineage", async ({ page }) => {
  await mockRecoveryShell(page);
  await page.goto("/workflow-recovery");
  const concept = page.getByTestId("workflow-recovery-concept");
  await page.getByTestId("workflow-recovery-attachment-attach-artifact.brief").click();

  await page.getByTestId("workflow-recovery-view-code").click();
  const editor = page.getByTestId("workflow-recovery-source-editor");
  const source = await editor.inputValue();
  expect(source).toContain("Generate bracket geometry");
  await editor.fill(source.replace("Generate bracket geometry", "Generate bracket geometry v2"));
  await page.getByTestId("workflow-recovery-source-apply").click();
  await expect(concept).toHaveAttribute("data-revision", "2");
  await page.getByTestId("workflow-recovery-view-diagram").click();
  await expect(page.getByTestId("workflow-recovery-block-block.generate-geometry")).toContainText("Generate bracket geometry v2");

  await page.getByTestId("workflow-recovery-ai-request").click();
  await expect(page.getByTestId("workflow-recovery-proposal")).toHaveAttribute("data-base-revision", "2");
  await expect(page.getByTestId("workflow-recovery-proposal-preview")).toContainText("Create inspection drawing");
  await page.getByTestId("workflow-recovery-proposal-reject").click();
  await expect(concept).toHaveAttribute("data-revision", "2");
  await expect(page.getByTestId("workflow-recovery-block-block.create-inspection-drawing")).toHaveCount(0);

  await page.getByTestId("workflow-recovery-ai-request").click();
  await page.getByTestId("workflow-recovery-block-block.create-inspection-drawing").click();
  await expect(page.getByTestId("workflow-recovery-candidate-readonly")).toBeVisible();
  await page.getByTestId("workflow-recovery-proposal-accept").click();
  await expect(concept).toHaveAttribute("data-revision", "3");
  await expect(page.getByTestId("workflow-recovery-block-block.create-inspection-drawing")).toBeAttached();
  await expect(page.getByTestId("workflow-recovery-block-block.review-inspection-drawing")).toBeAttached();
  await expect(page.getByTestId("workflow-recovery-simulation-issue")).toContainText("six-block mounting-bracket fixture");
  await expect(page.getByTestId("workflow-recovery-run-start")).toBeDisabled();
  await page.getByTestId("workflow-recovery-undo").click();
  await expect(concept).toHaveAttribute("data-revision", "4");
  await expect(page.getByTestId("workflow-recovery-block-block.create-inspection-drawing")).toHaveCount(0);
  await expect(page.getByTestId("workflow-recovery-simulation-issue")).toContainText("exact mounting-bracket fixture facts");
  await page.getByTestId("workflow-recovery-undo").click();
  await expect(concept).toHaveAttribute("data-revision", "5");
  await expect(page.getByTestId("workflow-recovery-block-block.generate-geometry")).toContainText("Generate bracket geometry");

  await page.getByTestId("workflow-recovery-run-start").click();
  await expect(page.getByTestId("workflow-recovery-run-mode")).toContainText("queued");
  await page.getByTestId("workflow-recovery-run-advance").click();
  await page.getByTestId("workflow-recovery-run-advance").click();
  await expect(page.getByTestId("workflow-recovery-run-mode")).toContainText("needs-input");
  await expect(page.getByTestId("workflow-recovery-block-block.review-design")).toHaveAttribute("data-run-state", "blocked");
  await page.getByTestId("workflow-recovery-run-recover").click();
  await expect(page.getByTestId("workflow-recovery-run-mode")).toContainText("running");
  for (let index = 0; index < 4; index += 1) {
    await page.getByTestId("workflow-recovery-run-advance").click();
  }
  await expect(page.getByTestId("workflow-recovery-run-mode")).toContainText("succeeded");
  await expect(page.getByTestId("workflow-recovery-run-mode")).toContainText("workflow.mounting-bracket r5");
  await expect(concept).toHaveAttribute("data-revision", "5");

  await page.getByTestId("workflow-recovery-block-block.export-step").click();
  await page.getByTestId("workflow-recovery-inspector-tab-outputs").click();
  await page.getByTestId("workflow-recovery-output-artifact.step").click();
  await expect(page.getByRole("heading", { name: "Mounting bracket STEP output" })).toBeVisible();
  await expect(page.getByAltText("Isometric L-shaped mounting bracket with four holes")).toBeVisible();
  await expect(page.getByText("Static illustrative fixture", { exact: false })).toBeVisible();
  await expect(page.getByText(/Fixture sha256:bf316fa511f5e6a3312f03cb5b36184d91109185730defc41542b8805884be83/)).toBeVisible();
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
  await page.getByRole("button", { name: "Project failure" }).click();
  await page.getByTestId("workflow-recovery-block-block.export-step").click();
  await page.getByTestId("workflow-recovery-inspector-tab-outputs").click();
  await expect(page.getByTestId("workflow-recovery-output-artifact.step")).toHaveCount(0);
  await expect(page.getByTestId("workflow-recovery-block-block.release-package")).toHaveAttribute("data-run-state", "blocked");
  await expect(concept).toHaveAttribute("data-revision", "5");
});

test("keeps paired edits and the run overlay inside the local one-second feedback bound", async ({ page }) => {
  await mockRecoveryShell(page);
  await page.goto("/workflow-recovery");
  await page.getByTestId("workflow-recovery-attachment-attach-artifact.brief").click();
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
  await source.fill(current.replace("Generate bracket geometry", "Generate bracket geometry paired"));
  const textStarted = Date.now();
  await page.getByTestId("workflow-recovery-source-apply").click();
  await expect(page.getByTestId("workflow-recovery-block-block.generate-geometry")).toContainText("Generate bracket geometry paired", { timeout: 1000 });
  const textToGraphMs = Date.now() - textStarted;
  expect(textToGraphMs).toBeLessThan(1000);

  await page.getByTestId("workflow-recovery-undo").click();
  await page.getByTestId("workflow-recovery-undo").click();
  await page.getByTestId("workflow-recovery-run-start").click();
  const overlayStarted = Date.now();
  await page.getByTestId("workflow-recovery-run-advance").click();
  await expect(page.getByTestId("workflow-recovery-block-block.generate-geometry")).toHaveAttribute("data-active", "true", { timeout: 1000 });
  const runOverlayMs = Date.now() - overlayStarted;
  expect(runOverlayMs).toBeLessThan(1000);

  test.info().annotations.push({ type: "latency", description: `graph→text=${graphToTextMs}ms; text→graph=${textToGraphMs}ms; run-overlay=${runOverlayMs}ms; bound<1000ms` });
});

test("keeps concept states accessible, reduced-motion legible, and mobile-contained", async ({ page }) => {
  await page.emulateMedia({ reducedMotion: "reduce" });
  await mockRecoveryShell(page);
  await page.goto("/workflow-recovery");
  await expect(page.getByTestId("workflow-recovery-concept")).toBeVisible();
  await page.getByTestId("workflow-recovery-attachment-attach-artifact.brief").click();

  const serious = async () => (await new AxeBuilder({ page }).include('[data-testid="workflow-recovery-concept"]').analyze())
    .violations.filter((violation) => violation.impact === "serious" || violation.impact === "critical")
    .map((violation) => violation.id);
  expect(await serious()).toEqual([]);

  await page.getByRole("button", { name: "Port lab" }).click();
  expect(await serious()).toEqual([]);
  await page.getByRole("button", { name: "Close dialog" }).click();

  await page.getByTestId("workflow-recovery-run-start").click();
  await page.getByTestId("workflow-recovery-run-advance").click();
  const activeEdge = page.getByTestId("workflow-recovery-edge-rel.brief-to-geometry");
  await expect(activeEdge).toHaveAttribute("data-active", "true");
  const animationDuration = await activeEdge.locator("path.react-flow__edge-path").evaluate((element) => getComputedStyle(element).animationDuration);
  expect(["0s", "0.000001s", "1e-06s"]).toContain(animationDuration);
  await expect(page.getByTestId("workflow-recovery-edge-select-rel.brief-to-geometry")).toContainText("Active flow");

  await page.setViewportSize({ width: 390, height: 844 });
  await page.reload();
  await expect(page.getByTestId("workflow-recovery-concept")).toBeVisible();
  const overflow = await page.evaluate(() => ({ width: document.documentElement.scrollWidth, viewport: document.documentElement.clientWidth }));
  expect(overflow.width).toBeLessThanOrEqual(overflow.viewport);
  await expect(page.getByTestId("workflow-recovery-palette")).toBeVisible();
  await expect(page.getByTestId("workflow-recovery-inspector")).toBeVisible();
});
