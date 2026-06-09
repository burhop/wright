import { test, expect } from '@playwright/test';

test.describe('Dashboard Page', () => {
  test.beforeEach(async ({ page }) => {
    // Mock recent workspaces list
    await page.route('**/api/workspace/recent', async (route) => {
      await route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify({
          workspaces: [
            {
              workspace_id: 'ws-1',
              session_id: 'session-1',
              workspace_name: 'Test Project',
              local_path: '/home/burhop/repos/wright',
              git_remote_url: null,
              git_username: null,
              enabled_tools: ['CalculiX Simulation'],
              updated_at: Math.floor(Date.now() / 1000) - 300
            }
          ]
        }),
      });
    });

    // Mock all workspaces list
    await page.route('**/api/workspace/list', async (route) => {
      await route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify({
          workspaces: [
            {
              workspace_id: 'ws-1',
              session_id: 'session-1',
              workspace_name: 'Test Project',
              local_path: '/home/burhop/repos/wright',
              git_remote_url: null,
              git_username: null,
              enabled_tools: ['CalculiX Simulation'],
              updated_at: Math.floor(Date.now() / 1000) - 300
            }
          ]
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

    // Mock default directory path
    await page.route('**/api/workspace/default-dir', async (route) => {
      await route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify({ default_dir: '/home/burhop/wright' }),
      });
    });

    // Mock workspace creation
    await page.route('**/api/workspace/create', async (route) => {
      await route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify({
          workspace_id: 'ws-new',
          session_id: 'session-new',
          workspace_name: 'New Project',
          local_path: '/home/burhop/wright/new-project',
          git_remote_url: null,
          git_username: null,
          updated_at: Math.floor(Date.now() / 1000)
        }),
      });
    });

    // Mock get workspace by ID
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

    // Mock agent sessions
    await page.route('**/api/agent/sessions', async (route) => {
      await route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify({ sessions: [] }),
      });
    });

    // Mock tool list
    await page.route('**/api/mcp/servers', async (route) => {
      await route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify({ servers: [] }),
      });
    });
    await page.route('**/api/mcp/tools', async (route) => {
      await route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify({ tools: [] }),
      });
    });

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

  test('should load the dashboard layout and select an existing workspace', async ({ page }) => {
    await page.goto('/');

    // Check title
    await expect(page).toHaveTitle('Wright');

    // Verify main regions render
    await expect(page.getByTestId('app-shell')).toBeVisible();
    await expect(page.getByTestId('page-dashboard')).toBeVisible();
    await expect(page.getByText('Wright Design Hub')).toBeVisible();

    // Verify workspace card is present
    const workspaceCard = page.getByText('Test Project', { exact: false });
    await expect(workspaceCard).toBeVisible();

    // Clicking workspace card should navigate to workspace page
    await workspaceCard.click();
    await expect(page).toHaveURL(/\/workspace\/ws-1/);
    await expect(page.getByTestId('page-workspace')).toBeVisible();
  });

  test('should open Create Workspace modal and submit', async ({ page }) => {
    await page.goto('/');

    // Open Modal
    const createBtn = page.locator('#create-workspace-btn');
    await expect(createBtn).toBeVisible();
    await createBtn.click();

    // Verify Modal container is visible
    const modal = page.getByTestId('create-workspace-modal');
    await expect(modal).toBeVisible();

    const nameInput = page.locator('#workspace-name-input');
    const submitBtn = page.locator('#workspace-create-submit');

    await expect(nameInput).toBeVisible();
    await expect(submitBtn).toBeVisible();

    // Type name: 'FEA Simulation'
    await nameInput.fill('FEA Simulation');

    // Click submit
    await submitBtn.click();

    // Modal should close and navigate to the new workspace page
    await expect(modal).not.toBeVisible();
    await expect(page).toHaveURL(/\/workspace\/ws-new/);
    await expect(page.getByTestId('page-workspace')).toBeVisible();
  });
});
