import { expect, test, type Page } from "@playwright/test";
import AxeBuilder from "@axe-core/playwright";

async function mockRecoveryShell(page: Page): Promise<void> {
  await page.route("**/api/**", async (route) => {
    const path = new URL(route.request().url()).pathname;
    if (path === "/api/auth/session/status") return route.fulfill({ json: { auth_required: false, authenticated: true } });
    if (path === "/api/setup/status") return route.fulfill({ json: { is_configured: true, active_agent: "hermes", theme: "dark" } });
    if (path === "/api/mcp/servers") return route.fulfill({ json: { servers: [] } });
    if (path === "/api/mcp/tools") return route.fulfill({ json: { tools: [] } });
    if (path === "/api/agent/sessions") return route.fulfill({ json: { sessions: [] } });
    if (path === "/api/workspace/recent" || path === "/api/workspace/list") return route.fulfill({ json: { workspaces: [] } });
    if (path.endsWith("/health")) return route.fulfill({ json: { state: "connected", latencyMs: 1 } });
    return route.fulfill({ status: 404, json: { detail: "Unmocked recovery-shell API" } });
  });
}

function focusIdentity(page: Page): Promise<string> {
  return page.evaluate(() => {
    const active = document.activeElement as HTMLElement | null;
    if (active === null) return "none";
    return active.dataset.testid ?? active.getAttribute("aria-label") ?? active.textContent?.trim().slice(0, 80) ?? active.tagName;
  });
}

test("supports representative authoring and component inspection with keyboard actions and ordered focus", async ({ page }) => {
  await mockRecoveryShell(page);
  await page.goto("/workflow-recovery");
  const concept = page.getByTestId("workflow-recovery-concept");
  await expect(concept).toBeVisible();

  const ordered: string[] = [];
  await page.getByTestId("workflow-recovery-view-diagram").focus();
  ordered.push(await focusIdentity(page));
  for (let index = 0; index < 12; index += 1) {
    await page.keyboard.press("Tab");
    ordered.push(await focusIdentity(page));
  }
  const orderOf = (identity: string) => ordered.indexOf(identity);
  expect(orderOf("workflow-recovery-view-diagram")).toBe(0);
  expect(orderOf("workflow-recovery-view-code")).toBeGreaterThan(orderOf("workflow-recovery-view-diagram"));
  expect(orderOf("workflow-recovery-view-split")).toBeGreaterThan(orderOf("workflow-recovery-view-code"));
  expect(orderOf("workflow-recovery-validate")).toBeGreaterThan(orderOf("workflow-recovery-view-split"));
  expect(orderOf("workflow-recovery-port-lab-open")).toBeGreaterThan(orderOf("workflow-recovery-validate"));
  expect(orderOf("workflow-recovery-ai-request")).toBeGreaterThan(orderOf("workflow-recovery-port-lab-open"));
  expect(orderOf("workflow-recovery-palette-search")).toBeGreaterThan(orderOf("workflow-recovery-ai-request"));

  const componentNode = page.getByTestId("workflow-recovery-block-block.review-design");
  const componentToggle = page.getByTestId("workflow-recovery-component-toggle-block.review-design");
  const componentKeyboard = page.getByTestId("workflow-recovery-component-keyboard-block.review-design");
  await componentKeyboard.focus();
  await expect(componentKeyboard).toBeFocused();
  await expect(componentNode).toHaveAttribute("aria-expanded", "false");
  await page.keyboard.press("Enter");
  await expect(componentKeyboard).toHaveAttribute("aria-expanded", "true");
  await expect(componentToggle).toHaveAttribute("aria-expanded", "true");
  await expect(componentNode).toHaveAttribute("aria-expanded", "true");
  await expect(page.getByTestId("workflow-recovery-component-addresses-block.review-design"))
    .toContainText("component.review-cell.relationship.accept");

  const find = page.getByTestId("workflow-recovery-find-input");
  await find.focus();
  await page.keyboard.type("block.export-step");
  await page.keyboard.press("Enter");
  await expect(page.getByRole("status", { name: "" }).filter({ hasText: "Focused Export STEP" })).toBeVisible();
  await expect(page.getByTestId("workflow-recovery-inspector")).toContainText("block.export-step");

  const edge = page.getByTestId("workflow-recovery-edge-select-rel.review-to-export");
  await edge.focus();
  await page.keyboard.press("Enter");
  const disconnect = page.getByTestId("workflow-recovery-disconnect-rel.review-to-export");
  await disconnect.focus();
  await page.keyboard.press("Enter");
  await expect(page.getByTestId("workflow-recovery-edge-rel.review-to-export")).toHaveCount(0);
  const source = page.getByTestId("workflow-recovery-handle-port.approved-geometry-out");
  const target = page.getByTestId("workflow-recovery-handle-port.approved-geometry-in");
  await source.focus();
  await page.keyboard.press("Enter");
  await expect(page.getByRole("status")).toContainText("Connection started");
  await target.focus();
  await page.keyboard.press("Enter");
  await expect(page.getByTestId("workflow-recovery-edge-rel.review-to-export")).toBeVisible();

  const portLab = page.getByTestId("workflow-recovery-port-lab-open");
  await portLab.focus();
  await page.keyboard.press("Enter");
  const dialog = page.getByRole("dialog", { name: "Port interaction lab" });
  await expect(dialog).toBeVisible();
  await expect(page.getByTestId("workflow-recovery-modal-close")).toBeFocused();
  await page.keyboard.press("Shift+Tab");
  expect(await page.evaluate(() => document.activeElement?.closest('[role="dialog"]') !== null)).toBe(true);
  await page.keyboard.press("Escape");
  await expect(dialog).toHaveCount(0);
  await expect(portLab).toBeFocused();
});

test("keeps the complete screen-reader contract available at a two-times page scale", async ({ page, context }) => {
  await mockRecoveryShell(page);
  await page.setViewportSize({ width: 720, height: 550 });
  await page.goto("/workflow-recovery");

  const chromiumSession = await context.newCDPSession(page);
  await chromiumSession.send("Emulation.setPageScaleFactor", { pageScaleFactor: 2 });
  await expect.poll(() => page.evaluate(() => window.visualViewport?.scale ?? 1)).toBe(2);

  const concept = page.getByTestId("workflow-recovery-concept");
  await expect(page.getByRole("heading", { level: 1, name: "Mounting bracket workflow" })).toBeVisible();
  await expect(page.getByRole("tablist", { name: "Workflow view" })).toBeVisible();
  await expect(page.getByRole("tablist", { name: "Inspector sections" })).toBeVisible();
  await expect(page.getByLabel("Mounting bracket workflow diagram")).toBeVisible();
  await expect(page.getByRole("button", { name: "Connect from Approved geometry output" })).toBeVisible();
  await expect(page.getByRole("button", { name: "Inspect Approved geometry output artifact" })).toBeVisible();
  await expect(page.getByRole("button", { name: "Fit workflow to view" })).toBeVisible();

  const aria = await concept.ariaSnapshot();
  expect(aria).toContain('heading "Mounting bracket workflow" [level=1]');
  expect(aria).toContain('tablist "Workflow view"');
  expect(aria).toContain('button "Expand"');
  expect(aria).toContain('button "Connect from Approved geometry output"');
  expect(aria).toContain('button "Inspect Approved geometry output artifact"');

  const serious = (await new AxeBuilder({ page }).include('[data-testid="workflow-recovery-concept"]').analyze())
    .violations.filter((violation) => violation.impact === "serious" || violation.impact === "critical")
    .map((violation) => violation.id);
  expect(serious).toEqual([]);

  const geometry = await page.evaluate(() => ({
    documentWidth: document.documentElement.scrollWidth,
    layoutViewportWidth: document.documentElement.clientWidth,
    visualViewportWidth: window.visualViewport?.width ?? 0,
    scale: window.visualViewport?.scale ?? 1,
  }));
  expect(geometry.documentWidth).toBeLessThanOrEqual(geometry.layoutViewportWidth);
  expect(geometry.visualViewportWidth).toBeGreaterThan(0);
  expect(geometry.scale).toBe(2);
});
