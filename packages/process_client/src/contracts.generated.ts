// Generated from core.process_interfaces.contract_schemas(). Do not hand edit.
// Schema SHA-256: b3036f7d59ac7c534aa23e8f2f236c3f73780a24464520c696b64223f66738df
export type JsonValue = null | boolean | number | string | ReadonlyArray<JsonValue> | { readonly [key: string]: JsonValue };

export type Action = {
  readonly "action_id": string;
  readonly "checkpoint_id"?: (string | null);
  readonly "enabled": boolean;
  readonly "idempotency_required"?: boolean;
  readonly "operation": "start" | "respond" | "review" | "action" | "cancel" | "attach" | "read" | "navigate";
  readonly "reasons"?: ReadonlyArray<Reason>;
  readonly "subject_digest"?: (string | null);
  readonly "title": string;
};

export type ArtifactRef = {
  readonly "artifact_ref": string;
  readonly "media_type"?: (string | null);
  readonly "representation_id"?: (string | null);
  readonly "result_id"?: (string | null);
  readonly "sha256": string;
};

export type AssessmentRef = {
  readonly "assessment_id": string;
  readonly "currentness": "current" | "stale" | "unresolved";
  readonly "outcome": "pass" | "fail" | "blocked" | "inconclusive" | "error" | "not_applicable";
  readonly "subject_digest": string;
};

export type AuthoringJob = {
  readonly "base_revision"?: (string | null);
  readonly "created_at": string;
  readonly "diagnostics"?: ReadonlyArray<Reason>;
  readonly "job_id": string;
  readonly "process": ProcessRef;
  readonly "repair_attempt"?: number;
  readonly "request_digest": string;
  readonly "request_id": string;
  readonly "revision_id"?: (string | null);
  readonly "role_resolution": RoleResolution;
  readonly "state": "queued" | "resolving" | "generating" | "validating" | "building" | "preview_ready" | "saved" | "failed" | "cancelled";
  readonly "updated_at": string;
};

export type BuildReport = {
  readonly "build_id": string;
  readonly "bundle_digest"?: (string | null);
  readonly "bundled_bytes"?: number;
  readonly "created_at": string;
  readonly "diagnostics"?: ReadonlyArray<Reason>;
  readonly "manifest_digest": string;
  readonly "source_digest": string;
  readonly "state": "built" | "failed" | "cancelled";
  readonly "toolchain_digest": string;
};

export type CapabilityRef = {
  readonly "binding_id": string;
  readonly "resource_digest"?: (string | null);
  readonly "schema_digest": string;
};

export type CodingRole = {
  readonly "allowed_tools"?: ReadonlyArray<"read-interface-contract" | "submit-interface-source">;
  readonly "instructions_digest": string;
  readonly "instructions_version": string;
  readonly "max_repairs"?: number;
  readonly "model_policy"?: "inherit_default";
  readonly "role"?: "process-ui-author";
  readonly "version"?: "1";
};

export type FileBinding = {
  readonly "input_id": string;
  readonly "kind"?: "file";
  readonly "provenance"?: "supplied" | "explicit_default";
  readonly "reference": ArtifactRef;
};

export type InputDefinition = {
  readonly "available_options"?: ReadonlyArray<InputOption>;
  readonly "binding_kind"?: "value" | "file" | "option";
  readonly "block_id": string;
  readonly "current_value"?: ((ValueBinding | FileBinding | OptionBinding) | null);
  readonly "default"?: ((ValueBinding | FileBinding | OptionBinding) | null);
  readonly "dependencies"?: ReadonlyArray<InputDependency>;
  readonly "frame"?: (string | null);
  readonly "input_id": string;
  readonly "option_source"?: (CapabilityRef | null);
  readonly "options_observed_at"?: (string | null);
  readonly "options_stale_after"?: (string | null);
  readonly "port_id": string;
  readonly "required"?: boolean;
  readonly "title": string;
  readonly "unit"?: (string | null);
  readonly "value_schema": Readonly<Record<string, JsonValue>>;
};

export type InputDependency = {
  readonly "binding_id": string;
  readonly "classification": "supplied" | "explicit_default" | "upstream_produced" | "declared_human_response" | "unresolved";
  readonly "interaction_step"?: (string | null);
  readonly "producer_port"?: (string | null);
  readonly "producer_step"?: (string | null);
  readonly "reasons"?: ReadonlyArray<Reason>;
};

export type InputOption = {
  readonly "option_id": string;
  readonly "title": string;
  readonly "value": JsonValue;
};

export type InputSnapshot = {
  readonly "bindings"?: ReadonlyArray<(ValueBinding | FileBinding | OptionBinding)>;
  readonly "created_at": string;
  readonly "digest": string;
  readonly "process": ProcessRef;
  readonly "schema_version"?: "wright.process-input-snapshot/1";
  readonly "snapshot_id": string;
};

export type InteractionContext = {
  readonly "cursor"?: number;
  readonly "generated_at": string;
  readonly "input_digest"?: (string | null);
  readonly "input_snapshot_id"?: (string | null);
  readonly "process": ProcessRef;
  readonly "run_id"?: (string | null);
};

export type InteractionResponse = {
  readonly "actor": string;
  readonly "checkpoint_id": string;
  readonly "created_at": string;
  readonly "digest": string;
  readonly "input_digest": string;
  readonly "integration_test"?: boolean;
  readonly "reason": string;
  readonly "request_id": string;
  readonly "response_id": string;
  readonly "run_id": string;
  readonly "schema_digest": string;
  readonly "subject_digest": string;
  readonly "value": JsonValue;
  readonly "workspace_id": string;
};

export type InteractionSnapshot = {
  readonly "actions"?: ReadonlyArray<Action>;
  readonly "context": InteractionContext;
  readonly "inputs"?: ReadonlyArray<InputDefinition>;
  readonly "interactions"?: ReadonlyArray<PendingInteraction>;
  readonly "navigation"?: ReadonlyArray<NavigationTarget>;
  readonly "next_page"?: (string | null);
  readonly "observations"?: ReadonlyArray<Observation>;
  readonly "outputs"?: ReadonlyArray<OutputRef>;
  readonly "readiness"?: (Readiness | null);
  readonly "schema_version"?: "wright.process-interaction/1";
  readonly "state": "preparing" | "ready" | "running" | "waiting_human" | "waiting_external" | "reconciliation_required" | "completed" | "failed" | "cancelled" | "cancellation_requested";
};

export type InterfaceBinding = {
  readonly "binding_id": string;
  readonly "block_id"?: (string | null);
  readonly "expected_schema"?: (Readonly<Record<string, JsonValue>> | null);
  readonly "fallback"?: (string | null);
  readonly "kind": "input" | "output" | "assessment" | "interaction" | "observation" | "action";
  readonly "port_id"?: (string | null);
  readonly "required"?: boolean;
  readonly "selector": string;
};

export type InterfaceManifest = {
  readonly "bindings"?: ReadonlyArray<InterfaceBinding>;
  readonly "capabilities"?: ReadonlyArray<"process.read" | "process.inputs" | "process.start" | "process.respond" | "process.review" | "process.action" | "process.cancel" | "process.results" | "process.navigate">;
  readonly "client_version": string;
  readonly "interaction_version"?: "wright.process-interaction/1";
  readonly "kit_version": string;
  readonly "navigation"?: ReadonlyArray<NavigationTarget>;
  readonly "parent_revision"?: (string | null);
  readonly "process": ProcessRef;
  readonly "revision_id": string;
  readonly "schema_version"?: "wright.process-ui/1";
  readonly "title": string;
  readonly "ui_id": string;
  readonly "viewers"?: ReadonlyArray<string>;
};

export type InterfaceRevision = {
  readonly "build": BuildReport;
  readonly "created_at": string;
  readonly "generation_request_digest": string;
  readonly "manifest": InterfaceManifest;
  readonly "previewed_at": string;
  readonly "role_resolution": RoleResolution;
  readonly "source_digest": string;
};

export type NavigationTarget = {
  readonly "artifact_ref"?: (string | null);
  readonly "assessment_id"?: (string | null);
  readonly "block_id"?: (string | null);
  readonly "kind": "process" | "block" | "run" | "result" | "assessment" | "evidence";
  readonly "result_id"?: (string | null);
  readonly "run_id"?: (string | null);
};

export type Observation = {
  readonly "activity"?: (string | null);
  readonly "estimated_remaining_seconds"?: (number | null);
  readonly "limitations"?: ReadonlyArray<string>;
  readonly "metrics"?: Readonly<Record<string, JsonValue>>;
  readonly "observation_id": string;
  readonly "observed_at": string;
  readonly "operation_id"?: (string | null);
  readonly "progress_percent"?: (number | null);
  readonly "provider_binding": string;
  readonly "stale_after"?: (string | null);
  readonly "state": "preparing" | "ready" | "running" | "waiting_human" | "waiting_external" | "reconciliation_required" | "completed" | "failed" | "cancelled" | "cancellation_requested";
};

export type OptionBinding = {
  readonly "capability": CapabilityRef;
  readonly "input_id": string;
  readonly "kind"?: "option";
  readonly "observed_at": string;
  readonly "option_id": string;
  readonly "provenance"?: "supplied" | "explicit_default";
  readonly "stale_after"?: (string | null);
  readonly "value": JsonValue;
};

export type OutputRef = {
  readonly "assessments"?: ReadonlyArray<AssessmentRef>;
  readonly "port_id": string;
  readonly "producer_attempt"?: (string | null);
  readonly "representations"?: ReadonlyArray<ArtifactRef>;
  readonly "result_id": string;
  readonly "revision_id"?: (string | null);
  readonly "role": string;
  readonly "step_id": string;
  readonly "supported_viewers"?: ReadonlyArray<string>;
  readonly "title": string;
};

export type PendingInteraction = {
  readonly "checkpoint_id": string;
  readonly "decisions"?: ReadonlyArray<string>;
  readonly "evidence"?: ReadonlyArray<ArtifactRef>;
  readonly "instructions": string;
  readonly "kind": "input" | "review" | "action";
  readonly "response_schema"?: (Readonly<Record<string, JsonValue>> | null);
  readonly "state"?: "waiting" | "responded" | "consumed" | "stale" | "cancelled";
  readonly "step_id": string;
  readonly "subject_digest": string;
};

export type ProcessCancellationReceipt = {
  readonly "request_id": string;
  readonly "run_id": string;
  readonly "state"?: "cancellation_requested";
};

export type ProcessRef = {
  readonly "semantic_digest"?: (string | null);
  readonly "source_contract"?: string;
  readonly "source_digest": string;
  readonly "source_path": string;
  readonly "workspace_id": string;
};

export type ProcessRunEvent = {
  readonly "at"?: (string | null);
  readonly "execution_kind"?: (string | null);
  readonly "kind"?: (string | null);
  readonly "sequence": number;
  readonly "step_id"?: (string | null);
  readonly "task_id"?: (string | null);
  readonly "task_title"?: (string | null);
};

export type ProcessRunEventPage = {
  readonly "cursor": string;
  readonly "events"?: ReadonlyArray<ProcessRunEvent>;
  readonly "following": boolean;
  readonly "has_more": boolean;
  readonly "run_id": string;
  readonly "state": "preparing" | "ready" | "running" | "waiting_human" | "waiting_external" | "reconciliation_required" | "completed" | "failed" | "cancelled" | "cancellation_requested";
};

export type ProcessUI = {
  readonly "active_revision"?: (string | null);
  readonly "archived"?: boolean;
  readonly "created_at": string;
  readonly "process": ProcessRef;
  readonly "title": string;
  readonly "ui_id": string;
  readonly "updated_at": string;
};

export type Readiness = {
  readonly "assessed_at": string;
  readonly "assessment_id": string;
  readonly "dependencies"?: ReadonlyArray<InputDependency>;
  readonly "expires_at"?: (string | null);
  readonly "input_digest"?: (string | null);
  readonly "process": ProcessRef;
  readonly "reasons"?: ReadonlyArray<Reason>;
  readonly "state": "ready" | "blocked" | "unsupported";
};

export type Reason = {
  readonly "binding_id"?: (string | null);
  readonly "code": string;
  readonly "correction": string;
  readonly "message": string;
  readonly "navigation"?: (NavigationTarget | null);
  readonly "step_id"?: (string | null);
  readonly "technical_details_ref"?: (string | null);
};

export type RoleResolution = {
  readonly "adapter": string;
  readonly "capability_scope"?: ReadonlyArray<string>;
  readonly "configuration_digest": string;
  readonly "effective_instructions_digest": string;
  readonly "model_reference": string;
  readonly "profile": CodingRole;
};

export type SourceAsset = {
  readonly "data_base64": string;
  readonly "media_type": "image/png" | "image/jpeg" | "image/webp" | "image/gif";
};

export type SourceEnvelope = {
  readonly "assets"?: Readonly<Record<string, SourceAsset>>;
  readonly "files": Readonly<Record<string, string>>;
};

export type StartReceipt = {
  readonly "created_at": string;
  readonly "initial_outcome"?: "accepted";
  readonly "input_digest": string;
  readonly "input_snapshot_id": string;
  readonly "payload_digest": string;
  readonly "principal_id": string;
  readonly "process": ProcessRef;
  readonly "request_id": string;
  readonly "run_id": string;
  readonly "run_log_path"?: (string | null);
};

export type ValueBinding = {
  readonly "input_id": string;
  readonly "kind"?: "value";
  readonly "provenance"?: "supplied" | "explicit_default";
  readonly "value": JsonValue;
};

export type InputBinding = (ValueBinding & { readonly kind: 'value' }) | (FileBinding & { readonly kind: 'file' }) | (OptionBinding & { readonly kind: 'option' });

export interface ContractTypes {
  readonly Action: Action;
  readonly ArtifactRef: ArtifactRef;
  readonly AssessmentRef: AssessmentRef;
  readonly AuthoringJob: AuthoringJob;
  readonly BuildReport: BuildReport;
  readonly CapabilityRef: CapabilityRef;
  readonly CodingRole: CodingRole;
  readonly FileBinding: FileBinding;
  readonly InputDefinition: InputDefinition;
  readonly InputDependency: InputDependency;
  readonly InputOption: InputOption;
  readonly InputSnapshot: InputSnapshot;
  readonly InteractionContext: InteractionContext;
  readonly InteractionResponse: InteractionResponse;
  readonly InteractionSnapshot: InteractionSnapshot;
  readonly InterfaceBinding: InterfaceBinding;
  readonly InterfaceManifest: InterfaceManifest;
  readonly InterfaceRevision: InterfaceRevision;
  readonly JsonValue: JsonValue;
  readonly NavigationTarget: NavigationTarget;
  readonly Observation: Observation;
  readonly OptionBinding: OptionBinding;
  readonly OutputRef: OutputRef;
  readonly PendingInteraction: PendingInteraction;
  readonly ProcessCancellationReceipt: ProcessCancellationReceipt;
  readonly ProcessRef: ProcessRef;
  readonly ProcessRunEvent: ProcessRunEvent;
  readonly ProcessRunEventPage: ProcessRunEventPage;
  readonly ProcessUI: ProcessUI;
  readonly Readiness: Readiness;
  readonly Reason: Reason;
  readonly RoleResolution: RoleResolution;
  readonly SourceAsset: SourceAsset;
  readonly SourceEnvelope: SourceEnvelope;
  readonly StartReceipt: StartReceipt;
  readonly ValueBinding: ValueBinding;
}

export type ContractName = keyof ContractTypes;
