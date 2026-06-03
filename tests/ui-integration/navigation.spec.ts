import { test, expect } from '@playwright/test';

test.describe('Navigation', () => {
  test('should navigate to all sections successfully and persist URLs', async ({ page }) => {
    await page.goto('/');

    await expect(page.getByTestId('nav-dashboard')).toBeVisible();
    
    await page.getByTestId('nav-tool-registry').click();
    await expect(page).toHaveURL('/tool-registry');
    await expect(page.getByTestId('page-tool-registry')).toBeVisible();

    await page.getByTestId('nav-file-vault').click();
    await expect(page).toHaveURL('/file-vault');
    await expect(page.getByTestId('page-file-vault')).toBeVisible();

    await page.goto('/invalid-url');
    await expect(page.getByTestId('page-not-found')).toBeVisible();
    
    await page.getByTestId('back-to-dashboard-btn').click();
    await expect(page).toHaveURL('/');
  });
});
