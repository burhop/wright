import { useEffect, useMemo, useRef } from "react";

import { McpAppClient } from "../../services/surfaces/mcp/mcp-app-client";
import {
  McpAppPresenter,
  type McpAppPresenterGateway,
} from "../../services/surfaces/mcp/mcp-app-presenter";
import type { SurfaceDescriptor } from "../../services/surfaces/surface-contract";

interface Props {
  readonly descriptor: SurfaceDescriptor;
  readonly sessionId: string;
  readonly onFocusMode?: () => void;
  readonly gateway?: McpAppPresenterGateway;
}

export function McpAppSurface({
  descriptor,
  sessionId,
  onFocusMode,
  gateway: providedGateway,
}: Props) {
  const host = useRef<HTMLDivElement>(null);
  const presenter = useRef<McpAppPresenter | null>(null);
  const gateway = useMemo(
    () => providedGateway || new McpAppClient(sessionId),
    [providedGateway, sessionId],
  );

  useEffect(() => {
    if (descriptor.source.kind !== "mcp_app" || !host.current) return;
    const next = new McpAppPresenter(descriptor, { sessionId, gateway });
    presenter.current = next;
    next.mount(host.current);
    return () => {
      next.dispose();
      if (presenter.current === next) presenter.current = null;
    };
  }, [descriptor.surfaceId, gateway, sessionId]);

  useEffect(() => {
    presenter.current?.update(descriptor);
  }, [descriptor]);

  return (
    <section
      data-testid="mcp-app-workspace-surface"
      aria-label={descriptor.title}
      style={{ height: "100%", display: "flex", flexDirection: "column" }}
    >
      <div data-focus-region="toolbar">
        {onFocusMode && (
          <button
            type="button"
            data-testid="surface-enter-focus"
            onClick={onFocusMode}
          >
            Maximize surface while keeping chat
          </button>
        )}
        <button
          type="button"
          data-testid="mcp-app-enter-frame"
          onClick={() => presenter.current?.focus()}
        >
          Enter interactive application
        </button>
      </div>
      <div ref={host} style={{ flex: 1, minHeight: 320 }} />
    </section>
  );
}
