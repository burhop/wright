# Feature Specification: Chatter and Model-Enabled Rivet Scenarios

**Feature Branch**: `codex/rivet-engineering-program` (feature identity: `072-chatter-rivet-scenarios`)

**Created**: 2026-08-13

**Status**: Complete

**Input**: User description: "Package Wright's CNC Chatter model safely and let Rivet combine its typed local inference with deterministic CAD and simulated CAM capabilities in reviewed, reproducible engineering workflows."

## User Scenarios & Testing _(mandatory)_

### User Story 1 - Qualify the exact Chatter model for local use (Priority: P1)

As an engineer, I can inspect and install one exact Wright Chatter package whose ownership, training provenance, serving conversion, compatibility, limits, and evidence are explicit, without loading an unsafe training artifact or downloading anything implicitly.

**Why this priority**: A model-enabled workflow is not trustworthy until the model package itself has a narrow, verified, reversible serving boundary.

**Independent Test**: Inspect the package offline, import its exact reviewed data-only serving artifacts, verify their digests, run mandatory positive/negative/boundary vectors, and confirm the package becomes ready only on a compatible host.

**Acceptance Scenarios**:

1. **Given** the immutable Wright Chatter source dataset/recipe and a trusted conversion result, **When** the engineer inspects the package, **Then** it shows exact source identities, internal-use terms, artifact digests, runtime, resources, model card, validation evidence, supported input population, output semantics, and limitations before installation.
2. **Given** the original training artifact uses a pickle-family format, **When** Wright evaluates it as package content, **Then** Wright rejects it and accepts only the separately produced, parity-validated, data-only serving export.
3. **Given** a changed artifact, recipe, feature order, preprocessing constant, classifier structure, threshold, runtime, or validation result, **When** an existing plan is confirmed or an installation is loaded, **Then** the exact identity mismatch blocks readiness and explains how to re-review the package.

---

### User Story 2 - Screen simulated cutting candidates truthfully (Priority: P1)

As a manufacturing engineer, I can submit a bounded set of fully specified simulated cutting candidates and receive stable/chatter classifications, an uncalibrated chatter score, threshold margin, applicability facts, and model limitations with explicit units.

**Why this priority**: The model is useful only when its result is understandable and does not overstate certainty or safe operating authority.

**Independent Test**: Score known stable, known chatter, near-threshold, out-of-domain, malformed, and boundary candidates through the installed model capability; verify exact fields, units, order, threshold behavior, warnings, and deterministic evidence.

**Acceptance Scenarios**:

1. **Given** one to one hundred schema-valid simulated candidates, **When** the model evaluates them, **Then** each result preserves candidate identity and order and includes predicted state, chatter score, decision threshold, signed threshold margin, calibration status, applicability status, limitations, and exact model/runtime evidence.
2. **Given** an uncalibrated classifier, **When** results are presented, **Then** Wright labels the score as an uncalibrated model output, never calls it a probability of real-world safety, and never invents a confidence interval.
3. **Given** missing, extra, non-finite, wrongly ordered, unit-incompatible, or out-of-contract values, **When** inference is requested, **Then** evaluation fails or returns an explicit out-of-domain result before any advisory ranking is published.

---

### User Story 3 - Run a reviewed chatter-aware CNC workflow in Rivet (Priority: P1)

As an engineer, I can run a reviewed Rivet scenario that combines deterministic CAD context, simulated CAM candidate generation, and the exact enabled Chatter model to create a reproducible advisory comparison without controlling a machine.

**Why this priority**: This is the program's first complete workflow that combines multiple MCP domains with a specialized local engineering model.

**Independent Test**: Execute a deterministic Tier-1 scenario through the real Rivet worker, Wright gateway, two independent CAD/CAM fixture MCPs, and an isolated Chatter adapter; verify engineering invariants, exact provenance, cleanup, and the absence of machine-control authority.

**Acceptance Scenarios**:

1. **Given** a reviewed graph with exact CAD, simulated CAM, and Chatter bindings, **When** the run starts, **Then** preflight revalidates the workflow, MCP tools, model installation/test evidence, resources, input/output schemas, units, threshold, and policy identities before any child call.
2. **Given** deterministic fixture and tool context plus several simulated cutting candidates, **When** the graph runs, **Then** Rivet obtains candidates from the CAM fixture, evaluates them through the Chatter capability, compares only the supplied discrete candidates, and emits an advisory report with exact artifact/model/tool provenance.
3. **Given** a completed report, **When** an engineer reviews it, **Then** the report clearly states simulation-only status, score calibration limits, applicability limits, required human review, and that no spindle speed, feed, G-code, machine setting, or physical action was issued.

---

### User Story 4 - Diagnose cancellation, resources, and drift (Priority: P1)

As an engineer, I receive bounded and actionable recovery when a model is missing, stale, incompatible, resource-blocked, cancelled, or fails during a workflow, without a late or partial result being reported as success.

**Why this priority**: Specialized local inference can consume meaningful resources and must fail truthfully inside a multi-capability run.

**Independent Test**: Exercise missing installation, failed standard test, stale binding, insufficient RAM/disk, runtime crash, timeout, concurrent reservation, cancellation before load, cancellation during inference, and cleanup residue; verify stable attribution and no late success.

**Acceptance Scenarios**:

1. **Given** insufficient declared resources, **When** preflight or load admission runs, **Then** the scenario is blocked before model execution and shows the required/available resource facts and a safe recovery action.
2. **Given** cancellation while a model call is active, **When** Wright revokes run authority, **Then** the adapter receives cancellation within the bounded interval, reservations are released, late output is ignored, and the final run records clean cancellation or explicit possible residue.
3. **Given** an exact model, runtime, contract, vector, MCP validation, workflow, or policy identity change, **When** an old reviewed run is retried, **Then** it is stale and must be reviewed again rather than silently rebound.

---

### User Story 5 - Reproduce and extend model-enabled scenarios safely (Priority: P2)

As a maintainer, I can reproduce a prior chatter-aware run and add another model-enabled scenario through versioned public contracts without adding model-specific branches to the generic Rivet runner or weakening gateway authority.

**Why this priority**: Chatter should prove a reusable model-capability seam rather than become bespoke workflow code.

**Independent Test**: Re-run the same exact scenario and compare identities/results; then register a generated test model scenario through the same extension contracts and prove invalid, colliding, stale, or model-specific runner changes are rejected.

**Acceptance Scenarios**:

1. **Given** unchanged workflow, bindings, Chatter package/runtime, inputs, fixtures, and policy, **When** the scenario is rerun, **Then** material results and evidence identities match within declared tolerances while timing/resource observations remain separately variable.
2. **Given** any material identity or input change, **When** runs are compared, **Then** the difference is explicit and the system never claims exact reproduction.
3. **Given** a new model-enabled scenario manifest using approved contracts, **When** it passes conformance, **Then** it can use the existing gateway/Rivet path without modifying the generic runner for that model family.

### Edge Cases

- The trusted training recipe is reproducible but produces different serving bytes because a dependency, seed, feature order, float precision, or exporter version changed.
- The source dataset or training artifact is available but ownership, internal-use terms, redistribution, or support responsibility is not recorded.
- A parity aggregate passes while one safety-relevant stable/chatter boundary vector changes class.
- A score equals the exact classification threshold or falls in a declared near-threshold review band.
- Two candidates share a display label but have different immutable candidate identities or source artifacts.
- A candidate is numerically valid but outside the recorded machine/tool/process/training population.
- The model is enabled but its mandatory test evidence, runtime health, or resource observation is stale.
- An MCP returns candidate features in a different order, unit, coordinate convention, or schema revision.
- A workflow tries to infer or interpolate an untested continuous stability region from discrete sampled candidates.
- Cancellation races with load completion, one candidate result, report generation, or child cleanup.
- A report contains a low chatter score but another engineering invariant such as clearance, force, deflection, or tool reach fails.
- A workflow or prompt attempts to turn advisory output into G-code, controller settings, machine motion, spindle start, or other physical actuation.

## Requirements _(mandatory)_

### Functional Requirements

#### Chatter package and trust

- **FR-001**: Wright MUST provide one distinct Chatter model package through the existing engineering model library, with a full immutable package identity and no embedded model payload in Git or application distributions.
- **FR-002**: The package MUST identify the Wright owner/support boundary, source repository revision, immutable training dataset digest, recipe/configuration identity, split/membership evidence, training/evaluation evidence, serving-conversion identity, and exact selected artifact digests.
- **FR-003**: Until an explicit owner decision broadens the terms, the Chatter package MUST be labelled internal-use and non-redistributable, and export MUST remain blocked.
- **FR-004**: Wright MUST reject Joblib, pickle, source code, estimator objects, training environments, and arbitrary repository artifacts as Chatter package content.
- **FR-005**: The installable Chatter artifact MUST be a narrowly validated data-only serving representation that declares all preprocessing constants, ordered features, classifier structure, class order, threshold, numeric precision, and bounded resource needs required for inference.
- **FR-006**: Producing the serving representation MUST be an explicit trusted conversion outside normal installation; installation MUST NOT train, deserialize the source artifact, install a converter, contact Data Vault, or mutate a global environment.
- **FR-007**: Conversion evidence MUST bind exact source data/recipe/environment/export identities and compare the serving representation with the trusted source evaluator over frozen membership and boundary cases, including per-row disagreement and score-delta ceilings.
- **FR-008**: Any change to source, ownership terms, data, recipe, feature contract, preprocessing, classifier, class order, threshold, serving bytes, adapter, resource ceiling, limitations, or validation evidence MUST create a new reviewed package revision.
- **FR-009**: A host without the separately reviewed compatible runtime MUST keep Chatter inspectable but incompatible and MUST NOT offer install or enable actions.

#### Typed inference and truthful interpretation

- **FR-010**: The Chatter capability MUST accept a versioned bounded batch of one to one hundred candidates with stable candidate identities and the complete ordered numeric input contract.
- **FR-011**: Every input field MUST declare engineering meaning, unit, finite numeric type, valid range, and whether it is a measured, identified, assumed, or simulated value; missing, extra, duplicate, reordered, non-finite, and unit-incompatible inputs MUST fail closed.
- **FR-012**: The output for each candidate MUST preserve order/identity and contain predicted `stable` or `chatter` state, uncalibrated chatter score, exact decision threshold, signed decision margin, calibration status, applicability status, warnings, and exact model/runtime/schema evidence.
- **FR-013**: Wright MUST NOT describe an uncalibrated chatter score or threshold margin as a real-world safety probability, statistical confidence interval, certification result, or guarantee.
- **FR-014**: Near-threshold and out-of-population results MUST require review and MUST NOT participate in an automatic “safe” recommendation.
- **FR-015**: The capability MAY compare and rank only caller-supplied discrete simulated candidates; it MUST NOT interpolate stability lobes, synthesize an untested operating point, or prescribe a machine setting.
- **FR-016**: Any candidate comparison MUST retain failed non-model engineering invariants and MUST NOT rank a candidate as preferred when clearance, force, deflection, tool reach, or another required invariant fails.
- **FR-017**: Mandatory vectors MUST include known stable, known chatter, near-threshold, malformed, out-of-range, non-finite, feature-order, unit, and resource/cancellation cases and MUST bind exact expected predicates and tolerances.
- **FR-018**: Model readiness MUST require successful serving-artifact verification, runtime compatibility/health, conversion-parity evidence, and every mandatory Chatter vector against the exact installation.

#### Rivet scenario and governed execution

- **FR-019**: Wright MUST provide a deterministic Tier-1 chatter-aware CNC scenario that combines at least one CAD context capability, one simulated CAM candidate capability, and the exact Chatter model capability in one reviewed Rivet graph.
- **FR-020**: All MCP and model capabilities MUST be discovered, reviewed, bound, invoked, cancelled, and audited through Wright's existing workspace gateway; Rivet MUST receive no child configuration, runtime endpoint, process handle, reusable credential, or independent lifecycle authority.
- **FR-021**: Scenario preflight MUST revalidate workflow/graph, node, MCP server/tool/schema/validation, model package/installation/adapter/vector, candidate schema/units, workspace grant, resource, policy, and scenario-manifest identities before start.
- **FR-022**: The scenario MUST use deterministic, proprietary-free CAD and simulated CAM fixtures in normal gates and MUST NOT require a real CAM application, CNC controller, machine tool, credential, paid service, GPU, or network.
- **FR-023**: The CAM capability MUST emit explicit candidate identities, units, simulated provenance, and the complete Chatter input contract; no prompt-derived or dynamically named model/tool binding is permitted.
- **FR-024**: The scenario MUST evaluate only the exact candidates returned by the bound CAM capability and MUST correlate each model result to its candidate and producing child receipt.
- **FR-025**: The scenario report MUST include selected discrete comparison, rejected candidates/reasons, all engineering invariant outcomes, simulation-only status, uncalibrated-score explanation, limitations, human-review action, and exact artifact/tool/model/workflow evidence.
- **FR-026**: The report and authorized artifacts MUST NOT contain G-code, controller instructions, spindle/feed override commands, machine endpoints, credentials, raw host paths, reusable run authority, private source rows, or model payload bytes.
- **FR-027**: Run evidence MUST identify the exact model package/revision/variant/artifact-set, adapter/runtime, test evidence, workspace binding, input/output schema, threshold, resource class, provider kind, model call, and correlated MCP calls without misrepresenting the model as an MCP server.
- **FR-028**: Reproduction comparison MUST distinguish material workflow/MCP/model/input/policy/evidence differences from non-material timing, resource observation, request, trace, and host diagnostic differences.

#### Lifecycle, failure, and extension safety

- **FR-029**: Model load and inference MUST pass existing resource admission and reservations; concurrent workflows MUST not overcommit declared RAM, CPU, output, or time ceilings.
- **FR-030**: Cancellation MUST revoke run authority first, reach active model/MCP calls within the configured bound, suppress late success, release reservations, stop owned processes, and record clean cleanup or explicit possible residue.
- **FR-031**: Missing, disabled, stale, corrupt, untested, incompatible, resource-blocked, timed-out, crashed, cancelled, or residue-producing model failures MUST have stable attribution and actionable recovery in both the scenario report and UI.
- **FR-032**: A failed or cancelled model call MUST NOT publish a preferred candidate, successful scenario, ready installation, or complete advisory artifact.
- **FR-033**: Model-enabled scenario extension contracts MUST remain provider-neutral and collision-safe; generic Rivet runner, gateway, scenario harness, and UI code MUST NOT branch on Chatter feature names or model IDs.
- **FR-034**: Structured events and traces MUST correlate scenario, workflow run, node, gateway request, model operation, candidate, artifact, adapter, cancellation, and cleanup identities while excluding inputs, scores tied to private rows, secrets, paths, commands, and payload bytes.
- **FR-035**: Normal tests MUST use generated or already-reviewed tiny deterministic fixtures and MUST run offline without training the real model, loading Joblib, credentials, proprietary apps, GPUs, hardware, large downloads, or physical actuation.
- **FR-036**: The exact real Chatter conversion/qualification probe MUST be explicitly selected, use only the reviewed local source fixture and ignored Wright-controlled state, execute no cloud or paid resource, and leave datasets, source artifacts, serving bytes, caches, and environments untracked.
- **FR-037**: No model result, workflow node, fixture, report, example, or UI action may start a spindle, move an axis, change a controller, generate executable machine instructions, apply heat, or perform any other physical actuation.

### Non-Functional Requirements

- **NFR-001**: A cold local Chatter call for up to one hundred candidates MUST complete within three seconds p95 on the reference CPU host, excluding initial package installation; a warm call, if supported, MUST complete within one second p95.
- **NFR-002**: Scenario preflight MUST complete within one second p95 and the deterministic Tier-1 chatter-aware scenario MUST complete within thirty seconds p95 on the reference development host.
- **NFR-003**: Cancellation MUST reach the model runtime within one second and owned runtime/MCP cleanup MUST finish within five seconds or report bounded possible residue.
- **NFR-004**: Material Chatter vector and scenario evidence MUST be deterministic across repeated supported CPU runs within declared score tolerances; timing/resource/trace observations MUST not alter the material digest.
- **NFR-005**: Candidate batches, artifact/report metadata, progress/events, logs, runtime messages, and evidence MUST have explicit item, string, and encoded-byte ceilings; model/source payloads MUST never enter ordinary records.
- **NFR-006**: Chatter inspection, candidate result, scenario preflight/start/progress/cancel/report/recovery, and comparison journeys MUST be keyboard operable, usable at 320 CSS pixels and 200% zoom, convey status without color alone, manage focus, and have no serious or critical automated accessibility findings.
- **NFR-007**: Restart after any model/scenario transition MUST preserve the last truthful durable state, invalidate non-reusable authority, and never convert an interrupted call into success.
- **NFR-008**: Installed Chatter inspection, standard test, inference, scenario execution with local fixtures, report review, comparison, disable, and removal MUST remain fully usable while air-gapped.

### Key Entities

- **Chatter Source Identity**: Immutable owner, repository revision, training dataset digest, recipe/configuration, split/membership evidence, evaluation, and support/terms record.
- **Chatter Serving Revision**: Exact data-only artifact set, feature/preprocessing/classifier/threshold representation, conversion identity, adapter, resources, limitations, and compatibility.
- **Conversion Parity Evidence**: Frozen population/membership identity, source/serving outputs, agreement and delta aggregates, boundary outcomes, environment identities, and material/observation digests.
- **Cutting Candidate**: Stable candidate identity plus complete typed Chatter feature values, units, value-origin classifications, simulated CAD/CAM provenance, and engineering invariant status.
- **Chatter Result**: Candidate-correlated predicted state, uncalibrated score, threshold, margin, calibration/applicability state, warnings, model identities, and evidence reference.
- **Model Capability Binding**: Workspace-scoped exact model package/installation/adapter/task/schema/vector/policy identity used by a reviewed Rivet node.
- **Chatter Scenario Manifest**: Versioned CAD/CAM/model requirements, graph/artifact contracts, invariants, environment tiers, failure policy, and physical-actuation prohibition.
- **Chatter Advisory Report**: Immutable bounded scenario outcome correlating candidate/model/MCP artifacts, comparisons, rejected reasons, limitations, cleanup, and reproducibility identities.

## Success Criteria _(mandatory)_

### Measurable Outcomes

- **SC-001**: When reviewed private inputs are locally available and the explicit qualification probe is selected, the exact real Chatter serving revision achieves at least 99.5% class agreement with its trusted source evaluator on the frozen qualification population, mean absolute score delta no greater than 0.01, maximum score delta no greater than 0.05, and no disagreement on mandatory stable/chatter boundary vectors.
- **SC-002**: When that explicit private qualification is selected, one exact Chatter package traverses inspect, effect plan, offline import, digest verification, install, standard test, enable, typed inference, disable, uninstall, and reference-safe purge using ignored local payload state and records complete bounded evidence; normal gates prove the same lifecycle with the generated Chatter-shaped package.
- **SC-003**: A deterministic Tier-1 Rivet graph invokes at least two independent fixture MCP capabilities and a tested local Chatter serving revision through Wright, passes at least three exact CAM-returned discrete candidates into the model node, and passes every declared engineering/provenance/cleanup invariant within thirty seconds. Normal gates use the generated revision; the explicit private qualification substitutes the real revision when reviewed inputs are available.
- **SC-004**: Every accepted Chatter result displays units, predicted state, uncalibrated score, threshold, margin, calibration/applicability status, limitations, simulation-only status, and exact model evidence; zero accepted surfaces label the score as a real-world safety probability or certainty.
- **SC-005**: One hundred percent of deterministic missing/stale/corrupt/schema/unit/resource/runtime/cancellation/residue and physical-actuation cases fail at the correct boundary with stable attribution and no late success, preferred candidate, or executable machine instruction.
- **SC-006**: Repeating an unchanged model-enabled scenario produces identical material model/candidate/artifact/assertion evidence within declared numeric tolerances; every material change appears in comparison output and invalidates exact reproduction.
- **SC-007**: Normal gates run without network, credentials, proprietary applications, paid services, GPUs, hardware, real-model training, Joblib loading, large downloads, committed model weights, or physical actuation.
- **SC-008**: When selected, the real opt-in qualification leaves zero Chatter dataset, training artifact, serving payload, environment, cache, or runtime scratch file tracked in Git; normal distribution scans always find no model payload in wheel, source archive, native runtime, or Docker application layer.
- **SC-009**: Cancellation reaches the model runtime within one second in all deterministic tests, and cleanup finishes within five seconds or records explicit bounded residue with an inspect-before-retry action.
- **SC-010**: Automated accessibility tests report no serious or critical findings across inspection, result, preflight, run, cancellation, report, and comparison journeys, including keyboard-only, narrow-width, and 200% zoom cases.
- **SC-011**: A maintainer can add a generated second model-enabled scenario through versioned manifests/registries without editing the generic Rivet runner, gateway, scenario orchestration, or generic UI for that model ID.

## Assumptions

- The authoritative local source is the user-owned Data Vault Chatter program: source revision `4eeb36dbfede3c194c43b3d2039abd5860a675f6`; immutable Dataset-2 digest `1d7880d3fd321a86885c825003bfc8c1ba3ccd15cf0e0e7b9c283a48b0d51d5f`; the Data Vault feature-095 CPU recipe with the exact 37-feature order, `GroupShuffleSplit(test_size=0.2, random_state=42)` by `dataset_id`, 96/24 train/validation groups and zero overlap, training-only preprocessing, and Random Forest defaults `500/25/10/5/sqrt/balanced/gini`; and its accepted model-user qualification contracts. The standalone source repository's separate 70/15/15 config-matched split remains comparison evidence, not the Loop 072 package recipe.
- The existing callable Chatter artifact is a scikit-learn/Joblib pipeline and remains outside Wright's trusted package boundary. Loop 072 may retrain the exact reviewed deterministic recipe from the immutable local dataset in an explicit qualification environment, then export a narrow data-only serving representation and compare it with the trusted evaluator; Wright installation never loads Joblib.
- The user described Chatter as "our" model and the source is in a user-owned repository, so the safest reversible default is `LicenseRef-Wright-Internal-Chatter`, local internal use only, no redistribution/export, with an explicit source/owner record required before approval. This does not grant public distribution rights.
- The existing Loop 071 model-library lifecycle and Loop 069/070 gateway, Rivet worker, Run Manifest, scenario harness, deterministic fixture MCPs, and engineering assertion contracts remain authoritative and are extended rather than duplicated.
- Chatter is a screening classifier for the recorded process-planning population. It is not a stability-lobe solver, controller, certification method, calibrated risk model, or substitute for machine-specific testing and qualified manufacturing review.
- One bounded batch call is the preferred first-slice lifecycle because it amortizes cold load without retaining a model process beyond the exact gateway call. Run-scoped warm reuse may be added only if planning proves identity, resource, cancellation, and cleanup benefits without widening authority.
- User-approved integration-branch execution supersedes the default one-branch-per-loop hook; Loop 072 remains a distinct numbered Spec Kit feature identity and commit sequence on `codex/rivet-engineering-program`.

## Out of Scope

- Training-product UI, hyperparameter tuning, feature engineering changes, data collection, relabelling, retraining services, MLflow/cloud execution, or publication of model/data artifacts.
- Dynamic loading of arbitrary scikit-learn, Joblib, pickle, ONNX, Skops, Python, repository, plugin, or remote-code models.
- Continuous stability-lobe generation, interpolation between sampled candidates, online adaptive control, sensor feedback, anomaly monitoring, or production machine validation.
- Generating executable G-code, changing feeds/speeds/controllers, starting a spindle, moving machinery, or any other Gate-E actuation.
- Installing a real CAD/CAM application, CNC controller bridge, proprietary host, paid service, GPU stack, compiler, or global model runtime as part of normal tests or model installation.
- Public redistribution, external catalog publication, license acceptance, or transfer of the Chatter dataset, Joblib artifact, serving payload, or private evaluation rows.
