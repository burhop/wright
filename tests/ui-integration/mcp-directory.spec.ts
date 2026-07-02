import { test, expect } from '@playwright/test';

test.describe('MCP Tool Registry Directory E2E Flow', () => {
  test('should register, list, toggle, and delete a custom MCP server', async ({ page }) => {
    // 1. Navigate to the tool registry page
    await page.goto('/tool-registry');
    await expect(page.getByRole('heading', { name: 'Engineering Tool Registry' })).toBeVisible();

    // 2. Check default seeded CalculiX card exists
    await expect(page.getByRole('heading', { name: 'CalculiX Simulation' })).toBeVisible();

    // 3. Click custom registration button
    await page.getByRole('button', { name: '+ Register Custom Tool' }).click();
    await expect(page.getByTestId('add-tool-modal-overlay')).toBeVisible();

    // 4. Fill form inputs
    const serverName = `Playwright Test CLI - ${Date.now()}`;
    await page.locator('#mcp-name').fill(serverName);
    await page.locator('#mcp-type').selectOption('stdio');
    await page.locator('#mcp-category').selectOption('simulation');
    await page.locator('#mcp-command').fill('python scripts/dummy.py');

    // 5. Submit registration
    await page.getByRole('button', { name: 'Register', exact: true }).click();

    // 6. Verify card is displayed in the list
    await expect(page.getByRole('heading', { name: serverName })).toBeVisible();

    // 7. Test removing/deleting the custom server card
    // Set up a listener for the window confirmation prompt
    page.once('dialog', async (dialog) => {
      expect(dialog.message()).toContain('Are you sure you want to remove');
      await dialog.accept();
    });

    // Click remove link on our newly created card
    const card = page.locator('[data-testid^="server-card-"]').filter({ hasText: serverName });
    await card.getByRole('button', { name: /Show details/ }).click();
    const removeBtn = card.getByRole('button', { name: 'Remove' });
    await expect(removeBtn).toBeVisible();
    await removeBtn.click();

    // Verify card is removed from directory
    await expect(page.getByRole('heading', { name: serverName })).not.toBeVisible();
  });
});
