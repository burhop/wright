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
  });

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

  test('should allow searching and selecting a workspace from the dropdown', async ({ page }) => {
    await page.goto('/');

    // Verify workspace switcher is visible
    await expect(page.getByRole('heading', { name: 'Engineering Workspaces' })).toBeVisible();

    // Click on the VS Code-style dropdown trigger
    const dropdownTrigger = page.getByText('Open Workspace...');
    await expect(dropdownTrigger).toBeVisible();
    await dropdownTrigger.click();

    // Wait for the dropdown container search input to appear and focus
    const searchInput = page.getByPlaceholder('Search workspaces by folder or path...');
    await expect(searchInput).toBeVisible();

    // Type a query (e.g., 'wright' or any part of the path)
    await searchInput.fill('wright');

    // Wait for filtered workspaces and click the first option
    const firstOption = page.locator('.dropdown-item').first();
    await expect(firstOption).toBeVisible();
    
    const optionText = await firstOption.innerText();
    console.log(`Selecting workspace option: ${optionText.replace('\n', ' - ')}`);

    await firstOption.click();

    // Selecting a workspace should trigger navigation to agent chat page
    await expect(page).toHaveURL('/agent-chat');
    await expect(page.getByTestId('page-agent-chat')).toBeVisible();
  });
});

