import { useEffect, useRef, type ReactNode } from "react";

interface Props {
  readonly compact: boolean;
  readonly open: boolean;
  readonly width: number;
  readonly onClose: () => void;
  readonly children: ReactNode;
}

/** Compact navigation overlays the document without changing desktop preferences. */
export function WorkspaceSidebarPanel({
  compact,
  open,
  width,
  onClose,
  children,
}: Props) {
  const closeRef = useRef<HTMLButtonElement>(null);
  useEffect(() => {
    if (!compact || !open) return;
    const initiator = document.activeElement;
    closeRef.current?.focus();
    return () => {
      if (initiator instanceof HTMLElement && initiator.isConnected)
        initiator.focus();
    };
  }, [compact, open]);

  return (
    <>
      {compact && open && (
        <button
          type="button"
          aria-label="Return to workspace"
          data-testid="workspace-sidebar-backdrop"
          onClick={onClose}
          style={{
            position: "absolute",
            inset: "0 0 0 48px",
            zIndex: 14,
            background: "#0006",
            border: 0,
            padding: 0,
          }}
        />
      )}
      <div
        id="workspace-navigation-panel"
        data-testid="workspace-sidebar"
        role="region"
        aria-label="Workspace navigation"
        onKeyDown={(event) => {
          if (compact && open && event.key === "Escape") {
            event.preventDefault();
            event.stopPropagation();
            onClose();
          }
        }}
        style={{
          backgroundColor: "var(--color-surface)",
          borderRight: "1px solid var(--color-border)",
          gridColumn: "2",
          display: open ? "flex" : "none",
          flexDirection: "column",
          overflow: "hidden",
          ...(compact
            ? {
                position: "absolute",
                top: 0,
                bottom: 0,
                left: 48,
                width,
                maxWidth: "calc(100% - 48px)",
                zIndex: 15,
              }
            : {}),
        }}
      >
        {compact && (
          <div
            style={{
              display: "flex",
              justifyContent: "flex-end",
              padding: "var(--space-sm)",
            }}
          >
            <button
              ref={closeRef}
              type="button"
              onClick={onClose}
              style={{ minHeight: 44 }}
              aria-label="Close workspace navigation"
            >
              Close
            </button>
          </div>
        )}
        <div style={{ flex: 1, minHeight: 0, overflow: "hidden" }}>
          {children}
        </div>
      </div>
    </>
  );
}
