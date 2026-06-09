import { test, expect } from '@playwright/test';

test.describe('LLM Setup Flow', () => {
  let isConfiguredMock = false;

  test.beforeEach(async ({ page }) => {
    isConfiguredMock = false;

    // Mock setup status
    await page.route('**/api/setup/status', async (route) => {
      await route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify({
          is_configured: isConfiguredMock,
          llm_api_url: isConfiguredMock ? 'http://127.0.0.1:8000/api/health' : null,
          active_agent: 'hermes',
          theme: 'dark'
        }),
      });
    });

    // Mock setup health check
    await page.route('**/api/setup/health*', async (route) => {
      const url = new URL(route.request().url());
      const targetUrl = url.searchParams.get('url') || '';
      if (targetUrl.includes('invalid')) {
        await route.fulfill({
          status: 200,
          contentType: 'application/json',
          body: JSON.stringify({ status: 'unhealthy', latency_ms: 0.0, error: 'Connection Error' }),
        });
      } else {
        await route.fulfill({
          status: 200,
          contentType: 'application/json',
          body: JSON.stringify({ status: 'healthy', latency_ms: 10.5 }),
        });
      }
    });

    // Mock setup configure
    await page.route('**/api/setup/configure', async (route) => {
      isConfiguredMock = true;
      await route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify({ success: true, message: 'System configured successfully.' }),
      });
    });

    // Mock resetting
    await page.route('**/api/setup/reset', async (route) => {
      isConfiguredMock = false;
      await route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify({ success: true, message: 'Setup reset successfully.' }),
      });
    });

    // Mock basic dashboard dependencies
    await page.route('**/api/workspace/recent', async (route) => {
      await route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify({ workspaces: [] }),
      });
    });

    await page.route('**/api/agent/sessions', async (route) => {
      await route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify({ sessions: [] }),
      });
    });

    await page.route('**/api/logs*', async (route) => {
      await route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify({ logs: [] }),
      });
    });
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
    await expect(page.locator('text=Connected').filter({ hasNotText: 'Disconnected' })).toBeVisible({ timeout: 10000 });

    // 6. Submit the setup configuration
    const nextBtn = page.locator('button:has-text("Next")');
    await expect(nextBtn).toBeEnabled();
    await nextBtn.click();

    // 7. Verify redirection to Dashboard
    await expect(page.getByTestId('nav-dashboard')).toBeVisible({ timeout: 5000 });
  });
});
