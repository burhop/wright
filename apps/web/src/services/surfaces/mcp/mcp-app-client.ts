import type {
  McpUiMessageRequest,
  McpUiResourceCsp,
  McpUiResourcePermissions,
  McpUiUpdateModelContextRequest,
} from "@modelcontextprotocol/ext-apps/app-bridge";
import type {
  CallToolRequest,
  CallToolResult,
  ListResourcesRequest,
  ListResourcesResult,
  ListResourceTemplatesRequest,
  ListResourceTemplatesResult,
  ReadResourceRequest,
  ReadResourceResult,
} from "@modelcontextprotocol/sdk/types.js";

import { hostAdapter } from "../../host-adapter";
import { surfaceRequestId } from "../ids";
import type { SurfaceDescriptor } from "../surface-contract";
import type { McpAppGateway, McpAppOperationContext } from "./mcp-app-host";
import type {
  McpAppPresentationProjection,
  McpAppPresenterGateway,
} from "./mcp-app-presenter";

type HostCapability = "context.update" | "user.message" | "open.link";

function record(value: unknown, label: string): Record<string, unknown> {
  if (typeof value !== "object" || value === null || Array.isArray(value)) {
    throw new TypeError(`${label} is malformed`);
  }
  return value as Record<string, unknown>;
}

function text(value: unknown, label: string): string {
  if (typeof value !== "string" || value.length === 0) {
    throw new TypeError(`${label} is malformed`);
  }
  return value;
}

async function responseJson(response: Response): Promise<unknown> {
  if (!response.ok) {
    throw new Error(`MCP App request failed with HTTP ${response.status}`);
  }
  return response.json();
}

function parseProjection(value: unknown): McpAppPresentationProjection {
  const projection = record(value, "MCP App presentation");
  if (
    !["supported", "absent", "unsupported"].includes(
      String(projection.capability),
    )
  ) {
    throw new TypeError("MCP App capability is malformed");
  }
  const rawCapabilities = projection.hostCapabilities ?? [];
  if (!Array.isArray(rawCapabilities)) {
    throw new TypeError("MCP App host capabilities are malformed");
  }
  const allowed = new Set<HostCapability>([
    "context.update",
    "user.message",
    "open.link",
  ]);
  const hostCapabilities = rawCapabilities.map((item) => {
    if (typeof item !== "string" || !allowed.has(item as HostCapability)) {
      throw new TypeError("MCP App host capability is unsupported");
    }
    return item as HostCapability;
  });
  let resource: McpAppPresentationProjection["resource"];
  if (projection.resource !== undefined && projection.resource !== null) {
    const raw = record(projection.resource, "MCP App resource");
    resource = {
      html: text(raw.html, "MCP App resource HTML"),
      mediaType: text(raw.mediaType, "MCP App resource media type"),
      ...(raw.csp === undefined || raw.csp === null
        ? {}
        : { csp: record(raw.csp, "MCP App resource CSP") as McpUiResourceCsp }),
      ...(raw.grantedPermissions === undefined
        ? {}
        : {
            grantedPermissions: record(
              raw.grantedPermissions,
              "MCP App granted permissions",
            ) as McpUiResourcePermissions,
          }),
    };
  }
  return {
    capability:
      projection.capability as McpAppPresentationProjection["capability"],
    ...(projection.protocolVersion === undefined ||
    projection.protocolVersion === null
      ? {}
      : {
          protocolVersion: text(
            projection.protocolVersion,
            "MCP App protocol version",
          ),
        }),
    ...(projection.reason === undefined || projection.reason === null
      ? {}
      : { reason: text(projection.reason, "MCP App fallback reason") }),
    ...(projection.contentHash === undefined || projection.contentHash === null
      ? {}
      : { contentHash: text(projection.contentHash, "MCP App content hash") }),
    ...(projection.sandboxOrigin === undefined ||
    projection.sandboxOrigin === null
      ? {}
      : {
          sandboxOrigin: text(
            projection.sandboxOrigin,
            "MCP App sandbox origin",
          ),
        }),
    ...(resource ? { resource } : {}),
    ...(projection.fallbackResult
      ? {
          fallbackResult: record(
            projection.fallbackResult,
            "MCP App fallback",
          ) as CallToolResult,
        }
      : {}),
    ...(projection.initialToolInput
      ? {
          initialToolInput: record(
            projection.initialToolInput,
            "MCP App tool input",
          ),
        }
      : {}),
    ...(projection.initialToolResult
      ? {
          initialToolResult: record(
            projection.initialToolResult,
            "MCP App tool result",
          ) as CallToolResult,
        }
      : {}),
    hostCapabilities,
  };
}

export class McpAppClient implements McpAppPresenterGateway, McpAppGateway {
  private readonly surfaceSessionId: string;

  constructor(surfaceSessionId: string) {
    this.surfaceSessionId = surfaceSessionId;
  }

  async getPresentation(
    descriptor: SurfaceDescriptor,
    signal: AbortSignal,
  ): Promise<McpAppPresentationProjection> {
    return parseProjection(
      await responseJson(
        await hostAdapter.fetch(
          `${this.base(descriptor.surfaceId)}/presentation`,
          {
            headers: this.headers(
              descriptor.workspaceId,
              this.surfaceSessionId,
            ),
            signal,
          },
        ),
      ),
    );
  }

  async callTool(
    params: CallToolRequest["params"],
    context: McpAppOperationContext,
  ): Promise<CallToolResult> {
    return (await this.post(
      "tools/call",
      { name: params.name, arguments: params.arguments || {} },
      context,
    )) as CallToolResult;
  }

  async listResources(
    _params: ListResourcesRequest["params"],
    context: McpAppOperationContext,
  ): Promise<ListResourcesResult> {
    return (await this.post(
      "resources/list",
      {},
      context,
    )) as ListResourcesResult;
  }

  async listResourceTemplates(
    _params: ListResourceTemplatesRequest["params"],
    context: McpAppOperationContext,
  ): Promise<ListResourceTemplatesResult> {
    return (await this.post(
      "resource-templates/list",
      {},
      context,
    )) as ListResourceTemplatesResult;
  }

  async readResource(
    params: ReadResourceRequest["params"],
    context: McpAppOperationContext,
  ): Promise<ReadResourceResult> {
    return (await this.post(
      "resources/read",
      { uri: params.uri },
      context,
    )) as ReadResourceResult;
  }

  async updateModelContext(
    _params: McpUiUpdateModelContextRequest["params"],
    _context: McpAppOperationContext,
  ): Promise<void> {
    throw new Error("MCP App context updates require an explicit Wright grant");
  }

  async sendUserMessage(
    _params: McpUiMessageRequest["params"],
    _context: McpAppOperationContext,
  ): Promise<void> {
    throw new Error("MCP App user messages require an explicit Wright grant");
  }

  private async post(
    path: string,
    body: Record<string, unknown>,
    context: McpAppOperationContext,
  ): Promise<unknown> {
    const requestId = surfaceRequestId();
    const cancel = () => {
      void hostAdapter
        .fetch(
          `${this.base(context.surfaceId)}/operations/${encodeURIComponent(requestId)}`,
          {
            method: "DELETE",
            headers: this.headers(context.workspaceId, context.sessionId),
          },
        )
        .catch(() => undefined);
    };
    if (context.signal.aborted) {
      throw new DOMException("MCP App request aborted", "AbortError");
    }
    context.signal.addEventListener("abort", cancel, { once: true });
    try {
      return await responseJson(
        await hostAdapter.fetch(`${this.base(context.surfaceId)}/${path}`, {
          method: "POST",
          headers: {
            ...this.headers(context.workspaceId, context.sessionId),
            "Content-Type": "application/json",
          },
          body: JSON.stringify({ requestId, ...body }),
          signal: context.signal,
        }),
      );
    } finally {
      context.signal.removeEventListener("abort", cancel);
    }
  }

  private base(surfaceId: string): string {
    return `${hostAdapter.getApiBaseUrl()}/api/workspace/surfaces/${encodeURIComponent(surfaceId)}/mcp-app`;
  }

  private headers(workspaceId: string, sessionId: string): HeadersInit {
    return {
      "X-Wright-Workspace-ID": workspaceId,
      "X-Wright-Session-ID": sessionId,
    };
  }
}
