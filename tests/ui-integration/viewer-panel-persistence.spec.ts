import { test, expect } from '@playwright/test';

test.describe('Pluggable Viewer Panel Persistence & Transaction History E2E', () => {
  const savePayloads: any[] = [];
  const backupPayloads: any[] = [];
  const deleteBackupPayloads: any[] = [];

  test.beforeEach(async ({ page }) => {
    savePayloads.length = 0;
    backupPayloads.length = 0;
    deleteBackupPayloads.length = 0;

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

    // Mock file tree list
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
                name: 'script.py',
                path: '/script.py',
                type: 'file',
                size: 200,
                last_modified: 1000,
                git_status: 'Clean',
                children: null,
              },
            ],
          },
        }),
      });
    });

    // Mock file contents (GET) and save (PUT)
    await page.route('**/api/workspace/files/content?*', async (route) => {
      const url = new URL(route.request().url());
      const filePath = url.searchParams.get('path') || '';

      if (filePath.endsWith('.py')) {
        await route.fulfill({
          status: 200,
          contentType: 'text/plain',
          body: "print('Hello Playwright Persistence')",
        });
      } else {
        await route.fulfill({
          status: 200,
          contentType: 'text/plain',
          body: 'Fallback content',
        });
      }
    });

    await page.route('**/api/workspace/files/content', async (route) => {
      if (route.request().method() === 'PUT') {
        const body = JSON.parse(route.request().postData() || '{}');
        savePayloads.push(body);
        await route.fulfill({
          status: 200,
          contentType: 'application/json',
          body: JSON.stringify({ success: true }),
        });
      } else {
        await route.fallback();
      }
    });

    // Mock backup POST and DELETE
    await page.route('**/api/workspace/files/backup', async (route) => {
      if (route.request().method() === 'POST') {
        const body = JSON.parse(route.request().postData() || '{}');
        backupPayloads.push(body);
        await route.fulfill({
          status: 200,
          contentType: 'application/json',
          body: JSON.stringify({ success: true, backup_id: 'mock-backup-123' }),
        });
      } else if (route.request().method() === 'DELETE') {
        const body = JSON.parse(route.request().postData() || '{}');
        deleteBackupPayloads.push(body);
        await route.fulfill({
          status: 200,
          contentType: 'application/json',
          body: JSON.stringify({ success: true }),
        });
      } else {
        await route.fallback();
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

  test('should handle dirty indicator, backup, and save on Ctrl+S shortcut', async ({ page }) => {
    await page.goto('/workspace/ws-1');

    // Expand root folder
    const rootFolder = page.locator('[data-testid="file-node-/"]');
    await expect(rootFolder).toBeVisible();
    await rootFolder.click();

    // Click python file
    const pyFile = page.locator('[data-testid="file-node-/script.py"]');
    await expect(pyFile).toBeVisible();
    await pyFile.click();

    // Check textarea is mounted
    const textarea = page.locator('[data-testid="viewer-container"] textarea');
    await expect(textarea).toBeVisible();
    await expect(textarea).toHaveValue("print('Hello Playwright Persistence')");

    // Make edit
    await textarea.fill("print('Hello Playwright Persistence Edited')");

    // Dirty badge or save button should appear
    const saveButton = page.locator('button:has-text("Save Changes")');
    await expect(saveButton).toBeVisible();

    // Verify a backup request was dispatched
    expect(backupPayloads.length).toBeGreaterThan(0);
    expect(backupPayloads[0].path).toBe('/script.py');
    expect(backupPayloads[0].content).toBe("print('Hello Playwright Persistence Edited')");

    // Press Ctrl+S
    await textarea.focus();
    await page.keyboard.press('Control+s');

    // Save button should hide as it is clean now
    await expect(saveButton).not.toBeVisible();

    // Verify save request details
    expect(savePayloads.length).toBe(1);
    expect(savePayloads[0].path).toBe('/script.py');
    expect(savePayloads[0].content).toBe("print('Hello Playwright Persistence Edited')");
  });

  test('should handle revert edits to clear dirty changes', async ({ page }) => {
    await page.goto('/workspace/ws-1');

    // Expand root folder
    const rootFolder = page.locator('[data-testid="file-node-/"]');
    await expect(rootFolder).toBeVisible();
    await rootFolder.click();

    // Click python file
    const pyFile = page.locator('[data-testid="file-node-/script.py"]');
    await expect(pyFile).toBeVisible();
    await pyFile.click();

    const textarea = page.locator('[data-testid="viewer-container"] textarea');
    await expect(textarea).toBeVisible();

    // Make edit to make dirty
    await textarea.fill("print('Hello Playwright Persistence Temporary Edit')");

    const saveButton = page.locator('button:has-text("Save Changes")');
    await expect(saveButton).toBeVisible();

    // Undo native action or focus and press Control+z
    await textarea.focus();
    await page.keyboard.press('Control+z');

    // Verify it reverts content and clears dirty flag (hides save button)
    await expect(saveButton).not.toBeVisible();
    await expect(textarea).toHaveValue("print('Hello Playwright Persistence')");
  });
});
