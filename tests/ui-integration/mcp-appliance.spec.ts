import { expect, test, type Page } from "@playwright/test";

const baseUrl =
  process.env.WRIGHT_MCP_PLAYWRIGHT_BASE_URL || process.env.PLAYWRIGHT_BASE_URL;
const accessToken =
  process.env.WRIGHT_MCP_PLAYWRIGHT_TOKEN || process.env.WRIGHT_API_TOKEN;

const defaultRequiredServerIds = [
  "openscad-mcp",
  "freecad-mcp",
  "brep-mcp",
  "playwright-mcp",
];
const requiredServers = (
  process.env.WRIGHT_MCP_PLAYWRIGHT_REQUIRED_SERVERS ||
  defaultRequiredServerIds.join(",")
)
  .split(",")
  .map((serverId) => ({ serverId: serverId.trim() }))
  .filter((server) => server.serverId.length > 0);

type McpServer = {
  server_id: string;
  name: string;
  is_installed: boolean;
  is_active: boolean;
  status: string;
  error_message?: string | null;
};

type WorkspaceBinding = {
  workspace_id: string;
  session_id: string;
  local_path: string;
};

type McpRpcEnvelope = {
  id?: number;
  result?: Record<string, unknown>;
  error?: { code?: number; message?: string };
};

function appUrl(path: string): string {
  if (!baseUrl) throw new Error("Missing MCP appliance base URL");
  return new URL(path, baseUrl).toString();
}

async function apiJson<T>(
  page: Page,
  path: string,
  options?: Parameters<Page["request"]["fetch"]>[1],
): Promise<T> {
  const response = await page.request.fetch(appUrl(path), options);
  const body = await response.text();
  expect(
    response.ok(),
    `${options?.method || "GET"} ${path} failed with ${response.status()}: ${body}`,
  ).toBeTruthy();
  return JSON.parse(body) as T;
}

async function authenticate(page: Page): Promise<void> {
  if (!accessToken) return;

  const response = await page.request.post(appUrl("/api/auth/session"), {
    data: { token: accessToken },
  });
  expect(
    response.ok(),
    `Failed to create Wright browser session: ${response.status()} ${await response.text()}`,
  ).toBeTruthy();

  await page.goto(appUrl("/"));
}

async function createWorkspace(page: Page): Promise<{
  workspace_id: string;
  session_id: string;
  local_path: string;
}> {
  await page.getByTestId("create-workspace-btn").click();
  await expect(page.getByTestId("create-workspace-modal")).toBeVisible();

  const name = `MCP appliance ${Date.now()}`;
  await page.locator("#workspace-name-input").fill(name);
  await page.locator("#workspace-create-submit").click();

  await expect(page).toHaveURL(/\/workspace\//, { timeout: 30_000 });
  await expect(page.getByTestId("page-workspace")).toBeVisible({
    timeout: 30_000,
  });

  const workspaceId = new URL(page.url()).pathname
    .split("/")
    .filter(Boolean)
    .at(-1);
  expect(
    workspaceId,
    `Unexpected workspace URL after create: ${page.url()}`,
  ).toBeTruthy();

  return apiJson(page, `/api/workspace/by-id/${workspaceId}`);
}

function mcpHeaders(
  workspace: WorkspaceBinding,
  transportSessionId?: string,
): Record<string, string> {
  return {
    Accept: "application/json, text/event-stream",
    "Content-Type": "application/json",
    "X-Wright-Session-Id": workspace.session_id,
    "X-Wright-Workspace-Id": workspace.workspace_id,
    ...(accessToken ? { Authorization: `Bearer ${accessToken}` } : {}),
    ...(transportSessionId
      ? {
          "Mcp-Session-Id": transportSessionId,
          "Mcp-Protocol-Version": "2025-11-25",
        }
      : {}),
  };
}

function parseMcpEnvelope(body: string): McpRpcEnvelope {
  const trimmed = body.trim();
  if (!trimmed) return {};
  if (trimmed.startsWith("{")) return JSON.parse(trimmed) as McpRpcEnvelope;

  const data = trimmed
    .split(/\r?\n/)
    .filter((line) => line.startsWith("data:"))
    .map((line) => line.replace(/^data:\s?/, ""))
    .join("\n")
    .trim();
  expect(data, `No JSON-RPC data found in MCP response: ${body}`).toBeTruthy();
  return JSON.parse(data) as McpRpcEnvelope;
}

async function mcpRpc(
  page: Page,
  workspace: WorkspaceBinding,
  payload: Record<string, unknown>,
  transportSessionId?: string,
): Promise<{ envelope: McpRpcEnvelope; transportSessionId: string }> {
  const response = await page.request.post(appUrl("/mcp"), {
    headers: mcpHeaders(workspace, transportSessionId),
    data: payload,
  });
  const body = await response.text();
  expect(
    response.ok(),
    `MCP ${String(payload.method)} failed with ${response.status()}: ${body}`,
  ).toBeTruthy();
  const nextTransportSessionId =
    response.headers()["mcp-session-id"] || transportSessionId;
  expect(
    nextTransportSessionId,
    "MCP response did not include a session id",
  ).toBeTruthy();
  const envelope = parseMcpEnvelope(body);
  expect(
    envelope.error,
    `MCP ${String(payload.method)} returned JSON-RPC error: ${body}`,
  ).toBeFalsy();
  return {
    envelope,
    transportSessionId: nextTransportSessionId!,
  };
}

async function mcpNotification(
  page: Page,
  workspace: WorkspaceBinding,
  payload: Record<string, unknown>,
  transportSessionId: string,
): Promise<void> {
  const response = await page.request.post(appUrl("/mcp"), {
    headers: mcpHeaders(workspace, transportSessionId),
    data: payload,
  });
  const body = await response.text();
  expect(
    response.ok(),
    `MCP notification ${String(payload.method)} failed with ${response.status()}: ${body}`,
  ).toBeTruthy();
}

function expectToolCallOk(toolName: string, envelope: McpRpcEnvelope) {
  const result = envelope.result as
    | { isError?: boolean; content?: { type?: string; text?: string }[] }
    | undefined;
  expect(result, `${toolName} did not return a result`).toBeTruthy();
  expect(
    result?.isError || false,
    `${toolName} returned an MCP tool error: ${JSON.stringify(result)}`,
  ).toBe(false);
  return result!;
}

function toolText(result: {
  content?: { type?: string; text?: string }[];
}): string {
  return result.content?.find((item) => item.type === "text")?.text || "";
}

async function setOnlyWorkspaceTool(
  page: Page,
  workspaceId: string,
  servers: McpServer[],
  target: McpServer,
): Promise<void> {
  for (const server of servers) {
    for (const serverId of [server.server_id, server.name]) {
      await apiJson(page, `/api/workspace/by-id/${workspaceId}/tools/toggle`, {
        method: "POST",
        data: { server_id: serverId, is_enabled: false },
      });
    }
  }

  await apiJson(page, `/api/workspace/by-id/${workspaceId}/tools/toggle`, {
    method: "POST",
    data: { server_id: target.server_id, is_enabled: true },
  });
}

async function enableWorkspaceTools(
  page: Page,
  workspaceId: string,
  servers: McpServer[],
): Promise<void> {
  for (const server of servers) {
    await apiJson(page, `/api/workspace/by-id/${workspaceId}/tools/toggle`, {
      method: "POST",
      data: { server_id: server.server_id, is_enabled: true },
    });
  }
}

test.describe("MCP appliance prompt workflow @live", () => {
  test.skip(
    !baseUrl,
    "Set WRIGHT_MCP_PLAYWRIGHT_BASE_URL or PLAYWRIGHT_BASE_URL to test a running MCP appliance",
  );
  test.skip(
    !accessToken,
    "Set WRIGHT_MCP_PLAYWRIGHT_TOKEN or WRIGHT_API_TOKEN for authenticated Docker appliances",
  );

  test("opens Wright, starts bundled MCPs, and submits an MCP-oriented prompt", async ({
    page,
  }) => {
    test.setTimeout(240_000);

    await test.step("authenticate and verify the registry", async () => {
      await authenticate(page);
      await expect(page.getByTestId("page-dashboard")).toBeVisible({
        timeout: 30_000,
      });

      const response = await apiJson<{ servers: McpServer[] }>(
        page,
        "/api/mcp/servers",
      );
      const installedById = new Map(
        response.servers
          .filter((server) =>
            requiredServers.some((s) => s.serverId === server.server_id),
          )
          .map((server) => [server.server_id, server]),
      );

      for (const required of requiredServers) {
        const server = installedById.get(required.serverId);
        expect(
          server,
          `Missing bundled MCP server registration: ${required.serverId}`,
        ).toBeTruthy();
        expect(
          server?.is_installed,
          `${required.serverId} should be installed in the appliance bundle`,
        ).toBe(true);
      }

      await page.goto(appUrl("/tool-registry"));
      await expect(page.getByTestId("page-tool-registry")).toBeVisible({
        timeout: 30_000,
      });
      for (const required of requiredServers) {
        const server = installedById.get(required.serverId);
        const card = page.getByTestId(`server-card-${required.serverId}`);
        await expect(card).toBeVisible({ timeout: 30_000 });
        await expect(card).toContainText(server?.name || required.serverId, {
          timeout: 30_000,
        });
      }
    });

    let workspace:
      | { workspace_id: string; session_id: string; local_path: string }
      | undefined;
    let installedServers: McpServer[] = [];

    await test.step("create a managed workspace", async () => {
      await page.goto(appUrl("/"));
      workspace = await createWorkspace(page);
      expect(workspace.local_path).toBeTruthy();
    });

    await test.step("start each bundled MCP and discover tools", async () => {
      const failures: string[] = [];
      const response = await apiJson<{ servers: McpServer[] }>(
        page,
        "/api/mcp/servers",
      );
      installedServers = requiredServers.map((required) => {
        const server = response.servers.find(
          (item) => item.server_id === required.serverId,
        );
        expect(
          server,
          `Missing bundled MCP server: ${required.serverId}`,
        ).toBeTruthy();
        return server as McpServer;
      });

      for (const server of installedServers) {
        await setOnlyWorkspaceTool(
          page,
          workspace!.workspace_id,
          installedServers,
          server,
        );
        const status = await apiJson<{
          status: string;
          message: string;
          running_mcps: {
            name: string;
            status: string;
            error_message?: string | null;
          }[];
        }>(page, `/api/workspace/by-id/${workspace!.workspace_id}/mcp-status`);

        if (status.status !== "ok") {
          failures.push(
            `${server.server_id}: workspace status ${status.status}: ${status.message}`,
          );
        }

        const running = status.running_mcps.find(
          (item) => item.name === server.name,
        );
        if (!running) {
          failures.push(
            `${server.server_id}: missing from running MCP status: ${JSON.stringify(status)}`,
          );
        } else if (running.status !== "active") {
          failures.push(
            `${server.server_id}: expected active, got ${running.status}: ${running.error_message || "no error message"}`,
          );
        }

        const tools = await apiJson<{ tools: { server_id: string }[] }>(
          page,
          "/api/mcp/tools",
        );
        if (!tools.tools.some((tool) => tool.server_id === server.server_id)) {
          failures.push(
            `${server.server_id}: ${server.name} started but did not register any tools`,
          );
        }
      }

      expect(failures).toEqual([]);
    });

    await test.step("call safe backend tools through the Wright MCP gateway", async () => {
      await enableWorkspaceTools(
        page,
        workspace!.workspace_id,
        installedServers,
      );

      let transportSessionId: string | undefined;
      const initialize = await mcpRpc(
        page,
        workspace!,
        {
          jsonrpc: "2.0",
          id: 1,
          method: "initialize",
          params: {
            protocolVersion: "2025-11-25",
            capabilities: {},
            clientInfo: { name: "wright-playwright-live", version: "1" },
          },
        },
        transportSessionId,
      );
      transportSessionId = initialize.transportSessionId;
      await mcpNotification(
        page,
        workspace!,
        { jsonrpc: "2.0", method: "notifications/initialized" },
        transportSessionId,
      );

      const listed = await mcpRpc(
        page,
        workspace!,
        { jsonrpc: "2.0", id: 2, method: "tools/list" },
        transportSessionId,
      );
      transportSessionId = listed.transportSessionId;
      const toolNames = new Set(
        (
          (listed.envelope.result?.tools as { name?: string }[] | undefined) ||
          []
        ).map((tool) => tool.name),
      );
      for (const toolName of [
        "openscad-mcp__check_openscad",
        "freecad-mcp__create_document",
        "brep-mcp__run_program",
        "playwright-mcp__browser_navigate",
      ]) {
        expect(
          toolNames.has(toolName),
          `Missing gateway tool ${toolName}`,
        ).toBe(true);
      }

      const openscad = await mcpRpc(
        page,
        workspace!,
        {
          jsonrpc: "2.0",
          id: 3,
          method: "tools/call",
          params: {
            name: "openscad-mcp__check_openscad",
            arguments: { include_paths: false },
          },
        },
        transportSessionId,
      );
      expectToolCallOk("openscad-mcp__check_openscad", openscad.envelope);
      expect(JSON.stringify(openscad.envelope.result)).toContain("OpenSCAD");

      const freecad = await mcpRpc(
        page,
        workspace!,
        {
          jsonrpc: "2.0",
          id: 4,
          method: "tools/call",
          params: {
            name: "freecad-mcp__create_document",
            arguments: { name: "WrightLiveProbe" },
          },
        },
        openscad.transportSessionId,
      );
      const freecadResult = expectToolCallOk(
        "freecad-mcp__create_document",
        freecad.envelope,
      );
      expect(toolText(freecadResult)).toContain("created successfully");

      const brep = await mcpRpc(
        page,
        workspace!,
        {
          jsonrpc: "2.0",
          id: 5,
          method: "tools/call",
          params: {
            name: "brep-mcp__run_program",
            arguments: {
              code: "import { box } from 'brepjs';\nexport default () => box(40, 20, 10, { centered: true });\n",
              timeoutMs: 30_000,
            },
          },
        },
        freecad.transportSessionId,
      );
      const brepResult = expectToolCallOk(
        "brep-mcp__run_program",
        brep.envelope,
      );
      const brepPayload = JSON.parse(toolText(brepResult)) as {
        ok: boolean;
        report: { measurements?: { volume?: number } };
      };
      expect(brepPayload.ok).toBe(true);
      expect(brepPayload.report.measurements?.volume).toBeGreaterThan(7_900);

      const browser = await mcpRpc(
        page,
        workspace!,
        {
          jsonrpc: "2.0",
          id: 6,
          method: "tools/call",
          params: {
            name: "playwright-mcp__browser_navigate",
            arguments: { url: "http://127.0.0.1:8000/api/health" },
          },
        },
        brep.transportSessionId,
      );
      expectToolCallOk("playwright-mcp__browser_navigate", browser.envelope);
    });

    await test.step("submit a prompt through the Wright workspace UI", async () => {
      await enableWorkspaceTools(
        page,
        workspace!.workspace_id,
        installedServers,
      );
      await page.goto(appUrl(`/workspace/${workspace!.workspace_id}`));
      await expect(page.getByTestId("page-workspace")).toBeVisible({
        timeout: 30_000,
      });

      const composer = page
        .getByTestId("composer-input")
        .or(page.getByRole("textbox"))
        .first();
      await expect(composer).toBeVisible({ timeout: 30_000 });

      const prompt =
        "List the MCP servers attached to this workspace and confirm this Linux appliance has OpenSCAD, FreeCAD, BREP, and Playwright available.";
      await composer.fill(prompt);

      const send = page
        .getByTestId("composer-send")
        .or(page.getByRole("button", { name: /send|submit/i }))
        .first();
      await send.click();

      const transcript = page.getByTestId("chat-transcript");
      await expect(transcript.getByText(prompt)).toBeVisible({
        timeout: 30_000,
      });
      await page.waitForTimeout(45_000);
      await expect(page.locator("body")).not.toContainText(
        /Failed to start workspace MCP server|Authentication required|Unauthorized|Hermes gateway restart failed|Hermes gateway did not become ready|Hermes agent is not available/i,
      );
    });
  });
});
