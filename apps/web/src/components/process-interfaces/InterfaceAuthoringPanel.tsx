import { useCallback, useEffect, useMemo, useRef, useState } from "react";
import type { InterfaceRevision, ProcessUI, Reason } from "@wright/process-client";
import { ProcessUI as ProcessTheme, ReasonNotice, Section } from "@wright/ui-kit";
import {
  interfaceAuthoringReason,
  type InterfaceAuthoringCapabilities,
  type InterfaceAuthoringClient,
  type InterfaceJobView,
} from "../../services/process-ui-authoring";
import {
  createInterfaceAuthoringRecoveryStore,
  type InterfaceAuthoringIntent,
  type InterfaceAuthoringRecoveryStore,
} from "../../services/process-ui-authoring-recovery";

export interface InterfaceAuthoringPanelProps {
  readonly client: InterfaceAuthoringClient;
  readonly sessionId: string;
  readonly viewId: string;
  readonly recoveryStore?: InterfaceAuthoringRecoveryStore;
  readonly onOpenPreview: (view: InterfaceJobView) => Promise<void>;
  readonly onOpenSaved: (ui: ProcessUI, revision: InterfaceRevision) => Promise<void>;
  readonly initialUiId?: string;
}
const terminal = (value: InterfaceJobView) => ["saved", "failed", "cancelled"].includes(value.job.state);
const progress = {
  queued: "Waiting to create the interface", resolving: "Preparing Wright's interface instructions",
  generating: "Creating the interface", validating: "Checking interface bindings",
  building: "Building the preview", preview_ready: "Preview ready", saved: "Interface saved",
  failed: "Interface needs attention", cancelled: "Interface creation cancelled",
};

/** Native controls only. Generated source has no access to this authoring client. */
export function InterfaceAuthoringPanel({client, sessionId, viewId, recoveryStore, onOpenPreview, onOpenSaved, initialUiId}: InterfaceAuthoringPanelProps) {
  const store = useMemo(() => recoveryStore ?? createInterfaceAuthoringRecoveryStore(client.process, sessionId, viewId),
    [client, sessionId, viewId, recoveryStore]);
  const [capabilities, setCapabilities] = useState<InterfaceAuthoringCapabilities>();
  const [capabilitiesLoading, setCapabilitiesLoading] = useState(true);
  const [interfaces, setInterfaces] = useState<readonly ProcessUI[]>([]);
  const [selectedUi, setSelectedUi] = useState(initialUiId ?? "");
  const [revisions, setRevisions] = useState<readonly InterfaceRevision[]>([]);
  const [selectedRevision, setSelectedRevision] = useState("");
  const [instruction, setInstruction] = useState("");
  const [title, setTitle] = useState("Process interface");
  const [intent, setIntent] = useState<InterfaceAuthoringIntent | null>(null);
  const [job, setJob] = useState<InterfaceJobView>();
  const [error, setError] = useState<Reason>();
  const [busy, setBusy] = useState(false);
  const [refresh, setRefresh] = useState(0);
  const [observerExpired, setObserverExpired] = useState(false);
  const [recoveryReady, setRecoveryReady] = useState(false);
  const inflight = useRef(false);
  const owned = useRef(true);
  useEffect(() => {owned.current = true; return () => {owned.current = false;};}, []);

  useEffect(() => {
    const abort = new AbortController();
    setCapabilities(undefined); setCapabilitiesLoading(true);
    // Creation readiness must not wait for an independent saved-interface read.
    const available = client.capabilities(abort.signal).then(value => {
      if (!abort.signal.aborted) setCapabilities(value);
    }).catch(error => {
      if (!abort.signal.aborted) setError(interfaceAuthoringReason(error));
    }).finally(() => {
      if (!abort.signal.aborted) setCapabilitiesLoading(false);
    });
    const saved = client.interfaces(abort.signal).then(value => {
      if (!abort.signal.aborted) setInterfaces(value);
    }).catch(error => {
      if (!abort.signal.aborted) setError(interfaceAuthoringReason(error));
    });
    void Promise.allSettled([available, saved]);
    return () => abort.abort();
  }, [client, refresh]);

  useEffect(() => {
    setJob(undefined);
    setIntent(null); setRecoveryReady(false);
    try {
      const retained = store.read();
      setIntent(retained);
      setRecoveryReady(true);
      if (retained) {setInstruction(retained.request.instruction); setTitle(retained.request.title);}
    } catch (error) {setError(interfaceAuthoringReason(error));}
  }, [store]);

  const ui = interfaces.find(value => value.ui_id === selectedUi);
  const jobId = intent?.job_id;
  useEffect(() => {
    if (!selectedUi) {setRevisions([]); setSelectedRevision(""); return;}
    const abort = new AbortController();
    void client.revisions(selectedUi, abort.signal).then(value => {
      if (!abort.signal.aborted) {
        setRevisions(value);
        // A background refresh must not overwrite a user's revision choice.
        setSelectedRevision(current => value.some(item => item.manifest.revision_id === current)
          ? current : ui?.active_revision ?? "");
      }
    }).catch(error => {if (!abort.signal.aborted) setError(interfaceAuthoringReason(error));});
    return () => abort.abort();
  }, [client, selectedUi, ui?.active_revision, refresh]);

  useEffect(() => {
    if (!jobId) return;
    const abort = new AbortController();
    const deadline = Date.now() + 300_000;
    let timer: ReturnType<typeof setTimeout> | undefined;
    setObserverExpired(false);
    async function observe() {
      try {
        const value = await client.getJob(jobId!, abort.signal);
        if (abort.signal.aborted) return;
        setJob(value);
        if (terminal(value)) return;
        if (Date.now() >= deadline) {setObserverExpired(true); return;}
        timer = setTimeout(() => void observe(), 1000);
      } catch (error) {if (!abort.signal.aborted) {setError(interfaceAuthoringReason(error)); setObserverExpired(true);}}
    }
    void observe();
    return () => {abort.abort(); clearTimeout(timer);};
  }, [client, jobId, refresh]);

  const command = useCallback(async (operation: () => Promise<void>) => {
    if (inflight.current) return;
    inflight.current = true;
    setBusy(true); setError(undefined);
    try {await operation();}
    catch (error) {if (owned.current) setError(interfaceAuthoringReason(error));}
    finally {inflight.current = false; if (owned.current) setBusy(false);}
  }, []);
  const generate = (update: boolean) => void command(async () => {
    if (intent && (!job || !terminal(job))) return;
    const request = {request_id: "interface-" + crypto.randomUUID(), instruction, title,
      ...(update && ui?.active_revision ? {ui_id: ui.ui_id, base_revision: ui.active_revision} : {})};
    const retained: InterfaceAuthoringIntent = {version: "1", process: client.process, request};
    store.write(retained);
    setIntent(retained); setJob(undefined);
    const result = await client.submit(request);
    const accepted = {...retained, job_id: result.job_id};
    store.write(accepted);
    if (owned.current) setIntent(accepted);
  });
  const reconcile = () => void command(async () => {
    if (!intent) return;
    const result = await client.submit(intent.request);
    const accepted = {...intent, job_id: result.job_id};
    store.write(accepted);
    if (owned.current) {setIntent(accepted); setRefresh(value => value + 1);}
  });
  const activeJob = !!intent && (!job || !terminal(job));
  const selected = revisions.find(value => value.manifest.revision_id === selectedRevision);

  return <ProcessTheme><Section title="Interface for this process">
    <p>Create a reusable working interface with Wright's configured model, or open a saved interface.</p>
    {capabilitiesLoading && <p role="status">Checking interface creation availability…</p>}
    {error && <ReasonNotice reason={error}/>}
    {capabilities && !capabilities.available && <ReasonNotice reason={capabilities.compiler_reason ?? {
      code: "CAPABILITY_UNAVAILABLE", message: "Interface creation is unavailable with the current model or adapter.",
      correction: "Use a saved interface or the common working view while authoring is configured."}}/>}
    <label className="wp-field">Interface title<input className="wp-input" value={title} maxLength={512}
      disabled={busy || activeJob} onChange={event => setTitle(event.target.value)}/></label>
    <label className="wp-field">How should this interface help the user?<textarea className="wp-input" value={instruction}
      disabled={busy || activeJob} maxLength={16384} onChange={event => setInstruction(event.target.value)}
      placeholder="For example, compare results, highlight findings and make pending decisions easy to review."/></label>
    <div className="wp-row">
      <button className="wp-button" type="button" disabled={busy || activeJob || !recoveryReady || !capabilities?.available || !instruction.trim() || !title.trim()}
        onClick={() => generate(false)}>Create interface</button>
      <button className="wp-button" type="button" disabled={busy || activeJob || !recoveryReady || !capabilities?.available || !ui?.active_revision || !instruction.trim() || !title.trim()}
        onClick={() => generate(true)}>Update selected interface</button>
    </div>
    {!recoveryReady && <p>Clear the invalid local request locator to prepare another request. This does not cancel any backend job.
      <button className="wp-button" type="button" disabled={busy} onClick={() => void command(async () => {
        store.clear(); setIntent(null); setJob(undefined); setRecoveryReady(true);
      })}>Clear local request locator</button></p>}
    {intent && !intent.job_id && <div role="status"><p>The request outcome is not confirmed. Reconcile this same request before creating another.</p>
      <button className="wp-button" type="button" disabled={busy} onClick={reconcile}>Reconcile request</button></div>}
    {job && <section aria-label="Interface creation progress" aria-live="polite">
      <h3>{progress[job.job.state]}</h3>
      {!!job.job.repair_attempt && <p>Correcting the interface · attempt {job.job.repair_attempt} of {job.job.role_resolution.profile.max_repairs ?? 2}</p>}
      {job.job.diagnostics?.map((reason, index) => <ReasonNotice key={index} reason={reason}/>)}
      <div className="wp-row">
        {job.preview && <button className="wp-button" type="button" disabled={busy} onClick={() => void command(() => onOpenPreview(job))}>Open preview</button>}
        {job.preview && job.job.state === "preview_ready" && <button className="wp-button" type="button" disabled={busy || !job.preview.previewed_at}
          onClick={() => void command(async () => {const saved = await client.save(job, job.preview!.active_revision);
            setSelectedUi(saved.manifest.ui_id); setSelectedRevision(saved.manifest.revision_id);
            setRefresh(value => value + 1);})}>Save interface</button>}
        {!terminal(job) && <button className="wp-button" type="button" disabled={busy} onClick={() => void command(async () => {
          await client.cancel(job.job.job_id); setRefresh(value => value + 1);
        })}>Cancel interface creation</button>}
      </div>
      {job.preview && !job.preview.previewed_at && <p>Open the preview and wait for it to load before saving.</p>}
      <details><summary>Creation details</summary><p>Model: {job.job.role_resolution.model_reference} · adapter: {job.job.role_resolution.adapter}</p>
        <p>Job {job.job.job_id} · revision {job.job.revision_id}</p></details>
    </section>}
    {observerExpired && <p role="status">Progress observation stopped. The backend job keeps its own state.
      <button className="wp-button" type="button" onClick={() => setRefresh(value => value + 1)}>Refresh job status</button></p>}
    <label className="wp-field">Saved interface<select className="wp-input" value={selectedUi} onChange={event => setSelectedUi(event.target.value)}>
      <option value="">Choose an interface</option>{interfaces.filter(value => !!value.active_revision).map(value =>
        <option key={value.ui_id} value={value.ui_id}>{value.title}</option>)}
    </select></label>
    {!!selectedUi && <label className="wp-field">Saved revision<select className="wp-input" value={selectedRevision} onChange={event => setSelectedRevision(event.target.value)}>
      <option value="">Choose a revision</option>{revisions.map(value => <option key={value.manifest.revision_id} value={value.manifest.revision_id}>
        {value.manifest.revision_id === ui?.active_revision ? "Current · " : "Earlier · "}{value.manifest.title} · {value.created_at}
      </option>)}
    </select></label>}
    <div className="wp-row">
      <button className="wp-button" type="button" disabled={busy || !ui || !selected} onClick={() => void command(async () => {
        const compatibility = await client.compatibility(ui!.ui_id, selected!.manifest.revision_id);
        if (compatibility.state !== "compatible") {setError(compatibility.reasons?.[0] ?? {
          code: "UI_INCOMPATIBLE", message: "This saved interface does not match the current process.", correction: "Update its bindings or use the common working view."}); return;}
        await onOpenSaved(ui!, selected!);
      })}>Open saved interface</button>
      <button className="wp-button" type="button" disabled={busy || !ui || !selected || selectedRevision === ui.active_revision}
        onClick={() => void command(async () => {await client.activate(ui!.ui_id, selectedRevision, ui!.active_revision ?? null); setRefresh(value => value + 1);})}>Use this revision</button>
      <button className="wp-button" type="button" disabled={busy} onClick={() => setRefresh(value => value + 1)}>Refresh interfaces</button>
    </div>
  </Section></ProcessTheme>;
}
