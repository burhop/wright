import type { SurfaceDescriptor } from "../../services/surfaces/surface-contract";
import { SurfaceStatus } from "./SurfaceStatus";

type PresentationKind = "panel" | "browser";

interface Props {
  readonly descriptor: SurfaceDescriptor;
  readonly activeKinds: readonly PresentationKind[];
  readonly rememberPreference: boolean;
  readonly preferredKind?: PresentationKind;
  readonly frameStatus?: "ready" | "unknown" | "blocked";
  readonly busy?: boolean;
  readonly onOpen: (kind: PresentationKind) => void | Promise<void>;
  readonly onOpenBoth: () => void | Promise<void>;
  readonly onFocus: () => void;
  readonly onClosePresentation: (
    kind: PresentationKind,
  ) => void | Promise<void>;
  readonly onStopApplication: () => void | Promise<void>;
  readonly onDiagnostics: () => void;
  readonly onRememberPreferenceChange: (value: boolean) => void;
  readonly onRestart?: () => void | Promise<void>;
}

function eligibility(
  descriptor: SurfaceDescriptor,
  kind: PresentationKind,
): boolean {
  return descriptor.presentations.some(
    (value) => value.kind === kind && value.eligible === true,
  );
}

export function SurfaceToolbar({
  descriptor,
  activeKinds,
  rememberPreference,
  preferredKind,
  frameStatus,
  busy = false,
  onOpen,
  onOpenBoth,
  onFocus,
  onClosePresentation,
  onStopApplication,
  onDiagnostics,
  onRememberPreferenceChange,
  onRestart,
}: Props) {
  const ready =
    descriptor.lifecycle === "ready" || descriptor.lifecycle === "unhealthy";
  const canOpen =
    ready ||
    descriptor.lifecycle === "declared" ||
    descriptor.lifecycle === "stopped" ||
    descriptor.lifecycle === "failed";
  const panelEligible = eligibility(descriptor, "panel");
  const browserEligible = eligibility(descriptor, "browser");
  const sharing = descriptor.instance?.sharing;
  const panelActive = activeKinds.includes("panel");
  const browserActive = activeKinds.includes("browser");

  return (
    <header
      data-testid="surface-toolbar"
      aria-label={`${descriptor.title} controls`}
    >
      <SurfaceStatus
        lifecycle={descriptor.lifecycle}
        frameStatus={frameStatus}
      />
      {sharing === "shared" ? (
        <p>Panel and browser use the same running instance.</p>
      ) : sharing === "isolated" ? (
        <p>Each presentation uses isolated preview credentials.</p>
      ) : null}
      {activeKinds.length > 0 && (
        <p>
          Closing this view keeps the workspace-lifetime application running.
        </p>
      )}
      {preferredKind && <p>Preferred presentation: {preferredKind}.</p>}
      <div role="toolbar" aria-label="Surface presentation actions">
        {canOpen && panelEligible && !panelActive && (
          <button
            type="button"
            data-testid="surface-open-panel"
            disabled={busy}
            onClick={() => void onOpen("panel")}
          >
            Open in panel{preferredKind === "panel" ? " (preferred)" : ""}
          </button>
        )}
        {canOpen && browserEligible && !browserActive && (
          <button
            type="button"
            data-testid="surface-open-browser"
            disabled={busy}
            onClick={() => void onOpen("browser")}
          >
            Open in browser{preferredKind === "browser" ? " (preferred)" : ""}
          </button>
        )}
        {ready && panelEligible && browserEligible && sharing === "shared" && (
          <button
            type="button"
            data-testid="surface-open-both"
            disabled={busy}
            onClick={() => void onOpenBoth()}
          >
            Open both
          </button>
        )}
        {panelActive && (
          <>
            <button type="button" data-testid="surface-focus" onClick={onFocus}>
              Focus panel
            </button>
            <button
              type="button"
              data-testid="surface-close-panel"
              onClick={() => void onClosePresentation("panel")}
            >
              Close panel presentation
            </button>
          </>
        )}
        {browserActive && (
          <button
            type="button"
            data-testid="surface-close-browser"
            onClick={() => void onClosePresentation("browser")}
          >
            Close browser presentation
          </button>
        )}
        {["starting", "ready", "unhealthy"].includes(descriptor.lifecycle) && (
          <button
            type="button"
            data-testid="surface-stop-application"
            onClick={() => void onStopApplication()}
          >
            Stop application
          </button>
        )}
        {onRestart &&
          ["stopped", "failed", "unhealthy"].includes(descriptor.lifecycle) && (
            <button
              type="button"
              data-testid="surface-restart-application"
              onClick={() => void onRestart()}
            >
              Restart application
            </button>
          )}
        <button
          type="button"
          data-testid="surface-diagnostics"
          onClick={onDiagnostics}
        >
          Diagnostics
        </button>
      </div>
      {ready && (
        <label>
          <input
            type="checkbox"
            checked={rememberPreference}
            onChange={(event) =>
              onRememberPreferenceChange(event.target.checked)
            }
          />
          Remember this presentation choice
        </label>
      )}
    </header>
  );
}
