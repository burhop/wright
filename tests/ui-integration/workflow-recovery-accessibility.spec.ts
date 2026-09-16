import { expect, test, type Page } from "@playwright/test";
import AxeBuilder from "@axe-core/playwright";

import {
  mockRecoveryWorkspace,
  openRecoveryEditor,
} from "./fixtures/workflow-recovery";

function focusIdentity(page: Page): Promise<string> {
  return page.evaluate(() => {
    const active = document.activeElement as HTMLElement | null;
    if (active === null) return "none";
    return (
      active.dataset.testid ??
      active.getAttribute("aria-label") ??
      active.textContent?.trim().slice(0, 80) ??
      active.tagName
    );
  });
}

test("supports representative authoring and component inspection with keyboard actions and ordered focus", async ({
  page,
}) => {
  await mockRecoveryWorkspace(page);
  await openRecoveryEditor(page);
  const concept = page.getByTestId("workflow-recovery-concept");
  await expect(concept).toBeVisible();
  await page
    .getByTestId("workflow-recovery-block-block.generate-geometry")
    .click();

  const ordered: string[] = [];
  await page.getByTestId("workflow-recovery-view-diagram").focus();
  ordered.push(await focusIdentity(page));
  for (let index = 0; index < 12; index += 1) {
    await page.keyboard.press("Tab");
    ordered.push(await focusIdentity(page));
  }
  const orderOf = (identity: string) => ordered.indexOf(identity);
  expect(orderOf("workflow-recovery-view-diagram")).toBe(0);
  expect(orderOf("workflow-recovery-view-code")).toBeGreaterThan(
    orderOf("workflow-recovery-view-diagram"),
  );
  expect(orderOf("workflow-recovery-view-split")).toBeGreaterThan(
    orderOf("workflow-recovery-view-code"),
  );
  expect(orderOf("workflow-recovery-validate")).toBeGreaterThan(
    orderOf("workflow-recovery-view-split"),
  );
  expect(orderOf("workflow-recovery-ai-request")).toBeGreaterThan(
    orderOf("workflow-recovery-validate"),
  );
  await expect(
    page.getByTestId("workflow-recovery-palette-search"),
  ).toHaveCount(0);

  const componentNode = page.getByTestId(
    "workflow-recovery-block-block.review-design",
  );
  const componentToggle = page.getByTestId(
    "workflow-recovery-component-toggle-block.review-design",
  );
  await componentToggle.focus();
  await expect(componentToggle).toBeFocused();
  await expect(componentNode).toHaveAttribute("aria-expanded", "false");
  await page.keyboard.press("Enter");
  await expect(componentToggle).toHaveAttribute("aria-expanded", "true");
  await expect(componentNode).toHaveAttribute("aria-expanded", "true");
  await expect(
    page.getByTestId(
      "workflow-recovery-component-addresses-block.review-design",
    ),
  ).toContainText("Accept the reviewed design");

  await expect(page.getByTestId("workflow-recovery-find-input")).toHaveCount(0);
  const exportStep = page.getByTestId(
    "workflow-recovery-block-block.export-step",
  );
  await exportStep.focus();
  await page.keyboard.press("Enter");
  await expect(page.getByTestId("workflow-recovery-inspector")).toContainText(
    "Export approved model as STEP AP242",
  );

  const edge = page.getByTestId(
    "workflow-recovery-edge-select-rel.review-to-export",
  );
  await edge.focus();
  await page.keyboard.press("Enter");
  const disconnect = page.getByTestId(
    "workflow-recovery-disconnect-rel.review-to-export",
  );
  await disconnect.focus();
  await page.keyboard.press("Enter");
  await expect(
    page.getByTestId("workflow-recovery-edge-rel.review-to-export"),
  ).toHaveCount(0);
  const source = page.getByTestId(
    "workflow-recovery-handle-port.approved-geometry-out",
  );
  const target = page.getByTestId(
    "workflow-recovery-handle-port.approved-geometry-in",
  );
  await source.focus();
  await page.keyboard.press("Enter");
  await expect(
    page.getByRole("status").filter({ hasText: "Connection started" }),
  ).toContainText("Connection started");
  await target.focus();
  await page.keyboard.press("Enter");
  await expect(
    page.getByTestId("workflow-recovery-edge-rel.review-to-export"),
  ).toBeVisible();

  await expect(page.getByTestId("workflow-recovery-run-mode")).toHaveCount(0);
});

test("keeps the complete screen-reader contract available at a two-times page scale", async ({
  page,
  context,
}) => {
  await mockRecoveryWorkspace(page);
  await openRecoveryEditor(page);
  await page.setViewportSize({ width: 720, height: 550 });
  await page.getByTestId("workspace-pane-surface").click();

  const chromiumSession = await context.newCDPSession(page);
  await chromiumSession.send("Emulation.setPageScaleFactor", {
    pageScaleFactor: 2,
  });
  await expect
    .poll(() => page.evaluate(() => window.visualViewport?.scale ?? 1))
    .toBe(2);

  const concept = page.getByTestId("workflow-recovery-concept");
  await expect(
    page.getByRole("heading", {
      level: 1,
      name: "Mounting bracket development",
    }),
  ).toBeVisible();
  await expect(page.getByTestId("workflow-recovery-view-select")).toBeVisible();
  await expect(
    page.getByRole("tablist", { name: "Step detail sections" }),
  ).toHaveCount(0);
  await expect(
    page.getByLabel("Mounting bracket development diagram"),
  ).toBeVisible();
  await expect(
    page.getByRole("button", {
      name: "Connect from Approved CAD model output",
    }),
  ).toBeVisible();
  await expect(
    page.getByRole("button", { name: "Open Approved CAD model output" }),
  ).toHaveCount(0);
  await expect(
    page.getByRole("button", { name: "Fit workflow to view" }),
  ).toBeVisible();
  await page.getByTestId("workflow-recovery-block-block.review-design").focus();
  await page.keyboard.press("Enter");
  await expect(page.getByTestId("workflow-recovery-inspector")).toContainText(
    "Approved CAD model",
  );

  const aria = await concept.ariaSnapshot();
  expect(aria).toContain('heading "Mounting bracket development" [level=1]');
  expect(aria).toContain('combobox "Workflow view"');
  expect(aria).toContain('button "Connect from Approved CAD model output"');
  expect(aria).not.toContain('button "Open Approved CAD model output"');

  const serious = (
    await new AxeBuilder({ page })
      .include('[data-testid="workflow-recovery-concept"]')
      .analyze()
  ).violations
    .filter(
      (violation) =>
        violation.impact === "serious" || violation.impact === "critical",
    )
    .map((violation) => violation.id);
  expect(serious).toEqual([]);

  const geometry = await page.evaluate(() => ({
    documentWidth: document.documentElement.scrollWidth,
    layoutViewportWidth: document.documentElement.clientWidth,
    visualViewportWidth: window.visualViewport?.width ?? 0,
    scale: window.visualViewport?.scale ?? 1,
  }));
  expect(geometry.documentWidth).toBeLessThanOrEqual(
    geometry.layoutViewportWidth,
  );
  expect(geometry.visualViewportWidth).toBeGreaterThan(0);
  expect(geometry.scale).toBe(2);
});
