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
          local_path: '/tmp/wright-e2e-workspace',
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
          workspace_path: '/tmp/wright-e2e-workspace'
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

    // Mock API health status
    await page.route('**/api/health', async (route) => {
      await route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify({ state: 'connected' }),
      });
    });

    // Mock recent logs (default empty)
    await page.route('**/api/logs?level=error&limit=3', async (route) => {
      await route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify({ logs: [], total: 0 }),
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

  test("should display the condensed dashboard cards with health statuses and system telemetry", async ({ page }) => {
    // Mock workspaces list on dashboard
    await page.route('**/api/workspace/recent', async (route) => {
      await route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify({
          workspaces: [
            {
              workspace_id: 'test-workspace-id',
              session_id: 'session-1',
              workspace_name: 'Test Project',
              local_path: '/tmp/wright-e2e-workspace',
              git_remote_url: 'https://github.com/burhop/wright.git',
              git_username: 'burhop',
              updated_at: Math.floor(Date.now() / 1000) - 120
            }
          ]
        }),
      });
    });

    // Mock logs with error level for system health log list
    await page.route('**/api/logs?level=error&limit=3', async (route) => {
      await route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify({
          logs: [
            {
              timestamp: '2026-06-09T15:00:16.123456',
              level: 'error',
              message: 'CalculiX solver failed to converge: exit code 1',
              logger: 'wright.core.solver',
              trace_id: 'trace-123'
            }
          ],
          total: 1
        }),
      });
    });

    // Mock agent sessions count
    await page.route('**/api/agent/sessions', async (route) => {
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

    await page.goto("/");

    // Verify workspace card details
    await expect(page.getByTestId("card-workspaces")).toBeVisible();
    await expect(page.getByTestId("card-workspace-test-workspace-id")).toBeVisible();
    await expect(page.getByText("Test Project")).toBeVisible();

    // Verify agent status card details
    const agentCard = page.getByTestId("card-agent-status");
    await expect(agentCard).toBeVisible();
    await expect(agentCard.getByText("Wright API: connected")).toBeVisible();
    await expect(agentCard.getByText("Hermes: connected")).toBeVisible();
    await expect(agentCard.getByText("Inference Engine: connected")).toBeVisible();
    await expect(agentCard.getByText("wright.core.solver: CalculiX solver failed to converge")).toBeVisible();

    // Verify updates / news card details
    await expect(page.getByTestId("card-news")).toBeVisible();
    await expect(page.getByText("v0.22.0 Release Modernized Navigation")).toBeVisible();

    // Verify system telemetry card details
    const telemetryCard = page.getByTestId("card-telemetry");
    await expect(telemetryCard).toBeVisible();
    await expect(telemetryCard.getByText("state.db")).toBeVisible();
    await expect(telemetryCard.getByText("Active Agent Chat Sessions:")).toBeVisible();
  });

  test("should support logs filtering and launching Hermes Diagnostic drawer via selection context menu", async ({ page }) => {
    // Mock workspaces list for filter dropdown
    await page.route('**/api/workspace/list', async (route) => {
      await route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify({
          workspaces: [
            {
              workspace_id: 'test-workspace-id',
              session_id: 'session-1',
              workspace_name: 'Test Project',
              local_path: '/tmp/wright-e2e-workspace',
              git_remote_url: null,
              git_username: null,
              updated_at: Math.floor(Date.now() / 1000)
            }
          ]
        }),
      });
    });

    // Mock logs list for logs viewer table
    await page.route('**/api/logs?*', async (route) => {
      await route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify({
          logs: [
            {
              timestamp: '2026-06-09T15:00:16.123456',
              level: 'info',
              message: 'Starting stiffness equations solving',
              logger: 'wright.core.analysis',
              trace_id: 'trace-123'
            },
            {
              timestamp: '2026-06-09T15:00:18.654321',
              level: 'error',
              message: 'CalculiX solver failed to converge: exit code 1',
              logger: 'wright.core.solver',
              trace_id: 'trace-123'
            }
          ],
          total: 2
        }),
      });
    });

    // Mock creation of diagnostic session
    await page.route('**/api/agent/sessions/new', async (route) => {
      await route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify({
          session_id: 'session-debug-123',
          title: 'Diagnostic Session',
          created_at: Date.now()
        }),
      });
    });

    // Mock chat turn streaming
    await page.route('**/api/agent/chat', async (route) => {
      if (route.request().method() === 'POST') {
        await route.fulfill({
          status: 200,
          contentType: 'text/event-stream; charset=utf-8',
          headers: {
            'Cache-Control': 'no-cache',
            'Connection': 'keep-alive',
          },
          body: [
            'event: token\n',
            'data: {"text": "This solver error happens when CalculiX solver is terminated abruptly. Check boundary constraints."}\n\n',
            'event: stream_end\n',
            'data: {"session_id": "session-debug-123"}\n\n'
          ].join(''),
        });
      } else {
        await route.fallback();
      }
    });

    // Navigate directly to Logs page
    await page.goto("/logs");
    await expect(page.getByTestId("page-logs")).toBeVisible();

    // Verify filter elements
    await expect(page.getByTestId("logs-filter-workspace")).toBeVisible();
    await expect(page.getByTestId("logs-filter-level")).toBeVisible();
    await expect(page.getByTestId("logs-filter-search")).toBeVisible();

    // Verify logs rows are rendered
    const errorCell = page.locator('table tbody tr').nth(1).locator('td').nth(3);
    await expect(errorCell).toContainText('CalculiX solver failed to converge');

    // Simulate selecting the error log message text
    await errorCell.evaluate((node) => {
      const selection = window.getSelection();
      const range = document.createRange();
      range.selectNodeContents(node);
      selection?.removeAllRanges();
      selection?.addRange(range);
    });

    // Trigger right-click context menu
    await errorCell.dispatchEvent('contextmenu');

    const contextMenu = page.getByTestId('logs-context-menu');
    await expect(contextMenu).toBeVisible();

    const sendBtn = page.getByTestId('logs-context-send-btn');
    await expect(sendBtn).toBeVisible();
    await sendBtn.click();

    // Verify sliding diagnostic drawer opens and displays LLM response
    const drawer = page.getByTestId('logs-debug-drawer');
    await expect(drawer).toBeVisible();
    await expect(drawer.getByText('HERMES', { exact: true })).toBeVisible();
    await expect(drawer.getByText('This solver error happens when CalculiX solver is terminated abruptly')).toBeVisible();

    // Close the drawer
    await page.getByTestId('logs-drawer-close').click();
    await expect(drawer).not.toBeVisible();
  });

  test("should support changing and saving custom workspace settings", async ({ page }) => {
    // Mock config retrieval
    await page.route('**/api/workspace/config?*', async (route) => {
      await route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify({
          workspace_id: 'test-workspace-id',
          git_remote_url: 'https://github.com/burhop/wright.git',
          git_username: 'burhop',
          has_token: true,
          workspace_path: '/tmp/wright-e2e-workspace',
          workspace_prompt: 'Initial prompt context',
          git_large_file_threshold: 10
        }),
      });
    });

    // Intercept POST request
    let postPayload: any = null;
    await page.route('**/api/workspace/config', async (route) => {
      postPayload = route.request().postDataJSON();
      await route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify({ success: true, workspace_id: 'test-workspace-id' }),
      });
    });

    // Navigate directly to workspace
    await page.goto("/workspace/test-workspace-id");
    await expect(page.getByTestId("workspace-panel")).toBeVisible();

    // Open Workspace Settings sidebar tab
    await page.getByTestId("activity-bar-settings-btn").click();
    await expect(page.getByText("Workspace Settings")).toBeVisible();

    // Verify initial prompt and large file values loaded
    const promptInput = page.getByTestId("workspace-prompt-input");
    const thresholdInput = page.getByTestId("workspace-settings-git-threshold");
    await expect(promptInput).toHaveValue('Initial prompt context');
    await expect(thresholdInput).toHaveValue('10');

    // Edit settings form
    await promptInput.fill('Use strict CAD constraints');
    await thresholdInput.fill('25');

    // Click Save
    await page.getByTestId("workspace-settings-save-btn").click();

    // Verify payload sent matches edits
    await expect.poll(() => postPayload).toEqual({
      session_id: 'session-1',
      git_remote_url: 'https://github.com/burhop/wright.git',
      git_username: 'burhop',
      git_token: null,
      workspace_prompt: 'Use strict CAD constraints',
      git_large_file_threshold: 25
    });

    // Verify success indicator is rendered
    await expect(page.getByText('✓ Saved!')).toBeVisible();
  });
});

