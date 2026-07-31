import { useCallback, useEffect, useRef, useState } from "react";

import { hostAdapter } from "../../services/host-adapter";
import type { SurfaceDescriptor } from "../../services/surfaces/surface-contract";
import {
  closePresentation,
  createPresentation,
  getPresentationPreference,
  type PresentationLaunch,
} from "../../services/surfaces/surface-client";
import {
  LiveAppPresenter,
  type LiveFrameStatus,
} from "../../services/surfaces/presenters/live-app-presenter";
import { installElectronReturnAccelerator } from "../../services/surfaces/focus-manager";
import { SurfaceToolbar } from "./SurfaceToolbar";
import { LiveAppControls } from "./LiveAppControls";

interface Props {
  readonly descriptor: SurfaceDescriptor;
  readonly sessionId: string;
  readonly onFocusMode: () => void;
}

type ActiveLaunches = Partial<Record<"panel" | "browser", PresentationLaunch>>;

export function LiveAppSurface({ descriptor, sessionId, onFocusMode }: Props) {
  const root = useRef<HTMLDivElement>(null);
  const panelHost = useRef<HTMLDivElement>(null);
  const runtimeControls = useRef<HTMLDivElement>(null);
  const presenter = useRef<LiveAppPresenter | null>(null);
  const [launches, setLaunches] = useState<ActiveLaunches>({});
  const [rememberPreference, setRememberPreference] = useState(false);
  const [preferredKind, setPreferredKind] = useState<
    "panel" | "browser" | undefined
  >();
  const [frameStatus, setFrameStatus] = useState<LiveFrameStatus>("loading");
  const [error, setError] = useState<string | null>(null);
  const [diagnostics, setDiagnostics] = useState(false);
  const [busy, setBusy] = useState(false);

  useEffect(() => {
    void getPresentationPreference(
      descriptor.surfaceId,
      descriptor.workspaceId,
      sessionId,
    )
      .then((decision) => {
        setPreferredKind(decision.remembered ? decision.kind : undefined);
      })
      .catch(() => undefined);
  }, [
    descriptor.source.sourceVersion,
    descriptor.surfaceId,
    descriptor.workspaceId,
    sessionId,
  ]);

  useEffect(() => {
    const current = presenter.current;
    if (!current) return;
    if (!["ready", "unhealthy"].includes(descriptor.lifecycle)) {
      current.dispose();
      presenter.current = null;
      setLaunches({});
      setFrameStatus("loading");
      return;
    }
    try {
      current.update(descriptor);
    } catch (reason) {
      current.dispose();
      presenter.current = null;
      setLaunches({});
      setError(reason instanceof Error ? reason.message : String(reason));
    }
  }, [descriptor]);

  useEffect(
    () => () => {
      presenter.current?.dispose();
      presenter.current = null;
    },
    [],
  );

  const returnToHost = useCallback(() => {
    root.current
      ?.querySelector<HTMLElement>('[data-testid="surface-focus"]')
      ?.focus();
  }, []);

  useEffect(
    () => installElectronReturnAccelerator(returnToHost),
    [returnToHost],
  );

  const open = async (kind: "panel" | "browser"): Promise<boolean> => {
    setBusy(true);
    setError(null);
    let launch: PresentationLaunch | null = null;
    try {
      launch = await createPresentation(
        descriptor.surfaceId,
        descriptor.workspaceId,
        sessionId,
        kind,
        {
          rememberPreference,
          isolatedAcknowledged: descriptor.instance?.sharing === "isolated",
        },
      );
      if (kind === "browser") {
        await hostAdapter.openExternal(launch.absoluteBootstrapUrl);
      } else {
        presenter.current?.dispose();
        const next = new LiveAppPresenter(launch, descriptor, setFrameStatus);
        presenter.current = next;
        if (!panelHost.current) throw new Error("Panel host is unavailable");
        next.mount(panelHost.current);
      }
      if (rememberPreference) setPreferredKind(kind);
      setLaunches((current) => ({ ...current, [kind]: launch! }));
      return true;
    } catch (reason) {
      if (kind === "browser" && launch) {
        void closePresentation(
          descriptor.surfaceId,
          launch.presentationId,
          descriptor.workspaceId,
          sessionId,
        ).catch(() => undefined);
      }
      setError(reason instanceof Error ? reason.message : String(reason));
      return false;
    } finally {
      setBusy(false);
    }
  };

  const close = async (kind: "panel" | "browser") => {
    const launch = launches[kind];
    if (!launch) return;
    setError(null);
    try {
      await closePresentation(
        descriptor.surfaceId,
        launch.presentationId,
        descriptor.workspaceId,
        sessionId,
      );
    } catch (reason) {
      setError(reason instanceof Error ? reason.message : String(reason));
      return;
    }
    if (kind === "panel") {
      presenter.current?.dispose();
      presenter.current = null;
    }
    setLaunches((current) => {
      const next = { ...current };
      delete next[kind];
      return next;
    });
  };

  return (
    <div
      ref={root}
      data-testid="live-app-surface"
      style={{ height: "100%", display: "flex", flexDirection: "column" }}
    >
      <div data-focus-region="toolbar">
        <SurfaceToolbar
          descriptor={descriptor}
          activeKinds={Object.keys(launches) as ("panel" | "browser")[]}
          rememberPreference={rememberPreference}
          preferredKind={preferredKind}
          frameStatus={
            frameStatus === "unknown" || frameStatus === "blocked"
              ? frameStatus
              : undefined
          }
          busy={busy}
          onOpen={(kind) => {
            void open(kind);
          }}
          onOpenBoth={async () => {
            const panelOpened = await open("panel");
            const browserOpened = await open("browser");
            if (panelOpened !== browserOpened) {
              setError(
                panelOpened
                  ? "The panel opened, but the system browser presentation failed."
                  : "The browser opened, but the workspace panel presentation failed.",
              );
            }
          }}
          onFocus={() => presenter.current?.focus()}
          onClosePresentation={close}
          onStopApplication={() => {
            runtimeControls.current
              ?.querySelector<HTMLButtonElement>('[data-operation="stop"]')
              ?.click();
          }}
          onDiagnostics={() => setDiagnostics((value) => !value)}
          onRememberPreferenceChange={setRememberPreference}
        />
      </div>
      <div ref={runtimeControls}>
        <LiveAppControls
          descriptor={descriptor}
          sessionId={sessionId}
          onRuntimeChange={(runtime) => {
            if (runtime.state === "stopped" || runtime.state === "failed") {
              presenter.current?.dispose();
              presenter.current = null;
              setLaunches({});
            }
          }}
        />
      </div>
      {error && <p role="alert">{error}</p>}
      {diagnostics && (
        <aside data-testid="surface-diagnostics-panel">
          Source {descriptor.source.sourceId}, revision {descriptor.revision},
          lifecycle {descriptor.lifecycle}.
        </aside>
      )}
      <button
        type="button"
        onClick={onFocusMode}
        data-testid="surface-enter-focus"
      >
        Maximize surface while keeping chat
      </button>
      {launches.panel && (
        <button
          type="button"
          className="workspace-surface-control"
          data-testid="surface-enter-frame"
          onClick={() => presenter.current?.focus()}
        >
          Enter embedded application
        </button>
      )}
      <div
        ref={panelHost}
        data-testid="surface-panel-host"
        style={{ flex: 1, minHeight: 320 }}
      />
      {launches.panel && (
        <button
          type="button"
          className="workspace-surface-control"
          data-testid="surface-return-host"
          data-focus-region="frame-return"
          onClick={returnToHost}
        >
          Return to surface controls
        </button>
      )}
      {(frameStatus === "unknown" || frameStatus === "blocked") && (
        <p
          role="note"
          aria-live="polite"
          data-testid="surface-frame-unverified"
        >
          Keyboard escape from this application is unverified. Use Return to
          surface controls, the desktop return shortcut, or open the application
          in your browser.
        </p>
      )}
    </div>
  );
}
