/** Native workspace authoring. This API is never bundled into generated UIs. */
import {
  assertContract,
  assertPresentationContext,
  assertProcessReference,
  ProcessClientError,
  type AuthoringJob,
  type BuildReport,
  type Compatibility,
  type InterfaceManifest,
  type InterfaceRevision,
  type ProcessRef,
  type ProcessUI,
  type ProcessPresentationContext,
  type Reason,
  type StartReceipt,
} from "@wright/process-client";
import { hostAdapter } from "./host-adapter";
import { sameProcessReference } from "./process-navigation";
import { parseSurfaceDescriptor, type SurfaceDescriptor } from "./surfaces/surface-contract";
import { parsePresentationLaunch, type PresentationLaunch } from "./surfaces/surface-client";

export interface InterfaceAuthoringCapabilities {
  readonly available: boolean;
  readonly role: "process-ui-author/1";
  readonly model: Readonly<Record<string, unknown>>;
  readonly compiler: Readonly<Record<string, unknown>> | null;
  readonly compiler_reason: Reason | null;
  readonly available_process_capabilities: readonly string[];
}
export interface InterfaceJobView {
  readonly job: AuthoringJob;
  /** Actual retained authoring correlation; absent on older native responses. */
  readonly trace_id?: string | null;
  readonly preview: {
    readonly manifest: InterfaceManifest;
    readonly build: BuildReport;
    readonly active_revision: string | null;
    readonly previewed_at: string | null;
  } | null;
}
export interface ProcessInterfacePresentation {
  readonly descriptor: SurfaceDescriptor;
  readonly launch: PresentationLaunch;
  readonly binding: Omit<ProcessPresentationContext, "schema_version" | "session_id" | "capabilities">;
  readonly job_id: string;
  readonly build: BuildReport;
}
export interface InterfaceAuthoringRequest {
  readonly request_id: string;
  readonly instruction: string;
  readonly title: string;
  readonly ui_id?: string;
  readonly base_revision?: string;
}
const record = (value: unknown): Record<string, unknown> => {
  if (!value || typeof value !== "object" || Array.isArray(value)) throw new TypeError("Invalid native interface response");
  return value as Record<string, unknown>;
};
const id = (value: unknown): string => {
  if (typeof value !== "string" || !/^[a-z0-9][a-z0-9._:-]{0,159}$/i.test(value)) throw new TypeError("Invalid interface identity");
  return value;
};
const date = (value: unknown): string => {
  if (typeof value !== "string" || Number.isNaN(Date.parse(value))) throw new TypeError("Invalid interface observation date");
  return value;
};
const nullableId = (value: unknown) => value === null ? null : id(value);

export function interfaceAuthoringReason(error: unknown): Reason {
  return error instanceof ProcessClientError ? error.reason : {
    code: "CAPABILITY_UNAVAILABLE",
    message: "Wright could not finish this interface request.",
    correction: "Reopen its saved job to reconcile progress before retrying. The common working view remains available.",
  };
}

export function createInterfaceAuthoringClient(reference: ProcessRef, sessionId: string) {
  const process = assertProcessReference(reference);
  const source = {session_id: id(sessionId), path: process.source_path, expected_storage_digest: process.source_digest};
  const query = new URLSearchParams(source).toString();
  const base = hostAdapter.resolveBackendUrl("/api/workspace/process-interfaces");
  const exact = (value: ProcessRef) => {
    if (!sameProcessReference(value, process)) throw new ProcessClientError({
      code: "SCOPE_DENIED", message: "This interface response belongs to another accepted process.",
      correction: "Open the exact saved process in its owning workspace."
    });
  };
  async function request(path: string, body?: Record<string, unknown>, signal?: AbortSignal, keepalive = false): Promise<unknown> {
    const response = await hostAdapter.fetch(base + path + (body ? "" : (path.includes("?") ? "&" : "?") + query), {
      method: body ? "POST" : "GET", signal, ...(keepalive ? {keepalive: true} : {}),
      ...(body ? {headers: {"Content-Type": "application/json"}, body: JSON.stringify({...body, ...source})} : {}),
    });
    if (response.status === 204 && response.ok) return null;
    const raw = await response.text();
    if (new TextEncoder().encode(raw).byteLength > 2_097_152) throw new TypeError("Interface response exceeds its supported size");
    let value: unknown;
    try { value = JSON.parse(raw); } catch { throw new TypeError("Interface response is not valid JSON"); }
    if (!response.ok) {
      const envelope = record(value);
      // Native API exception handlers publish ErrorEnvelope.details; direct
      // FastAPI transports may still use detail. Both carry a checked Reason.
      const detail = envelope.details ?? envelope.detail;
      if (detail && typeof detail === "object") {
        const reason = record(detail).reason;
        if (reason) throw new ProcessClientError(assertContract("Reason", reason));
      }
      throw new ProcessClientError({code: "CAPABILITY_UNAVAILABLE", message: "This interface request is unavailable.",
        correction: "Reconcile the saved job in Wright or use the common working view."});
    }
    return value;
  }
  const job = (raw: unknown): AuthoringJob => {
    const value = assertContract("AuthoringJob", raw);
    exact(value.process);
    return value;
  };
  const jobView = (raw: unknown): InterfaceJobView => {
    const value = record(raw), checked = job(value.job);
    const traceId = value.trace_id == null ? null : id(value.trace_id);
    if (value.preview === null) {
      if (["preview_ready", "saved"].includes(checked.state)) throw new TypeError("Built job has no verified preview");
      return {job: checked, preview: null, trace_id: traceId};
    }
    if (!["preview_ready", "saved"].includes(checked.state)) throw new TypeError("Unbuilt job cannot expose a preview");
    const built = record(value.preview);
    const manifest = assertContract("InterfaceManifest", built.manifest);
    const report = assertContract("BuildReport", built.build);
    exact(manifest.process);
    if (manifest.revision_id !== checked.revision_id || report.state !== "built") throw new TypeError("Preview and job revisions disagree");
    return {job: checked, trace_id: traceId, preview: {manifest, build: report, active_revision: nullableId(built.active_revision),
      previewed_at: built.previewed_at === null ? null : date(built.previewed_at)}};
  };
  const presentation = (raw: unknown, readonly: boolean, uiId?: string, revisionId?: string, runId?: string): ProcessInterfacePresentation => {
    const value = record(raw), binding = record(value.binding);
    const context = assertPresentationContext({...binding, schema_version: "wright.process-presentation/1", session_id: sessionId,
      capabilities: ["process.read"]});
    exact(context.process);
    const descriptor = parseSurfaceDescriptor(value.descriptor);
    const launch = parsePresentationLaunch(value.launch, "panel");
    if (context.read_only !== readonly || context.run_id !== (runId ?? null) ||
        (uiId !== undefined && context.ui_id !== uiId) || (revisionId !== undefined && context.revision_id !== revisionId) ||
        descriptor.workspaceId !== process.workspace_id || descriptor.source.kind !== "live_app" ||
        descriptor.source.sourceId !== `process.${context.ui_id}.${context.revision_id}` ||
        context.presentation_id !== launch.presentationId || context.generation !== launch.generation ||
        descriptor.instance?.instanceId !== launch.instanceId || descriptor.instance.generation !== launch.generation)
      throw new TypeError("Managed interface presentation identity disagrees");
    const report = assertContract("BuildReport", value.build);
    if (report.state !== "built") throw new TypeError("Managed interface has no successful build");
    return {descriptor, launch, binding: {process: context.process, ui_id: context.ui_id, revision_id: context.revision_id,
      run_id: context.run_id, read_only: context.read_only, presentation_id: context.presentation_id, generation: context.generation},
      job_id: id(value.job_id), build: report};
  };
  return Object.freeze({
    process,
    async startReceipt(view: ProcessInterfacePresentation, requestId?: string): Promise<StartReceipt | null> {
      if (view.binding.read_only || view.binding.run_id !== null) throw new TypeError("Only a preparation view has a start request");
      const value = record(await request("/presentations/start-receipt", {
        surface_id: view.descriptor.surfaceId, presentation_id: view.launch.presentationId,
        ...(requestId !== undefined ? {request_id: id(requestId)} : {})}));
      if (value.receipt === null) return null;
      const receipt = assertContract("StartReceipt", value.receipt);
      exact(receipt.process);
      if (requestId !== undefined && receipt.request_id !== requestId) throw new TypeError("View start request identity disagrees");
      return receipt;
    },
    async capabilities(signal?: AbortSignal): Promise<InterfaceAuthoringCapabilities> {
      const value = record(await request("/authoring-capabilities", undefined, signal));
      exact(assertProcessReference(value.process));
      if (typeof value.available !== "boolean" || value.role !== "process-ui-author/1" ||
          !Array.isArray(value.available_process_capabilities) || value.available_process_capabilities.some(cap => typeof cap !== "string"))
        throw new TypeError("Invalid interface authoring capabilities");
      return {available: value.available, role: value.role, model: record(value.model),
        compiler: value.compiler === null ? null : record(value.compiler),
        compiler_reason: value.compiler_reason === null ? null : assertContract("Reason", value.compiler_reason),
        available_process_capabilities: value.available_process_capabilities as string[]};
    },
    async submit(value: InterfaceAuthoringRequest) { return job(await request("/authoring-jobs", {...value, request_id: id(value.request_id)})); },
    async getJob(jobId: string, signal?: AbortSignal) {
      const value = jobView(await request(`/authoring-jobs/${encodeURIComponent(id(jobId))}`, undefined, signal));
      if (value.job.job_id !== jobId) throw new TypeError("Authoring job identity disagrees");
      return value;
    },
    async cancel(jobId: string) {
      const value = job(await request(`/authoring-jobs/${encodeURIComponent(id(jobId))}/cancel`, {}));
      if (value.job_id !== jobId) throw new TypeError("Cancelled authoring job identity disagrees");
      return value;
    },
    async interfaces(signal?: AbortSignal): Promise<readonly ProcessUI[]> {
      const values = record(await request("/uis", undefined, signal)).interfaces;
      if (!Array.isArray(values) || values.length > 256) throw new TypeError("Invalid interface list");
      return values.map(raw => {
        const ui = assertContract("ProcessUI", raw);
        if (ui.process.workspace_id !== process.workspace_id || ui.process.source_path !== process.source_path) throw new TypeError("Interface association disagrees");
        return ui;
      });
    },
    async revisions(uiId: string, signal?: AbortSignal): Promise<readonly InterfaceRevision[]> {
      const values = record(await request(`/uis/${encodeURIComponent(id(uiId))}/revisions`, undefined, signal)).revisions;
      if (!Array.isArray(values) || values.length > 256) throw new TypeError("Invalid interface revision list");
      return values.map(raw => {
        const value = assertContract("InterfaceRevision", raw);
        if (value.manifest.ui_id !== uiId || value.manifest.process.workspace_id !== process.workspace_id ||
            value.manifest.process.source_path !== process.source_path) throw new TypeError("Interface revision association disagrees");
        return value;
      });
    },
    async compatibility(uiId: string, revisionId?: string): Promise<Compatibility> {
      const suffix = revisionId ? `?revision_id=${encodeURIComponent(id(revisionId))}` : "";
      const value = assertContract("Compatibility", await request(`/uis/${encodeURIComponent(id(uiId))}/compatibility` + suffix));
      exact(value.current_process);
      if (value.ui_id !== uiId || (revisionId !== undefined && value.revision_id !== revisionId)) throw new TypeError("Compatibility revision identity disagrees");
      return value;
    },
    async preview(jobId: string, requestId: string, runId?: string) {
      const value = presentation(await request(`/authoring-jobs/${encodeURIComponent(id(jobId))}/preview`, {
        request_id: id(requestId), ...(runId ? {run_id: id(runId)} : {})}), true, undefined, undefined, runId);
      if (value.job_id !== jobId) throw new TypeError("Preview job identity disagrees");
      return value;
    },
    async present(uiId: string, revisionId: string, requestId: string, runId?: string) {
      return presentation(await request(`/uis/${encodeURIComponent(id(uiId))}/present`, {
        request_id: id(requestId), revision_id: id(revisionId), ...(runId ? {run_id: id(runId)} : {})}), false, uiId, revisionId, runId);
    },
    async close(value: ProcessInterfacePresentation, options?: {readonly keepalive?: boolean}) {
      await request("/presentations/close", {surface_id: value.descriptor.surfaceId, presentation_id: value.binding.presentation_id}, undefined, options?.keepalive);
    },
    async save(view: InterfaceJobView, expectedActive: string | null) {
      if (!view.preview || !view.preview.build.bundle_digest) throw new TypeError("No built preview to save");
      const {manifest, build} = view.preview;
      const value = assertContract("InterfaceRevision", await request(`/uis/${encodeURIComponent(manifest.ui_id)}/revisions/${encodeURIComponent(manifest.revision_id)}/save`, {
        job_id: view.job.job_id, source_digest: build.source_digest, manifest_digest: build.manifest_digest,
        bundle_digest: build.bundle_digest, expected_active_revision: expectedActive}));
      exact(value.manifest.process);
      if (value.manifest.ui_id !== manifest.ui_id || value.manifest.revision_id !== manifest.revision_id || value.build.bundle_digest !== build.bundle_digest)
        throw new TypeError("Saved interface revision identity disagrees");
      return value;
    },
    async activate(uiId: string, revisionId: string, expectedActive: string | null) {
      const value = assertContract("ProcessUI", await request(`/uis/${encodeURIComponent(id(uiId))}/activate`, {
        revision_id: id(revisionId), expected_active_revision: expectedActive}));
      if (value.ui_id !== uiId || value.active_revision !== revisionId || value.process.workspace_id !== process.workspace_id || value.process.source_path !== process.source_path)
        throw new TypeError("Activated interface revision identity disagrees");
      return value;
    },
  });
}
export type InterfaceAuthoringClient = ReturnType<typeof createInterfaceAuthoringClient>;
