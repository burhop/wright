import { test, expect } from '@playwright/test';

test.describe('Pluggable Viewer Panel Watchdog & Sandbox E2E', () => {
  test.beforeEach(async ({ page }) => {
    // Mock setup status
    await page.route('**/api/setup/status', async (route) => {
      await route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify({ is_configured: true, theme: 'dark' }),
      });
    });

    // Mock active agent
    await page.route('**/api/agent/active', async (route) => {
      await route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify('hermes'),
      });
    });

    // Mock agent sessions list
    await page.route('**/api/agent/sessions*', async (route) => {
      await route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify({
          sessions: [
            {
              session_id: 'session-1',
              title: 'Default Session',
              created_at: Date.now(),
              updated_at: Date.now(),
            },
          ],
        }),
      });
    });

    // Mock workspace info
    await page.route('**/api/workspace/by-id/*', async (route) => {
      await route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify({
          workspace_id: 'ws-1',
          session_id: 'session-1',
          workspace_name: 'Test Project',
          local_path: '/home/burhop/repos/wright',
          git_remote_url: null,
          git_username: null,
        }),
      });
    });

    // Mock workspace activation
    await page.route('**/api/workspace/activate', async (route) => {
      await route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify({
          success: true,
          session_id: 'session-1',
          workspace_path: '/home/burhop/repos/wright',
        }),
      });
    });

    // Mock file tree list with index.html
    await page.route('**/api/workspace/files?*', async (route) => {
      await route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify({
          workspace: {
            name: 'wright',
            path: '/',
            type: 'directory',
            children: [
              {
                name: 'index.html',
                path: '/index.html',
                type: 'file',
                size: 150,
                last_modified: 1000,
                git_status: 'Clean',
                children: null,
              },
            ],
          },
        }),
      });
    });

    // Mock html file contents
    await page.route('**/api/workspace/files/content?*', async (route) => {
      const url = new URL(route.request().url());
      const filePath = url.searchParams.get('path') || '';

      if (filePath.endsWith('.html')) {
        await route.fulfill({
          status: 200,
          contentType: 'text/html',
          body: `
            <!DOCTYPE html>
            <html>
            <head>
              <title>Sandbox Test Page</title>
            </head>
            <body>
              <h3>Hello Sandbox HTML Page</h3>
              <script>
                // Do not reply to ping message to trigger watchdog timeout
                window.addEventListener('message', (e) => {
                  console.log("Iframe received message in sandbox: ", e.data);
                });
              </script>
            </body>
            </html>
          `,
        });
      } else {
        await route.fulfill({
          status: 200,
          contentType: 'text/plain',
          body: 'Fallback content',
        });
      }
    });

    // Mock git status and history
    await page.route('**/api/workspace/git/status?*', async (route) => {
      await route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify({ branch_name: 'main', changes: [] }),
      });
    });
    await page.route('**/api/workspace/git/history?*', async (route) => {
      await route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify({ commits: [] }),
      });
    });
  });

  test('should verify sandbox attributes on iframe', async ({ page }) => {
    await page.goto('/workspace/ws-1');

    // Expand root folder
    const rootFolder = page.locator('[data-testid="file-node-/"]');
    await expect(rootFolder).toBeVisible();
    await rootFolder.click();

    // Click index.html
    const htmlFile = page.locator('[data-testid="file-node-/index.html"]');
    await expect(htmlFile).toBeVisible();
    await htmlFile.click();

    // Check iframe is mounted with correct sandbox permissions
    const sandboxIframe = page.locator('[data-testid="iframe-sandbox"]');
    await expect(sandboxIframe).toBeVisible();
    
    // Check sandbox attribute exists and is strictly safe (doesn't allow-same-origin)
    const sandboxAttr = await sandboxIframe.getAttribute('sandbox');
    expect(sandboxAttr).toContain('allow-scripts');
    expect(sandboxAttr).not.toContain('allow-same-origin');
  });

  test('should trigger unresponsive watchdog overlay when iframe does not pong', async ({ page }) => {
    await page.goto('/workspace/ws-1');

    // Expand root folder
    const rootFolder = page.locator('[data-testid="file-node-/"]');
    await expect(rootFolder).toBeVisible();
    await rootFolder.click();

    // Click index.html
    const htmlFile = page.locator('[data-testid="file-node-/index.html"]');
    await expect(htmlFile).toBeVisible();
    await htmlFile.click();

    // Verify watchdog overlay becomes visible after 5-6s (unresponsive trigger)
    const overlay = page.locator('[data-testid="watchdog-overlay"]');
    await expect(overlay).toBeVisible({ timeout: 10000 });

    // Click Close Tab button on overlay
    const closeBtn = page.locator('[data-testid="watchdog-close"]');
    await expect(closeBtn).toBeVisible();
    await closeBtn.click();

    // Verify tab and overlay are closed/removed
    await expect(overlay).not.toBeVisible();
    const htmlTab = page.locator('[data-testid="editor-tab-/index.html"]');
    await expect(htmlTab).not.toBeVisible();
  });

  test('should open, interact with, and close the Developer Tools diagnostics panel', async ({ page }) => {
    await page.goto('/workspace/ws-1');

    // Expand root folder
    const rootFolder = page.locator('[data-testid="file-node-/"]');
    await expect(rootFolder).toBeVisible();
    await rootFolder.click();

    // Click index.html
    const htmlFile = page.locator('[data-testid="file-node-/index.html"]');
    await expect(htmlFile).toBeVisible();
    await htmlFile.click();

    // Inspector toggle should be visible
    const inspectorToggle = page.locator('[data-testid="viewer-inspector-toggle"]');
    await expect(inspectorToggle).toBeVisible();
    await inspectorToggle.click();

    // Diagnostic panel should open
    const inspectorPanel = page.locator('[data-testid="viewer-inspector-panel"]');
    await expect(inspectorPanel).toBeVisible();

    // Verify diagnostic values
    await expect(inspectorPanel).toContainText('index.html');
    await expect(inspectorPanel).toContainText('iframe-viewer');
    await expect(inspectorPanel).toContainText('Isolated: Yes');

    // Verify watchdog state begins as RESPONSIVE
    const watchdogState = page.locator('[data-testid="inspector-watchdog-state"]');
    await expect(watchdogState).toHaveText('RESPONSIVE');

    // Close the panel using toggle
    await inspectorToggle.click();
    await expect(inspectorPanel).not.toBeVisible();

    // Reopen and close via panel close button
    await inspectorToggle.click();
    await expect(inspectorPanel).toBeVisible();

    const panelCloseBtn = page.locator('[data-testid="viewer-inspector-close"]');
    await expect(panelCloseBtn).toBeVisible();
    await panelCloseBtn.click();
    await expect(inspectorPanel).not.toBeVisible();
  });
});
