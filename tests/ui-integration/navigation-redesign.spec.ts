import { test, expect } from "@playwright/test";

test.describe("UI Navigation Redesign E2E", () => {
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
          workspace_id: 'test-workspace-id',
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
  });

  test("should load the new global sidebar navigation items and page views", async ({ page }) => {
    // 1. Visit Dashboard
    await page.goto("/");
    await expect(page.getByTestId("nav-dashboard")).toBeVisible();
    await expect(page.getByTestId("nav-tool-registry")).toBeVisible();
    await expect(page.getByTestId("nav-logs")).toBeVisible();
    await expect(page.getByTestId("nav-settings")).toBeVisible();

    // 2. Click Logs link
    await page.getByTestId("nav-logs").click();
    await expect(page).toHaveURL("/logs");
    await expect(page.getByTestId("page-logs")).toBeVisible();

    // Verify filter elements exist on logs page
    await expect(page.getByTestId("logs-filter-workspace")).toBeVisible();
    await expect(page.getByTestId("logs-filter-level")).toBeVisible();
    await expect(page.getByTestId("logs-filter-search")).toBeVisible();
    await expect(page.getByTestId("logs-refresh-btn")).toBeVisible();

    // 3. Click Settings link
    await page.getByTestId("nav-settings").click();
    await expect(page).toHaveURL("/settings");
    await expect(page.getByTestId("page-settings")).toBeVisible();

    // Verify settings elements exist
    await expect(page.getByTestId("settings-llm-provider")).toBeVisible();
    await expect(page.getByTestId("settings-theme")).toBeVisible();
    await expect(page.getByTestId("settings-save-btn")).toBeVisible();
  });

  test("should display the redesigned workspace sidebar activity buttons inside a workspace", async ({ page }) => {
    // Go to dashboard
    await page.goto("/");

    // Click on a workspace card if present, or navigate directly to a mock workspace
    // Let's go directly to a mock workspace route
    await page.goto("/workspace/test-workspace-id");

    // Verify workspace panel is loaded
    await expect(page.getByTestId("workspace-panel")).toBeVisible();

    // Verify the 6 redesigned vertical buttons are visible
    await expect(page.getByTestId("activity-bar-back-btn")).toBeVisible();
    await expect(page.getByTestId("activity-bar-explorer-btn")).toBeVisible();
    await expect(page.getByTestId("activity-bar-mcp-btn")).toBeVisible();
    await expect(page.getByTestId("activity-bar-git-btn")).toBeVisible();
    await expect(page.getByTestId("activity-bar-settings-btn")).toBeVisible();
    await expect(page.getByTestId("activity-bar-docs-btn")).toBeVisible();

    // Click MCP button and check it displays MCP Tools Selector
    await page.getByTestId("activity-bar-mcp-btn").click();
    await expect(page.getByText("MCP Tools Selector")).toBeVisible();

    // Click Settings button and check it displays Workspace Settings
    await page.getByTestId("activity-bar-settings-btn").click();
    await expect(page.getByText("Workspace Settings")).toBeVisible();
    await expect(page.getByTestId("workspace-prompt-input")).toBeVisible();
    await expect(page.getByTestId("workspace-settings-git-threshold")).toBeVisible();

    // Click Docs button and check it displays Docs & Learning
    await page.getByTestId("activity-bar-docs-btn").click();
    await expect(page.getByText("Docs & Learning")).toBeVisible();
  });
});
