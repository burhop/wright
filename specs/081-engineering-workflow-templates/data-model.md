# Data Model: Engineering Workflow Templates

## EngineeringWorkflowTemplate

Immutable packaged description of one example.

| Field                                | Type                    | Rules                                                                                  |
| ------------------------------------ | ----------------------- | -------------------------------------------------------------------------------------- |
| `template_id`                        | slug                    | Stable and unique; one of the ten contract IDs.                                        |
| `version`                            | semantic version        | Immutable once packaged.                                                               |
| `title`, `summary`, `discipline`     | text                    | Human-readable and bounded.                                                            |
| `source_resource`, `layout_resource` | package paths           | Canonical source and separate presentation; both validated before catalog publication. |
| `source_digest`, `layout_digest`     | SHA-256                 | Match packaged bytes.                                                                  |
| `provided_inputs`                    | InputAsset[]            | Redistributable, attributed, digest-bound fixtures only.                               |
| `requested_inputs`                   | InputRequirement[]      | User-provided values/files with type, units and constraints.                           |
| `expected_outputs`                   | OutputDeclaration[]     | Named artifact/result contracts, never screenshots alone.                              |
| `capability_requirements`            | CapabilityRequirement[] | Exact operation need and qualification evidence.                                       |
| `external_effects`                   | ExternalEffectKind[]    | Visible before creation and run.                                                       |
| `acceptance_profile`                 | identifier/version      | Selects versioned assertions without dispatching runtime by template ID.               |
| `preview`                            | PreviewDescriptor       | Licensed local visual and alt text.                                                    |
| `definition_status`                  | enum                    | `reviewed`, `deprecated`, or `withdrawn`.                                              |

The catalog contains exactly ten active reviewed entries. Template identity is not runtime operation identity.

## TemplateInstanceProvenance

Hidden host metadata linking an editable workflow to its origin.

| Field                                              | Type               | Rules                                    |
| -------------------------------------------------- | ------------------ | ---------------------------------------- |
| `workspace_id`, `workflow_id`                      | identifier         | Must match the created workspace source. |
| `template_id`, `template_version`                  | identifier/version | Exact packaged origin.                   |
| `template_source_digest`, `template_layout_digest` | SHA-256            | Exact creation subject.                  |
| `created_at`, `created_by`                         | timestamp/actor    | Existing local identity policy applies.  |

Instance creation generates fresh workflow/block identities and revision zero/one according to the canonical source contract. The instance is editable and never follows later template updates automatically.

## CapabilityRequirement and CapabilityEvidence

`CapabilityRequirement` declares a generic operation family, artifact/result expectations, platform/setup constraints, external effects, and minimum qualification level. `CapabilityEvidence` records independent facts:

- catalog/discovery source identity;
- pinned installation and startup;
- protocol/tool/schema discovery;
- real backend operation;
- Wright gateway operation;
- declared artifact verification;
- engineering assertion verification;
- negative/recovery behavior;
- reviewed timestamp and evidence links.

Current readiness is derived from requirements plus configuration/availability and cannot be stored as a self-asserted success flag.

## ApprovalCheckpoint

| Field                                              | Type                 | Rules                                                                                                                |
| -------------------------------------------------- | -------------------- | -------------------------------------------------------------------------------------------------------------------- |
| `checkpoint_id`                                    | immutable identifier | Unique; never reused.                                                                                                |
| `workspace_id`, `workflow_id`, `run_id`, `step_id` | identifiers          | Exact runtime position.                                                                                              |
| `action_kind`                                      | enum                 | Initially `printer_transfer`, `supplier_upload_preview`, or `cart_quote_handoff`. Purchase/payment is not supported. |
| `subject`                                          | ApprovalSubject      | Canonical exact inputs described below.                                                                              |
| `subject_digest`                                   | SHA-256              | Canonical digest over the complete subject.                                                                          |
| `state`                                            | enum                 | `pending`, `approved`, `changes_requested`, `expired`, `stale`, or `consumed`.                                       |
| `decision`                                         | decision record      | Actor, timestamp, bounded reason, exact prior state.                                                                 |
| `expires_at`                                       | optional timestamp   | Required when destination/session semantics expire.                                                                  |
| `continuation`                                     | ContinuationPointer  | Next safe step and completed operation evidence.                                                                     |

`ApprovalSubject` includes accepted definition revision/digest, all relevant input and artifact digests, exact server/tool/schema bindings, destination/device identity, settings such as profile/material/quantity/services, action request, and current reconciled destination state. Any changed component yields a new digest and makes the old checkpoint stale.

State transitions:

```text
pending -> approved -> consumed
pending -> changes_requested
pending -> expired
approved -> stale (subject/current state changed before dispatch)
approved -> expired
approved -> consumed (one authorized dispatch attempt recorded)
```

An ambiguous external outcome consumes the checkpoint and records `outcome_unknown`; reconciliation precedes any new authorization.

## ExternalActionRecord

Records intent and observed outcome without equating transfer with physical completion.

Fields: action ID/kind, checkpoint/subject digest, idempotency strategy, requested endpoint/device, safe argument summary, dispatch start/end, tool call evidence, outcome (`not_dispatched`, `accepted`, `rejected`, `unknown`, `cancelled_before_dispatch`), receipt/status evidence, reconciliation state, and trace ID. Secrets are references to configured credentials and never persisted in arguments or capture packages.

## EngineeringAssertion

Fields: assertion ID/version, target artifact/result, metric/method, units, expected condition/tolerance, observed value, evidence reference, state (`pass`, `fail`, `inconclusive`), and correction target. Assertions evaluate actual output. `inconclusive` blocks promotion and dependent gates.

## EngineeringArtifact

Reuse workspace artifact identity and lineage. Add representation roles needed by the templates: source image, manufacturer reference, design document, CAD native, STEP, source mesh, repaired mesh, slice package, support preview, solver mesh/case/field, result table, DXF, fabrication bundle, printer receipt, supplier preview, and capture asset. One logical result may have multiple representations; identity and transforms remain explicit.

## WorkflowContinuation

Fields: run ID, accepted definition snapshot, completed step records, pending checkpoint, next step, external-action records, resume token/digest, and state (`running`, `awaiting_approval`, `resuming`, `succeeded`, `failed`, `cancelled`, `outcome_unknown`). Resume revalidates workspace authorization, source/subject digests, bindings, destination state, and prior output existence before executing the next step.

## DemonstrationCapturePackage

Fields: capture ID, source run/revision/digest, selected artifact/result digests, locally rendered assets, sequence/caption draft, disclosure labels, input rights/attribution, redaction report, creation timestamp, and manifest digest. It contains no publishing target or posting credential.
