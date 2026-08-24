import { useCallback, useEffect, useRef, useState } from "react";

import { hostAdapter } from "../../services/host-adapter";
import {
  directRivetEditorUrl,
  directRivetWorkflowUrl,
} from "../../services/rivet-editor";
import {
  ensureRivetEditorRunning,
  retryRivetEditorRunning,
} from "../../services/rivet-editor-lifecycle";
import {
  closePresentation,
  createPresentation,
  type PresentationLaunch,
} from "../../services/surfaces/surface-client";
import type { RivetWorkflowDocument } from "../../services/workspace-service";
import { DirectRivetSurface } from "./DirectRivetSurface";

interface ManagedRivetSurfaceProps {
  readonly workspaceId: string;
  readonly sessionId: string;
  readonly initialSlug: string;
  readonly onWorkflowLoaded?: (workflow: RivetWorkflowDocument) => void;
  readonly externalRevisionToken?: string | null;
}

interface ManagedLaunch {
  readonly url: string;
  readonly surfaceId: string | null;
  readonly presentation: PresentationLaunch | null;
}

interface LaunchRequest {
  readonly id: number;
  readonly mode: "passive" | "explicit-retry";
}

export function ManagedRivetSurface({
  workspaceId,
  sessionId,
  initialSlug,
  onWorkflowLoaded,
  externalRevisionToken = null,
}: ManagedRivetSurfaceProps) {
  const [launch, setLaunch] = useState<ManagedLaunch | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [launchRequest, setLaunchRequest] = useState<LaunchRequest>({
    id: 0,
    mode: "passive",
  });
  const [retrying, setRetrying] = useState(false);
  const launchRef = useRef<ManagedLaunch | null>(null);
  const previewRecoveryAttempts = useRef(0);
  const retryInFlight = useRef(false);

  useEffect(() => {
    let active = true;
    setLaunch(null);
    setError(null);

    const configuredDirectUrl = directRivetEditorUrl();
    if (configuredDirectUrl) {
      retryInFlight.current = false;
      setRetrying(false);
      const directUrl =
        directRivetWorkflowUrl(initialSlug) ?? configuredDirectUrl;
      const next = { url: directUrl, surfaceId: null, presentation: null };
      launchRef.current = next;
      setLaunch(next);
      return () => {
        active = false;
        launchRef.current = null;
      };
    }

    const startEditor =
      launchRequest.mode === "explicit-retry"
        ? retryRivetEditorRunning
        : ensureRivetEditorRunning;
    void startEditor(workspaceId, sessionId)
      .then(async (surfaceId) => {
        // React may retire this effect while the shared, idempotent startup is
        // still resolving. Do not issue a presentation that this mount can no
        // longer display; Strict Mode and rapid tab changes otherwise create a
        // burst of immediately abandoned preview sessions.
        if (!active) return;
        const presentation = await createPresentation(
          surfaceId,
          workspaceId,
          sessionId,
          "panel",
          { isolatedAcknowledged: true },
        );
        if (!active) {
          await closePresentation(
            surfaceId,
            presentation.presentationId,
            workspaceId,
            sessionId,
          ).catch(() => undefined);
          return;
        }
        const next = {
          url: presentation.absoluteBootstrapUrl,
          surfaceId,
          presentation,
        };
        launchRef.current = next;
        setLaunch(next);
      })
      .catch((reason) => {
        if (active) {
          setError(reason instanceof Error ? reason.message : String(reason));
        }
      })
      .finally(() => {
        if (active && launchRequest.mode === "explicit-retry") {
          retryInFlight.current = false;
          setRetrying(false);
        }
      });

    return () => {
      active = false;
      const current = launchRef.current;
      launchRef.current = null;
      if (current?.surfaceId && current.presentation) {
        void closePresentation(
          current.surfaceId,
          current.presentation.presentationId,
          workspaceId,
          sessionId,
        ).catch(() => undefined);
      }
    };
  }, [initialSlug, launchRequest, sessionId, workspaceId]);

  const openInBrowser = useCallback(async () => {
    if (!launch) return;
    if (!launch.surfaceId) {
      await hostAdapter.openExternal(launch.url, { approvedDirectUrl: true });
      return;
    }
    const browser = await createPresentation(
      launch.surfaceId,
      workspaceId,
      sessionId,
      "browser",
      { isolatedAcknowledged: true },
    );
    await hostAdapter.openExternal(browser.absoluteBootstrapUrl);
  }, [launch, sessionId, workspaceId]);

  const editorReady = useCallback(() => {
    previewRecoveryAttempts.current = 0;
  }, []);

  const renewExpiredPreview = useCallback(
    (reason: string) => {
      if (previewRecoveryAttempts.current < 1) {
        previewRecoveryAttempts.current += 1;
        setLaunchRequest((value) => ({
          id: value.id + 1,
          mode: "passive",
        }));
        return;
      }
      const current = launchRef.current;
      launchRef.current = null;
      setLaunch(null);
      setError(`Rivet preview authorization could not be renewed (${reason}).`);
      if (current?.surfaceId && current.presentation) {
        void closePresentation(
          current.surfaceId,
          current.presentation.presentationId,
          workspaceId,
          sessionId,
        ).catch(() => undefined);
      }
    },
    [sessionId, workspaceId],
  );

  if (!launch) {
    return (
      <section
        data-testid="managed-rivet-startup"
        aria-label="Rivet editor startup"
        style={{
          width: "100%",
          height: "100%",
          display: "grid",
          placeItems: "center",
          color: error
            ? "var(--color-error, #ef4444)"
            : "var(--color-secondary, #a0aec0)",
        }}
      >
        <div style={{ textAlign: "center" }}>
          <p role={error ? "alert" : "status"}>
            {error ?? "Starting Rivet for this workspace..."}
          </p>
          {error && (
            <button
              type="button"
              data-testid="managed-rivet-retry"
              disabled={retrying}
              onClick={() => {
                if (retryInFlight.current) return;
                retryInFlight.current = true;
                previewRecoveryAttempts.current = 0;
                setRetrying(true);
                setLaunchRequest((value) => ({
                  id: value.id + 1,
                  mode: "explicit-retry",
                }));
              }}
            >
              {retrying ? "Retrying…" : "Retry"}
            </button>
          )}
        </div>
      </section>
    );
  }

  return (
    <DirectRivetSurface
      url={launch.url}
      sessionId={sessionId}
      initialSlug={initialSlug}
      externalRevisionToken={externalRevisionToken}
      onWorkflowLoaded={onWorkflowLoaded}
      onEditorReady={editorReady}
      onEditorUnavailable={renewExpiredPreview}
      onOpenInBrowser={() => void openInBrowser()}
    />
  );
}
