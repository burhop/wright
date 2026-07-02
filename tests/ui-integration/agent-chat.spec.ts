import { test, expect } from "@playwright/test";

test.describe("Agent Chat Page", () => {
  test("should support session creation, messaging flow, and workspace toggle", async ({
    page,
  }) => {
    // Mock health endpoints
    await page.route("**/api/agent/health", async (route) => {
      await route.fulfill({
        status: 200,
        contentType: "application/json",
        body: JSON.stringify({ state: "connected", latencyMs: 5.0 }),
      });
    });

    await page.route("**/api/inference/health", async (route) => {
      await route.fulfill({
        status: 200,
        contentType: "application/json",
        body: JSON.stringify({ state: "connected", latencyMs: 12.0 }),
      });
    });

    // Mock session list
    await page.route("**/api/agent/sessions*", async (route) => {
      await route.fulfill({
        status: 200,
        contentType: "application/json",
        body: JSON.stringify({ sessions: [] }),
      });
    });

    // Mock session creation
    await page.route("**/api/agent/sessions/new", async (route) => {
      await route.fulfill({
        status: 200,
        contentType: "application/json",
        body: JSON.stringify({
          session_id: "session123",
          title: "Untitled",
          created_at: Date.now(),
        }),
      });
    });

    // Mock chat turn initiation
    await page.route("**/api/agent/chat/start", async (route) => {
      await route.fulfill({
        status: 200,
        contentType: "application/json",
        body: JSON.stringify({
          stream_id: "stream123",
          session_id: "session123",
        }),
      });
    });

    // Mock SSE chat response stream
    await page.route("**/api/agent/chat", async (route) => {
      await route.fulfill({
        status: 200,
        contentType: "text/event-stream; charset=utf-8",
        headers: {
          "Cache-Control": "no-cache",
          Connection: "keep-alive",
        },
        body: [
          "event: tool\n",
          'data: {"name": "calculate_stress", "preview": "Analyzing stress fields..."}\n\n',
          "event: token\n",
          'data: {"text": "I have received your request: \\"Run stiffness analysis\\". As a local offline assistant in v1, I am processing your mechanical designs."}\n\n',
          "event: stream_end\n",
          'data: {"session_id": "session123"}\n\n',
        ].join(""),
      });
    });

    // Mock get workspace by ID
    await page.route("**/api/workspace/by-id/*", async (route) => {
      await route.fulfill({
        status: 200,
        contentType: "application/json",
        body: JSON.stringify({
          workspace_id: "ws-1",
          session_id: "session123",
          workspace_name: "Test Project",
          local_path: "/tmp/wright-e2e-workspace",
          git_remote_url: null,
          git_username: null,
          updated_at: Math.floor(Date.now() / 1000),
        }),
      });
    });

    // Mock workspace activate
    await page.route("**/api/workspace/activate", async (route) => {
      await route.fulfill({
        status: 200,
        contentType: "application/json",
        body: JSON.stringify({
          success: true,
          session_id: "session123",
          workspace_path: "/tmp/wright-e2e-workspace",
        }),
      });
    });

    // Mock workspace files tree
    await page.route("**/api/workspace/files?*", async (route) => {
      await route.fulfill({
        status: 200,
        contentType: "application/json",
        body: JSON.stringify({
          workspace: {
            name: "wright",
            path: "/",
            type: "directory",
            size: null,
            last_modified: 1000,
            git_status: "Clean",
            children: [],
          },
        }),
      });
    });

    // Mock workspace git status
    await page.route("**/api/workspace/git/status?*", async (route) => {
      await route.fulfill({
        status: 200,
        contentType: "application/json",
        body: JSON.stringify({
          branch_name: "main",
          is_clean: true,
          changes: [],
        }),
      });
    });

    // Mock tool lists
    await page.route("**/api/mcp/servers", async (route) => {
      await route.fulfill({
        status: 200,
        contentType: "application/json",
        body: JSON.stringify({ servers: [] }),
      });
    });
    await page.route("**/api/mcp/tools", async (route) => {
      await route.fulfill({
        status: 200,
        contentType: "application/json",
        body: JSON.stringify({ tools: [] }),
      });
    });

    // Mock window.fetch to simulate SSE streaming for POST /api/agent/chat
    await page.addInitScript(() => {
      const originalFetch = window.fetch;
      window.fetch = async function (input: any, init?: RequestInit) {
        const url =
          typeof input === "string"
            ? input
            : (input && (input as any).url) || String(input);
        if (url.includes("/api/agent/chat") && init?.method === "POST") {
          const stream = new ReadableStream({
            start(controller) {
              const encoder = new TextEncoder();

              const sendChunk = (text: string, delay: number) => {
                setTimeout(() => {
                  controller.enqueue(encoder.encode(text));
                }, delay);
              };

              sendChunk(
                'event: tool\ndata: {"name": "calculate_stress", "preview": "Analyzing stress fields..."}\n\n',
                500,
              );
              sendChunk(
                'event: progress\ndata: {"percentage": 50, "message": "Solving stiffness equations (50% done)..."}\n\n',
                1000,
              );
              sendChunk(
                'event: token\ndata: {"text": "I have received your request: **Run stiffness analysis**. As a local offline assistant in v1, I am processing your mechanical designs."}\n\n',
                1500,
              );
              sendChunk(
                'event: stream_end\ndata: {"session_id": "session123"}\n\n',
                4000,
              );

              setTimeout(() => {
                controller.close();
              }, 4200);
            },
          });

          return new Response(stream, {
            headers: {
              "Content-Type": "text/event-stream; charset=utf-8",
              "Cache-Control": "no-cache",
              Connection: "keep-alive",
            },
            status: 200,
          });
        }
        return originalFetch.call(this, input, init);
      };
    });

    await page.goto("/workspace/ws-1");

    await expect(page.getByTestId("chat-layout")).toBeVisible();
    await expect(page.getByTestId("sessions-sidebar")).toBeVisible();
    await expect(page.getByTestId("chat-transcript")).toBeVisible();
    await expect(page.getByTestId("workspace-panel")).toBeVisible();

    const createBtn = page.getByTestId("create-session-btn");
    await expect(createBtn).toBeVisible();
    await createBtn.click();

    await expect(page.getByTestId("message-composer")).toBeVisible();

    const composer = page.getByTestId("composer-input");
    await composer.fill("Run stiffness analysis");

    const sendBtn = page.getByTestId("composer-send");
    await sendBtn.click();

    await expect(
      page
        .getByTestId("chat-transcript")
        .getByText("Run stiffness analysis")
        .first(),
    ).toBeVisible();
    await expect(page.getByTestId("stream-activity-panel")).toBeVisible();
    await expect(page.getByTestId("stream-activity-panel")).toContainText(
      "Using calculate_stress",
    );

    // Check tool progress displays correctly
    await expect(page.getByTestId("progress-percentage")).toHaveText("50%");
    await expect(page.getByTestId("progress-bar")).toBeVisible();

    await expect(
      page.getByText(/processing your mechanical designs/i),
    ).toBeVisible({ timeout: 10000 });
    await expect(
      page
        .getByTestId("chat-transcript")
        .getByText("Run stiffness analysis")
        .last(),
    ).toBeVisible();

    const explorerBtn = page.getByTestId("activity-bar-explorer-btn");
    await explorerBtn.click();
    await expect(page.getByTestId("workspace-sidebar")).not.toBeVisible();

    await explorerBtn.click();
    await expect(page.getByTestId("workspace-sidebar")).toBeVisible();
  });

  test("should support toggling between different sessions in a workspace", async ({
    page,
  }) => {
    // Mock health endpoints
    await page.route("**/api/agent/health", async (route) => {
      await route.fulfill({
        status: 200,
        contentType: "application/json",
        body: JSON.stringify({ state: "connected", latencyMs: 5.0 }),
      });
    });

    await page.route("**/api/inference/health", async (route) => {
      await route.fulfill({
        status: 200,
        contentType: "application/json",
        body: JSON.stringify({ state: "connected", latencyMs: 12.0 }),
      });
    });

    // Mock session list with multiple sessions
    await page.route("**/api/agent/sessions*", async (route) => {
      await route.fulfill({
        status: 200,
        contentType: "application/json",
        body: JSON.stringify({
          sessions: [
            {
              session_id: "session-1",
              title: "Session One",
              created_at: Date.now(),
              updated_at: Date.now(),
            },
            {
              session_id: "session-2",
              title: "Session Two",
              created_at: Date.now(),
              updated_at: Date.now(),
            },
          ],
        }),
      });
    });

    // Mock workspace by ID
    await page.route("**/api/workspace/by-id/*", async (route) => {
      await route.fulfill({
        status: 200,
        contentType: "application/json",
        body: JSON.stringify({
          workspace_id: "ws-1",
          session_id: "session-1",
          workspace_name: "Test Project",
          local_path: "/tmp/wright-e2e-workspace",
          git_remote_url: null,
          git_username: null,
          updated_at: Math.floor(Date.now() / 1000),
        }),
      });
    });

    // Mock workspace activate
    await page.route("**/api/workspace/activate", async (route) => {
      await route.fulfill({
        status: 200,
        contentType: "application/json",
        body: JSON.stringify({
          success: true,
          session_id: "session-1",
          workspace_path: "/tmp/wright-e2e-workspace",
        }),
      });
    });

    // Mock workspace files tree
    await page.route("**/api/workspace/files?*", async (route) => {
      await route.fulfill({
        status: 200,
        contentType: "application/json",
        body: JSON.stringify({
          workspace: {
            name: "wright",
            path: "/",
            type: "directory",
            size: null,
            last_modified: 1000,
            git_status: "Clean",
            children: [],
          },
        }),
      });
    });

    // Mock workspace git status
    await page.route("**/api/workspace/git/status?*", async (route) => {
      await route.fulfill({
        status: 200,
        contentType: "application/json",
        body: JSON.stringify({
          branch_name: "main",
          is_clean: true,
          changes: [],
        }),
      });
    });

    // Mock tool/server lists
    await page.route("**/api/mcp/servers", async (route) => {
      await route.fulfill({
        status: 200,
        contentType: "application/json",
        body: JSON.stringify({ servers: [] }),
      });
    });
    await page.route("**/api/mcp/tools", async (route) => {
      await route.fulfill({
        status: 200,
        contentType: "application/json",
        body: JSON.stringify({ tools: [] }),
      });
    });

    await page.goto("/workspace/ws-1");

    // Get the selector and attempt to select Session Two
    const selectDropdown = page
      .locator('[data-testid="agent-tools-window"] select')
      .nth(1);
    await expect(selectDropdown).toBeVisible();

    // The workspace remains bound to session-1; selecting a different chat session should not reset it.
    await selectDropdown.selectOption("session-2");

    // The workspace-bound selection stays stable and the workspace shell remains visible.
    await expect(selectDropdown).toHaveValue("session-1");
    await expect(page.getByTestId("workspace-panel")).toBeVisible();
  });

  test("should display MCP status button and show status details on click", async ({
    page,
  }) => {
    // Mock health endpoints
    await page.route("**/api/agent/health", async (route) => {
      await route.fulfill({
        status: 200,
        contentType: "application/json",
        body: JSON.stringify({ state: "connected", latencyMs: 5.0 }),
      });
    });

    await page.route("**/api/inference/health", async (route) => {
      await route.fulfill({
        status: 200,
        contentType: "application/json",
        body: JSON.stringify({ state: "connected", latencyMs: 12.0 }),
      });
    });

    // Mock session list
    await page.route("**/api/agent/sessions*", async (route) => {
      await route.fulfill({
        status: 200,
        contentType: "application/json",
        body: JSON.stringify({
          sessions: [
            {
              session_id: "session-1",
              title: "Session One",
              created_at: Date.now(),
              updated_at: Date.now(),
            },
          ],
        }),
      });
    });

    // Mock workspace by ID
    await page.route("**/api/workspace/by-id/*", async (route) => {
      await route.fulfill({
        status: 200,
        contentType: "application/json",
        body: JSON.stringify({
          workspace_id: "ws-1",
          session_id: "session-1",
          workspace_name: "Test Project",
          local_path: "/tmp/wright-e2e-workspace",
          git_remote_url: null,
          git_username: null,
          updated_at: Math.floor(Date.now() / 1000),
        }),
      });
    });

    // Mock workspace activate
    await page.route("**/api/workspace/activate", async (route) => {
      await route.fulfill({
        status: 200,
        contentType: "application/json",
        body: JSON.stringify({
          success: true,
          session_id: "session-1",
          workspace_path: "/tmp/wright-e2e-workspace",
        }),
      });
    });

    // Mock workspace files tree
    await page.route("**/api/workspace/files?*", async (route) => {
      await route.fulfill({
        status: 200,
        contentType: "application/json",
        body: JSON.stringify({
          workspace: {
            name: "wright",
            path: "/",
            type: "directory",
            size: null,
            last_modified: 1000,
            git_status: "Clean",
            children: [],
          },
        }),
      });
    });

    // Mock workspace git status
    await page.route("**/api/workspace/git/status?*", async (route) => {
      await route.fulfill({
        status: 200,
        contentType: "application/json",
        body: JSON.stringify({
          branch_name: "main",
          is_clean: true,
          changes: [],
        }),
      });
    });

    // Mock tool/server lists
    await page.route("**/api/mcp/servers", async (route) => {
      await route.fulfill({
        status: 200,
        contentType: "application/json",
        body: JSON.stringify({ servers: [] }),
      });
    });
    await page.route("**/api/mcp/tools", async (route) => {
      await route.fulfill({
        status: 200,
        contentType: "application/json",
        body: JSON.stringify({ tools: [] }),
      });
    });

    // Mock MCP status endpoint returning healthy status initially
    let mcpStatusPayload = {
      status: "ok",
      message: "MCP configuration is active and healthy.",
    };
    await page.route("**/api/workspace/mcp-status?*", async (route) => {
      await route.fulfill({
        status: 200,
        contentType: "application/json",
        body: JSON.stringify(mcpStatusPayload),
      });
    });

    await page.goto("/workspace/ws-1");

    // Verify MCP button is visible and green
    const mcpBtn = page.getByTestId("mcp-status-indicator");
    await expect(mcpBtn).toBeVisible();
    await expect(mcpBtn).toHaveCSS("background-color", "rgb(34, 197, 94)"); // #22c55e

    // Click to show popup
    await mcpBtn.click();
    const popup = page.getByTestId("mcp-status-popup");
    await expect(popup).toBeVisible();
    await expect(popup).toContainText(
      "MCP configuration is active and healthy.",
    );

    // Update payload to mismatch error state
    mcpStatusPayload = {
      status: "mismatch",
      message:
        "Tool change during session. Start a new session to apply changes.",
    };

    // Wait for the next poll (3 seconds interval in composer) and verify color turns amber
    await expect(mcpBtn).toHaveCSS("background-color", "rgb(245, 158, 11)", {
      timeout: 5000,
    }); // #f59e0b

    // Verify updated message in the open popup
    await expect(popup).toContainText(
      "Tool change during session. Start a new session to apply changes.",
    );
  });
});
