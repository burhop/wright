/** Controlled UI data only; no live model, browser preview or engineering claim. */
import type { AuthoringJob, InterfaceRevision, ProcessRef, ProcessUI } from "@wright/process-client";
import type { InterfaceAuthoringCapabilities, InterfaceJobView, ProcessInterfacePresentation } from "../../src/services/process-ui-authoring";

export const authoringProcess: ProcessRef = {workspace_id: "workspace", source_path: "workflows/job.wflow", source_digest: "a".repeat(64)};
export const authoringNow = "2026-10-01T12:00:00Z";
export const authoringUiId = "ui-" + "a".repeat(32);
export const authoringRevisionId = "revision-" + "b".repeat(32);
export const authoringJob: AuthoringJob = {job_id: "job-one", request_id: "author-one", request_digest: "c".repeat(64),
  process: authoringProcess, state: "preview_ready", revision_id: authoringRevisionId,
  created_at: authoringNow, updated_at: authoringNow, role_resolution: {
    profile: {instructions_version: "role-v1", instructions_digest: "a".repeat(64)}, adapter: "controlled-adapter",
    model_reference: "controlled-default", configuration_digest: "b".repeat(64), effective_instructions_digest: "a".repeat(64)}};
export const authoringView: InterfaceJobView = {job: authoringJob, preview: {
  manifest: {ui_id: authoringUiId, revision_id: authoringRevisionId, process: authoringProcess,
    title: "Results comparison", client_version: "1.0.0", kit_version: "1.0.0"},
  build: {build_id: "build-one", source_digest: "d".repeat(64), manifest_digest: "e".repeat(64), bundle_digest: "f".repeat(64),
    toolchain_digest: "a".repeat(64), state: "built", created_at: authoringNow, bundled_bytes: 21},
  active_revision: null, previewed_at: null}};
export const authoringRevision: InterfaceRevision = {manifest: authoringView.preview!.manifest, build: authoringView.preview!.build,
  source_digest: authoringView.preview!.build.source_digest, role_resolution: authoringJob.role_resolution,
  generation_request_digest: authoringJob.request_digest, created_at: authoringNow, previewed_at: authoringNow};
export const authoringUi: ProcessUI = {ui_id: authoringUiId, process: authoringProcess, title: "Results comparison",
  active_revision: authoringRevisionId, created_at: authoringNow, updated_at: authoringNow};
export const authoringCapabilities: InterfaceAuthoringCapabilities = {available: true, role: "process-ui-author/1",
  model: {adapter: "controlled-adapter", available: true}, compiler: {controlled: true}, compiler_reason: null,
  available_process_capabilities: ["process.read", "process.results", "process.navigate"]};

export const authoringPresentation: ProcessInterfacePresentation = {
  descriptor: {schemaVersion: 1, surfaceId: "surface-one", workspaceId: authoringProcess.workspace_id,
    source: {kind: "live_app", sourceId: `process.${authoringUiId}.${authoringRevisionId}`,
      sourceVersion: "a".repeat(64), manifestId: `process.${authoringUiId}.${authoringRevisionId}`},
    title: authoringUi.title, lifecycle: "ready", instance: {instanceId: "instance-one", generation: 1, sharing: "isolated"},
    presentations: [{kind: "panel", eligible: true}], capabilities: [], revision: 2, createdAt: authoringNow, updatedAt: authoringNow},
  launch: {presentationId: "presentation-one", instanceId: "instance-one", generation: 1, kind: "panel",
    absoluteBootstrapUrl: "http://s-presentation-one.localhost:8000/bootstrap?token=controlled", expiresAt: authoringNow},
  binding: {process: authoringProcess, ui_id: authoringUiId, revision_id: authoringRevisionId, run_id: null, read_only: false,
    presentation_id: "presentation-one", generation: 1},
  job_id: authoringJob.job_id, build: authoringView.preview!.build,
};
