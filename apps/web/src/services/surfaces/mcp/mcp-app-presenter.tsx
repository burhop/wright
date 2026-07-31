import { SUPPORTED_PROTOCOL_VERSIONS } from "@modelcontextprotocol/ext-apps/app-bridge";
import type { CallToolResult, ContentBlock } from "@modelcontextprotocol/sdk/types.js";

import type { SurfacePresenter } from "../registry";
import type { SurfaceDescriptor } from "../surface-contract";
import {
  McpAppHost,
  type McpAppGateway,
  type McpAppHostStatus,
  type McpAppResourceDocument,
} from "./mcp-app-host";
import {
  MCP_APP_MEDIA_TYPE,
  MCP_OUTER_SANDBOX_ATTRIBUTE,
  createSandboxProxyUrl,
  validateSandboxPolicy,
} from "./sandbox-proxy";

export type McpAppCapabilityState = "supported" | "absent" | "unsupported";

export interface McpAppPresentationProjection {
  readonly capability: McpAppCapabilityState;
  readonly protocolVersion?: string;
  readonly reason?: string;
  readonly contentHash?: string;
  readonly sandboxOrigin?: string;
  readonly resource?: McpAppResourceDocument;
  readonly fallbackResult?: CallToolResult;
  readonly initialToolInput?: Readonly<Record<string, unknown>>;
  readonly initialToolResult?: CallToolResult;
  readonly hostCapabilities?: readonly (
    | "context.update"
    | "user.message"
    | "open.link"
  )[];
}

export interface McpAppPresenterGateway extends McpAppGateway {
  getPresentation(
    descriptor: SurfaceDescriptor,
    signal: AbortSignal,
  ): Promise<McpAppPresentationProjection>;
}

export interface McpAppPresenterOptions {
  readonly sessionId: string;
  readonly gateway: McpAppPresenterGateway;
  readonly hostOrigin?: string;
  readonly platform?: "web" | "desktop" | "mobile";
}

function source(descriptor: SurfaceDescriptor) {
  if (descriptor.source.kind !== "mcp_app") {
    throw new TypeError("McpAppPresenter requires an MCP App surface");
  }
  return descriptor.source;
}

function nonce(): string {
  const bytes = new Uint8Array(24);
  crypto.getRandomValues(bytes);
  return [...bytes].map((value) => value.toString(16).padStart(2, "0")).join("");
}

function fallbackText(block: ContentBlock): string | null {
  switch (block.type) {
    case "text":
      return block.text;
    case "image":
      return "Image output remains available in the tool result.";
    case "audio":
      return "Audio output remains available in the tool result.";
    case "resource":
      return "Embedded resource output remains available in the tool result.";
    case "resource_link":
      return `Resource output: ${block.name || block.uri}`;
    default:
      return null;
  }
}

export class McpAppPresenter implements SurfacePresenter {
  private container: HTMLElement | null = null;
  private root: HTMLDivElement | null = null;
  private statusElement: HTMLParagraphElement | null = null;
  private frame: HTMLIFrameElement | null = null;
  private host: McpAppHost | null = null;
  private loadController: AbortController | null = null;
  private disposed = false;
  private loadGeneration = 0;
  private descriptor: SurfaceDescriptor;
  private readonly options: McpAppPresenterOptions;

  constructor(
    descriptor: SurfaceDescriptor,
    options: McpAppPresenterOptions,
  ) {
    source(descriptor);
    this.descriptor = descriptor;
    this.options = options;
  }

  mount(container: HTMLElement): void {
    if (this.disposed) throw new Error("MCP App presenter is disposed");
    if (this.container) throw new Error("MCP App presenter is already mounted");
    this.container = container;
    this.root = document.createElement("div");
    this.root.dataset.testid = "mcp-app-surface";
    this.root.style.height = "100%";
    this.root.style.display = "flex";
    this.root.style.flexDirection = "column";
    this.statusElement = document.createElement("p");
    this.statusElement.dataset.testid = "mcp-app-status";
    this.statusElement.setAttribute("role", "status");
    this.statusElement.setAttribute("aria-live", "polite");
    this.root.append(this.statusElement);
    container.replaceChildren(this.root);
    void this.load();
  }

  update(descriptor: SurfaceDescriptor): void {
    if (this.disposed) throw new Error("MCP App presenter is disposed");
    const previous = source(this.descriptor);
    const next = source(descriptor);
    if (descriptor.surfaceId !== this.descriptor.surfaceId) {
      throw new Error("MCP App presenter cannot change surface identity");
    }
    this.descriptor = descriptor;
    if (
      previous.sourceVersion !== next.sourceVersion ||
      previous.contentHash !== next.contentHash ||
      previous.resourceUri !== next.resourceUri
    ) {
      void this.load();
    } else if (this.frame) {
      this.frame.title = descriptor.title;
    }
  }

  focus(): void {
    this.frame?.focus();
  }

  dispose(): void {
    if (this.disposed) return;
    this.disposed = true;
    this.loadController?.abort();
    this.loadController = null;
    const host = this.host;
    this.host = null;
    void host?.teardown();
    this.frame?.remove();
    this.frame = null;
    this.root?.remove();
    this.root = null;
    this.container = null;
  }

  private async load(): Promise<void> {
    const root = this.root;
    if (!root || this.disposed) return;
    const generation = ++this.loadGeneration;
    this.loadController?.abort();
    const controller = new AbortController();
    this.loadController = controller;
    const previousHost = this.host;
    this.host = null;
    void previousHost?.teardown();
    this.frame?.remove();
    this.frame = null;
    this.removeFallback();
    this.setStatus("Loading interactive MCP App…");
    let projection: McpAppPresentationProjection;
    try {
      projection = await this.options.gateway.getPresentation(
        this.descriptor,
        controller.signal,
      );
    } catch (reason) {
      if (controller.signal.aborted || generation !== this.loadGeneration) return;
      this.showFallback(
        `Interactive view could not be loaded: ${
          reason instanceof Error ? reason.message : String(reason)
        }`,
      );
      return;
    }
    if (controller.signal.aborted || generation !== this.loadGeneration || this.disposed) return;
    const appSource = source(this.descriptor);
    if (projection.capability !== "supported") {
      this.showFallback(
        projection.reason ||
          (projection.capability === "absent"
            ? "This MCP server did not negotiate interactive UI support."
            : "This MCP App protocol version is not supported by Wright."),
        projection.fallbackResult,
      );
      return;
    }
    if (
      !projection.protocolVersion ||
      !SUPPORTED_PROTOCOL_VERSIONS.includes(projection.protocolVersion)
    ) {
      this.showFallback(
        `Interactive view uses unsupported protocol ${projection.protocolVersion || "unknown"}.`,
        projection.fallbackResult,
      );
      return;
    }
    if (!projection.resource) {
      this.showFallback(
        projection.reason || "The MCP server did not return its associated UI resource.",
        projection.fallbackResult,
      );
      return;
    }
    if (projection.resource.mediaType.toLowerCase() !== MCP_APP_MEDIA_TYPE) {
      this.showFallback(
        `The MCP UI resource has unsupported media type ${projection.resource.mediaType}.`,
        projection.fallbackResult,
      );
      return;
    }
    if (projection.contentHash !== appSource.contentHash) {
      this.showFallback(
        "The MCP UI resource changed while it was loading. Refresh to use the current version.",
        projection.fallbackResult,
      );
      return;
    }
    if (!projection.sandboxOrigin) {
      this.showFallback(
        "A distinct MCP App sandbox origin is not configured for this deployment.",
        projection.fallbackResult,
      );
      return;
    }
    try {
      const policy = validateSandboxPolicy(
        projection.resource.csp,
        projection.resource.grantedPermissions,
      );
      const hostOrigin = new URL(this.options.hostOrigin || window.location.origin).origin;
      const sandboxOrigin = new URL(projection.sandboxOrigin).origin;
      if (hostOrigin === sandboxOrigin) {
        throw new Error("MCP App sandbox origin must differ from Wright's control origin");
      }
      const frame = document.createElement("iframe");
      frame.dataset.testid = "mcp-app-sandbox-frame";
      frame.title = this.descriptor.title;
      frame.setAttribute("sandbox", MCP_OUTER_SANDBOX_ATTRIBUTE);
      frame.setAttribute("referrerpolicy", "no-referrer");
      frame.allow = policy.allowAttribute;
      frame.style.border = "0";
      frame.style.flex = "1";
      frame.style.minHeight = "320px";
      frame.style.width = "100%";
      frame.src = createSandboxProxyUrl({
        sandboxOrigin,
        hostOrigin,
        surfaceId: this.descriptor.surfaceId,
        generation: this.descriptor.instance?.generation || this.descriptor.revision,
        nonce: nonce(),
      }).href;
      root.append(frame);
      const frameWindow = frame.contentWindow;
      if (!frameWindow) throw new Error("MCP App sandbox frame is unavailable");
      const host = new McpAppHost({
        frameWindow,
        sandboxOrigin,
        workspaceId: this.descriptor.workspaceId,
        sessionId: this.options.sessionId,
        surfaceId: this.descriptor.surfaceId,
        generation: this.descriptor.instance?.generation || this.descriptor.revision,
        serverId: appSource.serverId,
        nonce: new URL(frame.src).searchParams.get("nonce") || "",
        resource: projection.resource,
        policy,
        gateway: this.options.gateway,
        hostContext: {
          theme: window.matchMedia("(prefers-color-scheme: dark)").matches ? "dark" : "light",
          displayMode: "inline",
          availableDisplayModes: ["inline", "fullscreen"],
          locale: navigator.language,
          timeZone: Intl.DateTimeFormat().resolvedOptions().timeZone,
          userAgent: "Wright Workspace Surfaces",
          platform: this.options.platform || "web",
        },
        initialToolInput: projection.initialToolInput,
        initialToolResult: projection.initialToolResult,
        enabledHostCapabilities: new Set(projection.hostCapabilities || []),
        onStatus: (status, detail) => this.hostStatus(status, detail),
        onSizeChange: ({ height }) => {
          if (height && Number.isFinite(height)) {
            frame.style.height = `${Math.min(Math.max(height, 160), 2_000)}px`;
          }
        },
        onRequestTeardown: () => this.showFallback("The MCP App closed its interactive view."),
        onSecurityViolation: () => this.setStatus("Blocked an invalid MCP App message."),
      });
      this.frame = frame;
      this.host = host;
      await host.connect();
    } catch (reason) {
      if (controller.signal.aborted || generation !== this.loadGeneration) return;
      this.host = null;
      this.frame?.remove();
      this.frame = null;
      this.showFallback(
        `Interactive view was blocked by its renderer or security policy: ${
          reason instanceof Error ? reason.message : String(reason)
        }`,
        projection.fallbackResult,
      );
    }
  }

  private hostStatus(status: McpAppHostStatus, detail?: string): void {
    const messages: Record<McpAppHostStatus, string> = {
      connecting: "Connecting secure MCP App bridge…",
      waiting_for_proxy: "Waiting for the isolated MCP App sandbox…",
      loading_resource: "Loading the packaged MCP App resource…",
      initializing: "Initializing the MCP App…",
      ready: "Interactive MCP App ready.",
      tearing_down: "Closing the MCP App…",
      closed: "MCP App closed.",
      error: `MCP App bridge error${detail ? `: ${detail}` : "."}`,
    };
    this.setStatus(messages[status]);
  }

  private setStatus(message: string): void {
    if (this.statusElement) this.statusElement.textContent = message;
  }

  private removeFallback(): void {
    this.root?.querySelector('[data-testid="mcp-app-fallback"]')?.remove();
  }

  private showFallback(reason: string, result?: CallToolResult): void {
    const root = this.root;
    if (!root || this.disposed) return;
    const host = this.host;
    this.host = null;
    void host?.teardown();
    this.frame?.remove();
    this.frame = null;
    this.removeFallback();
    this.setStatus("Interactive MCP App unavailable. Showing safe fallback.");
    const fallback = document.createElement("section");
    fallback.dataset.testid = "mcp-app-fallback";
    fallback.setAttribute("role", "region");
    fallback.setAttribute("aria-label", "MCP App fallback content");
    const heading = document.createElement("h3");
    heading.textContent = "Interactive view unavailable";
    const explanation = document.createElement("p");
    explanation.textContent = reason;
    fallback.append(heading, explanation);
    const texts = result?.content.map(fallbackText).filter((item): item is string => Boolean(item)) || [];
    for (const text of texts) {
      const paragraph = document.createElement("p");
      paragraph.textContent = text;
      fallback.append(paragraph);
    }
    if (result?.structuredContent) {
      const structured = document.createElement("pre");
      structured.textContent = JSON.stringify(result.structuredContent, null, 2);
      fallback.append(structured);
    }
    if (texts.length === 0 && !result?.structuredContent) {
      const retained = document.createElement("p");
      retained.textContent = "The tool result remains available in the conversation.";
      fallback.append(retained);
    }
    const retry = document.createElement("button");
    retry.type = "button";
    retry.dataset.testid = "mcp-app-retry";
    retry.textContent = "Retry interactive view";
    retry.addEventListener("click", () => void this.load());
    fallback.append(retry);
    root.append(fallback);
  }
}
