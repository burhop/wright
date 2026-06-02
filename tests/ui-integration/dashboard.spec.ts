import { test, expect } from '@playwright/test';

test.describe('Dashboard Page', () => {
  test('should load the dashboard and verify all layout regions render', async ({ page }) => {
    await page.goto('/');

    // Check title
    await expect(page).toHaveTitle('Wright');

    // Check layout shell regions
    await expect(page.getByTestId('app-shell')).toBeVisible();
    await expect(page.getByTestId('header')).toBeVisible();
    await expect(page.getByTestId('sidebar')).toBeVisible();
    await expect(page.getByTestId('status-bar')).toBeVisible();
    
    // Check main page content area
    await expect(page.getByTestId('page-dashboard')).toBeVisible();
    await expect(page.getByText(/Welcome to Wright/i)).toBeVisible();
  });
});
