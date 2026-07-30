import { test, expect } from '@playwright/test';

const baseUrl = process.env.WRIGHT_MCP_PLAYWRIGHT_BASE_URL;

test.describe('MCP appliance prompt workflow @live', () => {
  test.skip(!baseUrl, 'Set WRIGHT_MCP_PLAYWRIGHT_BASE_URL to test a running MCP appliance');

  test('opens Wright and can submit MCP-oriented prompts', async ({ page }) => {
    await page.goto(baseUrl ?? '/');

    await expect(page.locator('body')).toContainText(/Wright|Dashboard|Workspace|Chat/i);

    if ((await page.getByTestId('composer-input').count()) === 0) {
      await page.getByTestId('create-workspace-btn').click();
      await expect(page.getByTestId('create-workspace-modal')).toBeVisible();
      await page.locator('#workspace-name-input').fill(`MCP appliance ${Date.now()}`);
      await page.locator('#workspace-create-submit').click();
      await expect(page).toHaveURL(/\/workspace\//, { timeout: 15000 });
      await expect(page.getByTestId('page-workspace')).toBeVisible({ timeout: 15000 });
    }

    const composer = page
      .getByTestId('composer-input')
      .or(page.getByRole('textbox'))
      .first();

    await expect(composer).toBeVisible({ timeout: 30000 });
    const prompt =
      'List the MCP servers attached to this workspace and check health for OpenSCAD, FreeCAD, BREP, SolidEdgeMCP, and Playwright.';
    await composer.fill(prompt);

    const send = page
      .getByTestId('composer-send')
      .or(page.getByRole('button', { name: /send|submit/i }))
      .first();
    await send.click();

    await expect(page.locator('body')).toContainText(/OpenSCAD|FreeCAD|BREP|SolidEdgeMCP|Playwright|Hermes/i, {
      timeout: 60000,
    });
  });
});
