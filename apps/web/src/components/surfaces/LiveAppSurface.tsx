import { useCallback, useEffect, useRef, useState } from "react";

import { hostAdapter } from "../../services/host-adapter";
import type { SurfaceDescriptor } from "../../services/surfaces/surface-contract";
import {
  closePresentation,
  createPresentation,
  getPresentationPreference,
  operateLiveApp,
  type LiveAppOperation,
  type PresentationLaunch,
} from "../../services/surfaces/surface-client";
import {
  LiveAppPresenter,
  type LiveFrameStatus,
} from "../../services/surfaces/presenters/live-app-presenter";
import { installElectronReturnAccelerator } from "../../services/surfaces/focus-manager";
import { SurfaceToolbar } from "./SurfaceToolbar";
import { LiveAppControls } from "./LiveAppControls";

export interface LiveAppSurfaceProps {
  readonly descriptor: SurfaceDescriptor;
  readonly sessionId: string;
  readonly onFocusMode?: () => void;
  /** Issued by a native owner that uses its own exact process presentation scope. */
  readonly managedPresentation?: {
    readonly launch: PresentationLaunch;
    readonly close: () => Promise<void>;
    readonly connect?: (
      frame: HTMLIFrameElement,
      ready: () => void,
    ) => () => void;
    readonly onCloseFailure?: (error: unknown) => void;
    readonly closeOnUnmount?: boolean;
  };
}

type ActiveLaunches = Partial<Record<"panel" | "browser", PresentationLaunch>>;

// Give a same-presentation StrictMode remount one turn to retain its issued
// view. A real close disposes/revokes it; this never controls process execution.
const deferredClosures = new Map<string, ReturnType<typeof setTimeout>>();

function recoveryOperation(
  lifecycle: SurfaceDescriptor["lifecycle"],
): LiveAppOperation | null {
  if (lifecycle === "declared") return "start";
  if (lifecycle === "stopped") return "restart";
  if (lifecycle === "failed") return "retry";
  return null;
}

function requiresIsolatedAcknowledgement(
  descriptor: SurfaceDescriptor,
): boolean {
  return (
    descriptor.instance?.sharing === "isolated" ||
    descriptor.source.sourceId === "wright.rivet-editor"
  );
}

function presentationEligible(
  descriptor: SurfaceDescriptor,
  kind: "panel" | "browser",
): boolean {
  return descriptor.presentations.some(
    (value) => value.kind === kind && value.eligible === true,
  );
}

function shouldAutoOpenPanel(descriptor: SurfaceDescriptor): boolean {
  return (
    descriptor.source.sourceId === "wright.rivet-editor" &&
    (descriptor.lifecycle === "ready" ||
      descriptor.lifecycle === "unhealthy") &&
    presentationEligible(descriptor, "panel")
  );
}

export function LiveAppSurface({
  descriptor,
  sessionId,
  onFocusMode,
  managedPresentation,
}: LiveAppSurfaceProps) {
  const root = useRef<HTMLDivElement>(null);
  const panelHost = useRef<HTMLDivElement>(null);
  const runtimeControls = useRef<HTMLDivElement>(null);
  const presenter = useRef<LiveAppPresenter | null>(null);
  const autoPanelKeys = useRef(new Set<string>());
  const [launches, setLaunches] = useState<ActiveLaunches>({});
  const [rememberPreference, setRememberPreference] = useState(false);
  const [preferredKind, setPreferredKind] = useState<
    "panel" | "browser" | undefined
  >();
  const [frameStatus, setFrameStatus] = useState<LiveFrameStatus>("loading");
  const [error, setError] = useState<string | null>(null);
  const [diagnostics, setDiagnostics] = useState(false);
  const [busy, setBusy] = useState(false);
  const managed = useRef(managedPresentation);
  const managedDescriptor = useRef(descriptor);
  const isManaged = managedPresentation !== undefined;
  useEffect(() => {
    managed.current = managedPresentation;
    managedDescriptor.current = descriptor;
  }, [managedPresentation, descriptor]);

  useEffect(() => {
    if (isManaged) return;
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
    isManaged,
  ]);

  useEffect(() => {
    const port = managed.current;
    if (!port || !panelHost.current) return;
    const launch = port.launch;
    const pending = deferredClosures.get(launch.presentationId);
    if (pending !== undefined) clearTimeout(pending);
    deferredClosures.delete(launch.presentationId);
    const next = new LiveAppPresenter(
      launch,
      managedDescriptor.current,
      setFrameStatus,
    );
    presenter.current?.dispose();
    presenter.current = next;
    next.mount(panelHost.current);
    const frame = panelHost.current.querySelector<HTMLIFrameElement>("iframe");
    const disconnect = frame
      ? port.connect?.(frame, () => next.confirmReady())
      : undefined;
    setLaunches({ panel: launch });
    return () => {
      disconnect?.();
      next.dispose();
      if (presenter.current === next) presenter.current = null;
      if (port.closeOnUnmount === false) return;
      const timer = setTimeout(() => {
        deferredClosures.delete(launch.presentationId);
        void port.close().catch((error) => port.onCloseFailure?.(error));
      }, 0);
      deferredClosures.set(launch.presentationId, timer);
    };
  }, [
    managedPresentation?.launch.presentationId,
    managedPresentation?.launch.generation,
    managedPresentation?.launch.absoluteBootstrapUrl,
    descriptor.surfaceId,
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
    if (managed.current) return false;
    setBusy(true);
    setError(null);
    let launch: PresentationLaunch | null = null;
    try {
      const operation = recoveryOperation(descriptor.lifecycle);
      if (operation) {
        await operateLiveApp(
          descriptor.surfaceId,
          descriptor.workspaceId,
          sessionId,
          operation,
        );
        window.dispatchEvent(new Event("wright-surfaces-changed"));
      }
      launch = await createPresentation(
        descriptor.surfaceId,
        descriptor.workspaceId,
        sessionId,
        kind,
        {
          rememberPreference,
          isolatedAcknowledged: requiresIsolatedAcknowledgement(descriptor),
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

  useEffect(() => {
    const instance = descriptor.instance;
    const generation = instance?.generation ?? 0;
    const instanceId = instance?.instanceId ?? "none";
    const key = `${descriptor.surfaceId}:${instanceId}:${generation}`;
    if (
      busy ||
      managed.current ||
      launches.panel ||
      autoPanelKeys.current.has(key) ||
      !shouldAutoOpenPanel(descriptor)
    ) {
      return;
    }
    autoPanelKeys.current.add(key);
    void open("panel");
  }, [busy, descriptor, launches.panel]);

  const close = async (kind: "panel" | "browser") => {
    const launch = launches[kind];
    if (!launch) return;
    setError(null);
    try {
      if (managed.current) await managed.current.close();
      else
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
      className={managedPresentation ? "process-managed-surface" : undefined}
      style={{ height: "100%", display: "flex", flexDirection: "column" }}
    >
      {!managedPresentation && (
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
      )}
      {!managedPresentation && (
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
      )}
      {managedPresentation && launches.panel && (
        <div
          className="process-surface-toolbar"
          role="group"
          aria-label="Interface view controls"
          data-focus-region="toolbar"
        >
          <button
            type="button"
            data-testid="surface-focus"
            onClick={() => presenter.current?.focus()}
          >
            Enter interface
          </button>
          <button type="button" onClick={() => void close("panel")}>
            Close interface view
          </button>
        </div>
      )}
      {error && (
        <p role="alert" data-testid="surface-presentation-error">
          {error}
        </p>
      )}
      {diagnostics && (
        <aside data-testid="surface-diagnostics-panel">
          Source {descriptor.source.sourceId}, revision {descriptor.revision},
          lifecycle {descriptor.lifecycle}.
        </aside>
      )}
      {onFocusMode && (
        <button
          type="button"
          onClick={onFocusMode}
          data-testid="surface-enter-focus"
        >
          Maximize surface while keeping chat
        </button>
      )}
      {launches.panel && !managedPresentation && (
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
          surface controls, the desktop return shortcut
          {!managedPresentation && ", or open the application in your browser"}.
        </p>
      )}
    </div>
  );
}
