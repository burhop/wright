import { useEffect, useRef, useState } from "react";
import { ProcessUI, ReasonNotice } from "@wright/ui-kit";
import { ProcessClientError, type Reason, type NavigationTarget } from "@wright/process-client";
import { interfaceAuthoringReason, type InterfaceAuthoringClient, type ProcessInterfacePresentation } from "../../services/process-ui-authoring";
import type { ProcessInterfaceLocator } from "../../services/process-workspace-tabs";
import { LiveAppSurface } from "../surfaces/LiveAppSurface";
import { connectProcessPresentation } from "../../services/process-presentation-host";

export interface ProcessInterfaceViewProps {
  readonly client: InterfaceAuthoringClient;
  readonly locator: ProcessInterfaceLocator;
  readonly sessionId: string;
  readonly viewId: string;
  readonly runId?: string;
  readonly onUseCommon: () => void;
  readonly onRunAttached?: (runId: string) => void;
  readonly onNavigate?: (target: NavigationTarget) => Promise<void>;
}
interface ViewLease {
  readonly key: string;
  readonly client: InterfaceAuthoringClient;
  readonly opening: Promise<ProcessInterfacePresentation>;
  released: boolean;
  timer?: ReturnType<typeof setTimeout>;
}

/** Presentation lifetime only. Opening never submits or resumes process work. */
export function ProcessInterfaceView({client, locator, sessionId, viewId, runId, onUseCommon, onRunAttached, onNavigate}: ProcessInterfaceViewProps) {
  const [presentation, setPresentation] = useState<ProcessInterfacePresentation>();
  const [error, setError] = useState<Reason>();
  const [reopen, setReopen] = useState(0);
  const lease = useRef<ViewLease | null>(null);
  const jobId = locator.kind === "preview" ? locator.job_id : undefined;
  const key = JSON.stringify([sessionId, viewId, runId ?? null, locator.kind, locator.ui_id, locator.revision_id, jobId, reopen]);

  useEffect(() => {
    let current = lease.current;
    if (!current || current.key !== key || current.client !== client) {
      const requestId = "presentation-" + crypto.randomUUID();
      const opening = (async () => {
        if (jobId !== undefined) {
          const job = await client.getJob(jobId);
          if (job.preview?.manifest.ui_id !== locator.ui_id || job.preview.manifest.revision_id !== locator.revision_id)
            throw new Error("The preview does not identify this interface revision.");
          return client.preview(jobId, requestId, runId);
        }
        const compatible = await client.compatibility(locator.ui_id, locator.revision_id);
        if (compatible.state !== "compatible") {
          const reason = compatible.reasons?.[0];
          throw new ProcessClientError(reason ?? {code: "UI_INCOMPATIBLE", message: "The saved interface needs updated bindings.",
            correction: "Update the interface or use the common working view."});
        }
        return client.present(locator.ui_id, locator.revision_id, requestId, runId);
      })();
      current = {key, client, opening, released: false};
      lease.current = current;
    }
    const held = current;
    if (held.timer !== undefined) clearTimeout(held.timer);
    held.released = false;
    setPresentation(undefined); setError(undefined);
    let observing = true;
    void held.opening.then(value => {if (observing && !held.released) setPresentation(value);})
      .catch(reason => {if (observing) setError(interfaceAuthoringReason(reason));});
    return () => {
      observing = false;
      held.timer = setTimeout(() => {
        held.released = true;
        void held.opening.then(value => held.client.close(value).catch(() => {
          window.dispatchEvent(new CustomEvent("wright-process-ui-close-failed", {detail: {viewId}}));
        }), () => undefined);
      }, 0);
    };
  }, [client, key, jobId, locator.kind, locator.ui_id, locator.revision_id, runId, viewId]);

  return <div style={{height: "100%", minHeight: 360, display: "flex", flexDirection: "column"}}>
    <ProcessUI><div className="wp-row">
      <button className="wp-button" type="button" onClick={onUseCommon}>Use common working view</button>
      <button className="wp-button" type="button" onClick={() => setReopen(value => value + 1)}>Reopen interface view</button>
    </div>
    {locator.kind === "preview" && <p>Interface preview · process actions are unavailable. Opening it does not start work.</p>}
    {error && <ReasonNotice reason={error}/>}
    {!presentation && !error && <p role="status">Opening the saved interface…</p>}
    </ProcessUI>
    {presentation && <LiveAppSurface descriptor={presentation.descriptor} sessionId={sessionId}
      managedPresentation={{launch: presentation.launch, close: () => client.close(presentation), closeOnUnmount: false,
        connect: (frame, ready) => connectProcessPresentation(frame, presentation, {ready, navigate: onNavigate,
          started: async requestId => {
            const receipt = await client.startReceipt(presentation, requestId);
            if (receipt) onRunAttached?.(receipt.run_id);
          }, failed: error => setError(interfaceAuthoringReason(error))}),
        onCloseFailure: error => setError(interfaceAuthoringReason(error))}}/>}
  </div>;
}
