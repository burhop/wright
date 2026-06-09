import { test, expect } from '@playwright/test';

test.describe('Navigation', () => {
  test.beforeEach(async ({ page }) => {
    // Mock setup status
    await page.route('**/api/setup/status', async (route) => {
      await route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify({
          is_configured: true,
          llm_api_url: 'http://localhost:8000',
          active_agent: 'hermes',
          theme: 'dark'
        }),
      });
    });
  });

  test('should navigate to all sections successfully and persist URLs', async ({ page }) => {
    await page.goto('/');

    await expect(page.getByTestId('nav-dashboard')).toBeVisible();
    
    await page.getByTestId('nav-tool-registry').click();
    await expect(page).toHaveURL('/tool-registry');
    await expect(page.getByTestId('page-tool-registry')).toBeVisible();

    await page.getByTestId('nav-logs').click();
    await expect(page).toHaveURL('/logs');
    await expect(page.getByTestId('page-logs')).toBeVisible();

    await page.getByTestId('nav-settings').click();
    await expect(page).toHaveURL('/settings');
    await expect(page.getByTestId('page-settings')).toBeVisible();

    await page.goto('/invalid-url');
    await expect(page.getByTestId('page-not-found')).toBeVisible();
    
    await page.getByTestId('back-to-dashboard-btn').click();
    await expect(page).toHaveURL('/');
  });
});
