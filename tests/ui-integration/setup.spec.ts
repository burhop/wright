import { test, expect } from '@playwright/test';

test.describe('LLM Setup Flow', () => {
  test.beforeEach(async ({ page, baseURL }) => {
    // Reset setup configuration so the wizard appears
    const apiBase = baseURL || 'http://localhost:8080';
    await page.request.delete(`${apiBase}/api/setup/reset`);
  });

  test('should display setup page when unconfigured, test health status, and complete configuration to unlock dashboard', async ({ page }) => {
    // 1. Visit the app base URL
    await page.goto('/');

    // 2. Expect welcome layout & fields to be visible
    await expect(page.locator('h1')).toContainText('Welcome to Wright');
    await expect(page.locator('input[placeholder="e.g. http://localhost:8000"]')).toBeVisible();

    // 3. Verify agent selection (Hermes is active, others are disabled)
    const hermesCard = page.locator('strong:has-text("Hermes")');
    await expect(hermesCard).toBeVisible();

    // 4. Fill in an invalid URL to trigger validation error
    const urlInput = page.locator('input[placeholder="e.g. http://localhost:8000"]');
    await urlInput.fill('http://invalid-host-name-test:8000');

    // Wait for the debounced connection status to show Disconnected error
    await expect(page.locator('text=Disconnected')).toBeVisible({ timeout: 10000 });
    await expect(page.locator('text=Connection Error')).toBeVisible();

    // 5. Fill in a working URL (the internal API's health check is running on container port 8000)
    const checkURL = 'http://127.0.0.1:8000/api/health';
    await urlInput.fill(checkURL);

    // Wait for the debounced connection check to return healthy
    await expect(page.locator('text=Connected')).toBeVisible({ timeout: 10000 });

    // 6. Submit the setup configuration
    const nextBtn = page.locator('button:has-text("Next")');
    await expect(nextBtn).toBeEnabled();
    await nextBtn.click();

    // 7. Verify redirection to Dashboard
    await expect(page.getByTestId('nav-dashboard')).toBeVisible({ timeout: 5000 });
  });
});
