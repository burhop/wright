import type { ReactNode } from "react";

import type { NarrowPane } from "./workspace-layout";

interface Props {
  readonly activePane: NarrowPane;
  readonly onChange: (pane: NarrowPane) => void;
  readonly chat?: ReactNode;
  readonly surface?: ReactNode;
  readonly hiddenChatUpdate?: string | null;
  readonly hiddenSurfaceUpdate?: string | null;
  readonly controlsOnly?: boolean;
}

export function ResponsivePaneSwitcher({
  activePane,
  onChange,
  chat,
  surface,
  hiddenChatUpdate,
  hiddenSurfaceUpdate,
  controlsOnly = false,
}: Props) {
  return (
    <>
      <nav className="workspace-pane-switcher" aria-label="Workspace pane">
        <button
          type="button"
          data-testid="workspace-pane-chat"
          aria-pressed={activePane === "chat"}
          onClick={() => onChange("chat")}
        >
          Chat
        </button>
        <button
          type="button"
          data-testid="workspace-pane-surface"
          aria-pressed={activePane === "surface"}
          onClick={() => onChange("surface")}
        >
          Surface
        </button>
      </nav>
      <div
        className="sr-only"
        aria-live="polite"
        data-testid="hidden-pane-updates"
      >
        {activePane === "surface" ? hiddenChatUpdate : hiddenSurfaceUpdate}
      </div>
      {!controlsOnly && (
        <div className="workspace-narrow-panes">
          <section hidden={activePane !== "chat"} aria-label="Chat pane">
            {chat}
          </section>
          <section hidden={activePane !== "surface"} aria-label="Surface pane">
            {surface}
          </section>
        </div>
      )}
    </>
  );
}
