import { test, expect } from "@playwright/test";

test.describe("Create Session Button E2E", () => {
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

    // Mock workspaces list
    await page.route('**/api/workspace/recent', async (route) => {
      await route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify({ workspaces: [] }),
      });
    });

    // Mock workspace by id
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
          updated_at: Math.floor(Date.now() / 1000)
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
          workspace_path: '/home/burhop/repos/wright'
        }),
      });
    });

    // Mock workspace files tree
    await page.route('**/api/workspace/files?*', async (route) => {
      await route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify({
          workspace: {
            name: 'wright',
            path: '/',
            type: 'directory',
            size: null,
            last_modified: 1000,
            git_status: 'Clean',
            children: []
          }
        }),
      });
    });

    // Mock workspace git status
    await page.route('**/api/workspace/git/status?*', async (route) => {
      await route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify({
          branch_name: 'main',
          is_clean: true,
          changes: []
        }),
      });
    });

    // Mock active agent
    await page.route('**/api/agent/active', async (route) => {
      await route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify({ agent: 'hermes' }),
      });
    });

    // Mock agent health
    await page.route('**/api/agent/health', async (route) => {
      await route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify({ state: 'connected', latencyMs: 5.0 }),
      });
    });

    // Mock inference health
    await page.route('**/api/inference/health', async (route) => {
      await route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify({ state: 'connected', latencyMs: 5.0 }),
      });
    });

    // Mock agent sessions list
    await page.route('**/api/agent/sessions*', async (route) => {
      await route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify({
          sessions: [
            { session_id: 'session-1', title: 'Session One', created_at: Date.now(), updated_at: Date.now() }
          ]
        }),
      });
    });

    // Mock tool lists
    await page.route('**/api/mcp/servers', async (route) => {
      await route.fulfill({ status: 200, contentType: 'application/json', body: JSON.stringify({ servers: [] }) });
    });
    await page.route('**/api/mcp/tools', async (route) => {
      await route.fulfill({ status: 200, contentType: 'application/json', body: JSON.stringify({ tools: [] }) });
    });

    // Mock API health
    await page.route('**/api/health', async (route) => {
      await route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify({ state: 'connected' }),
      });
    });
  });

  test("clicking '+' button successfully creates and selects a new session", async ({ page }) => {
    // Intercept session creation
    let sessionCreated = false;
    await page.route('**/api/agent/sessions/new', async (route) => {
      sessionCreated = true;
      await route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify({
          session_id: 'session-new-123',
          title: 'Session Two',
          created_at: Date.now()
        }),
      });
    });

    // Intercept workspace session association update
    let associationUpdatedPayload: any = null;
    await page.route('**/api/workspace/by-id/ws-1/session', async (route) => {
      associationUpdatedPayload = route.request().postDataJSON();
      await route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify({ success: true }),
      });
    });

    // Navigate to workspace page
    await page.goto('/workspace/ws-1');
    await expect(page.getByTestId('chat-layout')).toBeVisible();

    // Click the '+' button
    const plusBtn = page.getByTestId('create-session-btn');
    await expect(plusBtn).toBeVisible();
    await plusBtn.click();

    // Verify session creation was triggered
    expect(sessionCreated).toBe(true);

    // Verify database association update was requested with the correct session ID
    await expect.poll(() => associationUpdatedPayload).toEqual({ session_id: 'session-new-123' });
  });
});
