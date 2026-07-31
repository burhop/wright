import {
  useEffect,
  useRef,
  useState,
  type KeyboardEvent,
  type RefObject,
} from "react";

export interface SurfaceTabItem {
  readonly id: string;
  readonly label: string;
  readonly closable?: boolean;
  readonly status?: string;
}

interface Props {
  readonly tabs: readonly SurfaceTabItem[];
  readonly selectedId: string | null;
  readonly onSelect: (surfaceId: string) => void;
  readonly onClose?: (surfaceId: string) => void;
  readonly emptyFocusRef?: RefObject<HTMLElement | null>;
}

export function SurfaceTabs({
  tabs,
  selectedId,
  onSelect,
  onClose,
  emptyFocusRef,
}: Props) {
  const [focusedId, setFocusedId] = useState(selectedId ?? tabs[0]?.id ?? null);
  const tabRefs = useRef(new Map<string, HTMLButtonElement>());

  useEffect(() => {
    if (focusedId && tabs.some((tab) => tab.id === focusedId)) return;
    setFocusedId(selectedId ?? tabs[0]?.id ?? null);
  }, [focusedId, selectedId, tabs]);

  const moveFocus = (currentId: string, destination: number) => {
    const currentIndex = tabs.findIndex((tab) => tab.id === currentId);
    const index = destination < 0
      ? (currentIndex - 1 + tabs.length) % tabs.length
      : destination >= tabs.length
        ? (currentIndex + 1) % tabs.length
        : destination;
    const nextId = tabs[index]?.id;
    if (!nextId) return;
    setFocusedId(nextId);
    tabRefs.current.get(nextId)?.focus();
  };

  const close = (surfaceId: string) => {
    const index = tabs.findIndex((tab) => tab.id === surfaceId);
    const next = tabs[index + 1] ?? tabs[index - 1];
    onClose?.(surfaceId);
    if (next) {
      setFocusedId(next.id);
      queueMicrotask(() => tabRefs.current.get(next.id)?.focus());
    } else {
      queueMicrotask(() => emptyFocusRef?.current?.focus());
    }
  };

  const onKeyDown = (event: KeyboardEvent<HTMLButtonElement>, tab: SurfaceTabItem) => {
    switch (event.key) {
      case "ArrowLeft":
        event.preventDefault();
        moveFocus(tab.id, -1);
        break;
      case "ArrowRight":
        event.preventDefault();
        moveFocus(tab.id, tabs.length);
        break;
      case "Home":
        event.preventDefault();
        moveFocus(tab.id, 0);
        break;
      case "End":
        event.preventDefault();
        moveFocus(tab.id, tabs.length - 1);
        break;
      case "Enter":
      case " ":
        event.preventDefault();
        onSelect(tab.id);
        break;
      case "Delete":
        if (tab.closable && onClose) {
          event.preventDefault();
          close(tab.id);
        }
        break;
    }
  };

  return (
    <div className="surface-tabs-shell">
      <div className="surface-tabs" role="tablist" aria-label="Workspace surfaces">
        {tabs.map((tab) => (
          <button
            key={tab.id}
            ref={(node) => {
              if (node) tabRefs.current.set(tab.id, node);
              else tabRefs.current.delete(tab.id);
            }}
            id={`surface-tab-control-${tab.id}`}
            data-testid={`surface-tab-${tab.id}`}
            type="button"
            role="tab"
            aria-selected={tab.id === selectedId}
            aria-controls={`surface-panel-${tab.id}`}
            aria-describedby={
              tab.status && tab.id === selectedId
                ? `surface-tab-status-${tab.id}`
                : undefined
            }
            tabIndex={tab.id === focusedId ? 0 : -1}
            onFocus={() => setFocusedId(tab.id)}
            onClick={() => onSelect(tab.id)}
            onKeyDown={(event) => onKeyDown(event, tab)}
          >
            {tab.label}
          </button>
        ))}
      </div>
      {tabs.some((tab) => tab.id === selectedId && tab.status) && (
        <div className="surface-tab-statuses" aria-label="Surface states">
          {tabs.map((tab) =>
            tab.id === selectedId && tab.status ? (
              <span
                key={tab.id}
                id={`surface-tab-status-${tab.id}`}
                className="surface-tab-status"
              >
                {tab.label}: {tab.status}
              </span>
            ) : null,
          )}
        </div>
      )}
      {onClose && tabs.some((tab) => tab.id === selectedId && tab.closable) && (
        <div className="surface-tab-close-controls" role="toolbar" aria-label="Close surfaces">
          {tabs.map((tab) =>
            tab.id === selectedId && tab.closable ? (
              <button
                key={tab.id}
                type="button"
                data-testid={`surface-tab-close-${tab.id}`}
                aria-label={`Close ${tab.label}`}
                onClick={() => close(tab.id)}
              >
                ×
              </button>
            ) : null,
          )}
        </div>
      )}
    </div>
  );
}
