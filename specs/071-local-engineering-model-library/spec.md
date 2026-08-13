# Feature Specification: Local Engineering Model Library

**Feature Branch**: `codex/rivet-engineering-program` (feature identity: `071-local-engineering-model-library`)

**Created**: 2026-08-13

**Status**: Draft

**Input**: User description: "Let engineers list, inspect, download or import, verify, install, test, enable, update, roll back, and remove safe local engineering models, beginning with Wright's Chatter model foundation and an appropriately licensed external engineering model, without committing weights or silently executing repository code."

## Clarifications

### Session 2026-08-13

- **Q: May Wright acquire gated or private Hugging Face content?** -> **A:** Wright may describe it as blocked and explain the publisher-controlled steps. It never requests access or accepts terms. After a user independently has access, an explicitly stored fine-grained read-only token may be referenced by a fresh plan, but the token never enters model files, runtimes, logs, evidence, or exports. Public ungated acquisition and offline import remain the first supported paths.
- **Q: May installing a model silently install its runtime or hardware dependencies?** -> **A:** No. Runtime adapters and their dependencies have a separate reviewed lifecycle and install plan. A model plan may depend on an already approved runtime or remain blocked with an action to review that runtime; it cannot add packages, drivers, compilers, services, containers, or global settings as an incidental step.
- **Q: What does removal mean when reproducibility references still exist?** -> **A:** Disable and uninstall remove workspace availability and the active installation, while purge removes content bytes. Uninstall may preserve referenced content in the verified cache; purge is blocked until every workspace, workflow, retained run, and export reference is safely detached or archived with an explicit portable package.
- **Q: What evidence makes the first external model genuinely supported?** -> **A:** Model-card metadata alone is insufficient. Gate D must approve exact license evidence, immutable files and digests, data-only format, adapter/runtime, resource envelope, honest limitations, and real deterministic test-vector results against the downloaded artifact. Until then the candidate is evaluation-only, and a safer candidate may replace it without changing the library contracts.
- **Q: How broadly may verified content be shared?** -> **A:** Content may be deduplicated within one Wright-managed user data root while retaining package and workspace references. Private/gated content remains locally access-controlled and is never exported or made visible through another user/workspace merely because its digest matches; public artifacts still require source/license attribution.

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Evaluate a model before changing the machine (Priority: P1)

An engineer opens the local engineering model library, filters by engineering task and hardware, and inspects a model's purpose, provenance, license, artifact size, compatibility, runtime needs, limitations, and evidence before deciding whether it belongs on the machine.

**Why this priority**: Engineers need to understand trust, storage, hardware, and usefulness before Wright downloads bytes or installs a runtime.

**Independent Test**: Load a bundled catalog containing a Wright-owned deterministic test model, an approved public point-cloud model, an incompatible variant, a gated model, and an unreviewed-code model; confirm that the library explains which variants are eligible and why without contacting any source.

**Acceptance Scenarios**:

1. **Given** a supported CPU-only machine, **When** the engineer opens a compatible model, **Then** Wright shows its exact source revision, tasks, inputs and outputs, artifact files and sizes, license and attribution, runtime, expected memory and disk, test evidence, limitations, and install readiness.
2. **Given** a model that needs a GPU, gated access, a license action, a different platform, or repository code, **When** the engineer inspects it, **Then** Wright labels the precise blocker and a safe recovery without presenting it as ready.
3. **Given** no network connection, **When** the engineer browses the library, **Then** bundled catalog metadata and already cached model state remain available and clearly distinguish cached facts from live update information.

---

### User Story 2 - Acquire and install a verified model safely (Priority: P1)

An engineer previews the exact effects, downloads a pinned public model or selects an offline package, verifies every artifact, and activates it atomically. Cancellation, interruption, corruption, or insufficient disk space never creates an apparently ready installation.

**Why this priority**: Safe, reversible acquisition is the core user request and the main supply-chain boundary.

**Independent Test**: Use small local fixtures to exercise fresh download, resume, cache reuse, offline import, checksum failure, truncation, cancellation, disk exhaustion, disallowed file type, path escape, and atomic activation without network, credentials, large assets, or model execution.

**Acceptance Scenarios**:

1. **Given** an eligible model variant, **When** the engineer reviews and confirms its install plan, **Then** Wright resolves an immutable source revision, shows exact maximum bytes and storage effects, stages only declared files, verifies them, and activates one exact installation.
2. **Given** the required artifact already exists in the verified cache, **When** another model package references the same content, **Then** Wright reuses it without downloading or duplicating the bytes and records both references.
3. **Given** an interrupted or cancelled transfer, **When** the operation stops, **Then** the model remains unavailable, resumable staging is distinguished from verified content, and retry or cleanup guidance is shown.
4. **Given** an offline package, **When** the engineer imports it, **Then** Wright applies the same manifest, license, compatibility, path, size, format, checksum, and test-vector checks as an online acquisition.

---

### User Story 3 - Prove a model is ready and use a typed capability (Priority: P1)

An engineer runs the package's standard test vector, sees runtime health and resource use, and enables a typed model capability for a workspace only after the exact model and runtime identities pass verification.

**Why this priority**: Installed bytes are not useful or trustworthy until a bounded runtime proves the declared contract and can be mediated like other workspace capabilities.

**Independent Test**: Install a tiny deterministic Wright-owned model fixture, run positive and negative typed test vectors through an isolated fake runtime, enable it for one workspace, and prove another workspace and an unreviewed workflow cannot call it.

**Acceptance Scenarios**:

1. **Given** a verified installation and compatible resources, **When** the engineer runs its standard test, **Then** Wright loads it through its approved runtime, validates typed input and bounded output, records exact identities and timing, unloads it, and reports pass or a precise failure.
2. **Given** a model that is corrupt, incompatible, missing a runtime, out of memory, or returns malformed/non-finite output, **When** the test runs, **Then** activation or enablement fails closed with actionable recovery and no reusable authority in the evidence.
3. **Given** a healthy enabled model, **When** a reviewed workspace client discovers it, **Then** it receives a typed namespaced capability through Wright's existing workspace gateway rather than a direct runtime connection.
4. **Given** cancellation during load or inference, **When** the cancellation deadline expires, **Then** later output cannot be published as success and cleanup or residue is reported truthfully.

---

### User Story 4 - Update, roll back, remove, and move models predictably (Priority: P2)

An engineer can compare an available revision, preserve the current working model until the replacement passes, roll back, export an offline package, and remove unused content without breaking workspaces or approved workflows.

**Why this priority**: Model libraries become unsafe and expensive when upgrades silently drift or removal loses reproducibility.

**Independent Test**: Upgrade between two tiny fixture revisions, inject verification and self-test failures, roll back, export and re-import offline, and exercise removal with zero, one, and multiple durable references.

**Acceptance Scenarios**:

1. **Given** an installed model and a newer approved revision, **When** the engineer previews an update, **Then** Wright shows material manifest, license, artifact, runtime, resource, schema, limitation, and test-vector changes before confirmation.
2. **Given** a replacement that fails verification or its standard test, **When** the update finishes, **Then** the prior healthy revision remains active and the failed candidate is recoverable or removable.
3. **Given** an installed revision referenced by a workspace, reviewed workflow, or preserved run, **When** removal is requested, **Then** Wright blocks deletion of required content or explains the exact references and safe detach/archive choices.
4. **Given** a verified installation, **When** the engineer exports it for another offline machine, **Then** the package contains bounded manifest, artifacts, checksums, license/attribution, runtime requirements, and test vectors but no tokens, host paths, mutable authority, or private catalog data.

---

### User Story 5 - Extend the library without weakening trust (Priority: P2)

A maintainer can add another model, variant, or runtime adapter through public versioned contracts and deterministic conformance tests rather than model-specific application code.

**Why this priority**: The library must grow across 3D, mesh, surrogate, quality, and manufacturing models without turning every addition into a bespoke security path.

**Independent Test**: Register a test-only model and adapter, validate its package and test vectors, then reject duplicate identities, unsupported versions, undeclared files, unsafe formats, unknown licenses, executable repository content, and incompatible output schemas.

**Acceptance Scenarios**:

1. **Given** a complete package and an approved adapter contract, **When** a maintainer validates it, **Then** it can traverse the normal catalog, install, verify, self-test, enable, and removal lifecycle without changing the library service.
2. **Given** an unsafe or incomplete package, **When** validation runs, **Then** the exact field, artifact, policy, or compatibility problem is reported before any download or runtime start.

### Edge Cases

- A mutable branch or tag resolves to a different commit between preview and download.
- A source omits file sizes, checksums, license evidence, or immutable revision metadata.
- A source is public during preview but becomes gated, private, deleted, or disabled before acquisition.
- A redirect changes host or downgrades transport, or a response exceeds declared size.
- A partial file has the expected name and length but the wrong content digest.
- A package contains symlinks, hard links, absolute paths, traversal, duplicate normalized names, executable bits, archives within archives, or files not declared by the manifest.
- A package declares pickle, joblib, Python source, native libraries, shell commands, macros, plugins, or remote code as model data.
- The model's license changes between revisions or requires acceptance outside Wright.
- The cache contains corrupt content or content written by a prior crashed process.
- Two operations target the same model or content digest concurrently.
- Available disk, RAM, GPU memory, architecture, driver, or runtime changes after preflight.
- The runtime crashes, hangs, ignores cancellation, emits too much output, returns NaN/infinity, or changes schema.
- An update changes task meaning, units, coordinate conventions, label order, confidence semantics, or limitations without changing a display name.
- A referenced revision is removed while another revision of the same model remains installed.
- Offline import is valid but the required runtime is absent or incompatible.
- An engineer clears a token or cache while an operation is running.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: Wright MUST provide a distinct local engineering model library separate from conversational/tool-use model-provider setup.
- **FR-002**: Engineers MUST be able to list, filter, sort, and inspect model packages and variants by engineering task, source, maturity, license state, install state, platform, architecture, accelerator need, runtime, artifact size, and evidence state.
- **FR-003**: Every model package MUST declare a stable model and package identity, schema version, publisher, source kind and URI, immutable source revision, task taxonomy, variants, input/output contracts, units and coordinate conventions where applicable, artifacts, checksums, sizes, license, attribution, redistribution policy, runtime adapter, resource envelope, test vectors, limitations, and remote-code policy.
- **FR-004**: Model variants MUST have independent artifact, runtime, precision, platform, resource, and test evidence and MUST NOT inherit compatibility merely from another variant.
- **FR-005**: Catalog entries MUST distinguish approved, needs-review, gated/external-action, incompatible, deprecated, withdrawn, and blocked states; only approved compatible variants may be installed.
- **FR-006**: The first catalog MUST include a tiny Wright-owned deterministic test model and at least one specifically reviewed public external engineering model at a full immutable revision.
- **FR-007**: Wright MUST show whether source, license, artifact, runtime, compatibility, security, and test evidence is bundled, cached, live, stale, partial, or absent.
- **FR-008**: Compatibility preflight MUST fail closed for unsupported operating system, architecture, runtime version, instruction set, CPU/RAM/disk, GPU/VRAM/driver, unavailable accelerator, unavailable runtime, or incompatible input/output contract.
- **FR-009**: Before acquisition, Wright MUST show an expiring install plan containing exact source revision, declared files and maximum bytes, cache/install locations in safe user-oriented terms, network/token/license requirements, runtime effects, compatibility, prompts, references, rollback, and cleanup.
- **FR-010**: A mutable source reference MUST be resolved to an immutable revision before confirmation, and any revision or manifest change MUST invalidate the plan.
- **FR-011**: Download and import MUST accept only package-declared files from approved sources and MUST enforce secure transport, redirect policy, normalized relative paths, file/count/size ceilings, and declared content digests.
- **FR-012**: Downloads MUST stage outside the ready installation, support bounded progress and cancellation, and distinguish resumable partial content from verified cache content.
- **FR-013**: Failed, interrupted, cancelled, oversized, corrupt, or incomplete acquisition MUST NOT create an installed, enabled, or loadable model.
- **FR-014**: Verified artifacts MUST use content-addressed storage so identical bytes are reused across packages while reference ownership remains exact.
- **FR-015**: Cache and installation activation MUST be atomic, concurrency-safe, idempotent, recoverable after restart, and resistant to time-of-check/time-of-use replacement.
- **FR-016**: Online download and offline import MUST apply the same package, license, compatibility, artifact, format, checksum, and test-vector policy.
- **FR-017**: Model data formats MUST be explicitly allowlisted and treated as untrusted; package validation MUST reject executable code, scripts, macros, plugins, native libraries, unsafe deserialization formats, symlinks, traversal, undeclared files, and nested unbounded archives.
- **FR-018**: Repository code execution and implicit remote code MUST remain disabled; a package requiring remote code MUST be blocked rather than activated by a hidden or generic trust switch.
- **FR-019**: External license acceptance, gated access, subscriptions, or sharing of personal information MUST occur independently and explicitly; Wright MUST NOT silently accept terms, request access, disclose user data, or store a source token in model metadata, logs, evidence, or exports.
- **FR-020**: Tokens, when explicitly needed, MUST be stored only through the existing secret boundary, requested with minimum read scope, never passed to runtimes, and removable without altering verified public artifacts.
- **FR-021**: Wright MUST perform disk admission before acquisition and resource admission before load and inference, including concurrent reservation and a safe CPU fallback only when the package declares one.
- **FR-022**: A versioned runtime adapter contract MUST support compatibility and health probes, verify, load, unload, typed inference, progress, timeout, cancellation, resource reporting, deterministic test-vector execution, exact identity, and bounded redacted diagnostics.
- **FR-023**: A runtime adapter MUST be independently reviewed and installed; downloading model artifacts MUST NOT silently install packages, drivers, compilers, system services, or global dependencies.
- **FR-024**: A model MUST remain unready until its artifacts verify, its adapter is compatible and healthy, and every mandatory standard test vector passes against the exact model/runtime pair.
- **FR-025**: Test vectors MUST declare typed inputs, units/coordinates where material, expected output schema, numerical tolerances or membership rules, deterministic seed, resource/time ceilings, and the model limitations they exercise.
- **FR-026**: Inference MUST validate typed bounded inputs and outputs and reject undeclared dimensions, incompatible units, unsupported coordinates, invalid labels, NaN/infinity, oversized payloads, unsafe paths/URIs, and secret-like values.
- **FR-027**: Model capabilities MUST be exposed to workspaces through the existing Wright gateway with namespaced typed schemas, workspace enablement, policy, review, short-lived run authority, progress, cancellation, audit, and evidence; clients MUST NOT connect directly to runtimes.
- **FR-028**: Capability discovery and inference evidence MUST identify exact package, source revision, variant, artifact-set digest, adapter/runtime version, schema digest, resource class, test evidence, and workspace binding without exposing host paths or authority.
- **FR-029**: Enabling a model MUST be per workspace and MUST NOT broaden another workspace, existing MCP, conversational provider, or ordinary workflow authority.
- **FR-030**: Cancellation MUST stop or bound active load/inference through the gateway path, prevent late output from publishing success, release reservations, and record truthful cleanup or residue.
- **FR-031**: Every failure MUST have a stable category and reason code covering catalog, source, license, authentication, compatibility, admission, download, import, integrity, format, runtime, test, inference, cancellation, reference, cleanup, and internal failures, with actionable recovery.
- **FR-032**: Update preview MUST compare every material catalog, manifest, license, artifact, adapter, runtime, hardware, schema, task/units, limitation, and test-vector change and MUST preserve the current healthy revision until the candidate passes.
- **FR-033**: Rollback MUST restore a previously verified compatible revision without redownload when its referenced content remains available and MUST re-run compatibility and mandatory tests before activation.
- **FR-034**: Removal MUST be reference-aware across workspaces, reviewed workflows, retained runs, exports, and shared content; Wright MUST block destructive removal or explain exact detach/archive consequences before deleting required bytes.
- **FR-035**: Unreferenced cache cleanup MUST preview exact reclaimable bytes, preserve verified content needed by installed packages or reproducibility records, and be cancellable and recoverable.
- **FR-036**: Offline export MUST include the exact package manifest, allowed artifacts, checksums, license and attribution, runtime requirements, and test vectors, and MUST exclude secrets, mutable authority, raw host paths, private catalog data, and undeclared files.
- **FR-037**: Durable lifecycle state and evidence MUST survive restart and preserve exact plan, operation, package, artifact, runtime, test, reference, cancellation, cleanup, and rollback identities within bounded records.
- **FR-038**: The UI MUST separate engineering models from conversational-provider setup and explain value, task, compatibility, storage, hardware, license, safety, limitations, state, progress, evidence, references, and recovery in engineering-oriented plain language.
- **FR-039**: The initial external candidate MUST be pinned, public, ungated, permissively licensed, bounded in size, useful for a typed engineering task, loadable without repository code, and documented with honest limitations; a candidate failing any condition MUST remain evaluation-only or blocked.
- **FR-040**: Normal tests MUST use tiny deterministic generated fixtures and MUST NOT require network, credentials, gated terms, paid services, proprietary apps, GPUs, hardware, large downloads, or committed model weights.
- **FR-041**: Optional live source validation MUST be explicitly selected, download only reviewed allowlisted artifacts into Wright-controlled storage, record exact source/digest/runtime evidence, and leave downloads, weights, caches, and runtime environments untracked.
- **FR-042**: No model capability, test vector, or example may start or command physical machinery, motion, heat, a spindle, extrusion, a printer, a robot, or a PLC.
- **FR-043**: Public package and adapter registries MUST reject duplicate identities, unsupported contract versions, ambiguous task schemas, conflicting file ownership, or unapproved adapter/version combinations before acquisition.

### Non-Functional Requirements

- **NFR-001**: Listing 1,000 cached model variants and filtering them by task and compatibility MUST complete in under 500 milliseconds at the 95th percentile on a reference development machine, excluding live source refresh.
- **NFR-002**: Install-plan creation and local manifest validation for a 100-file package MUST each complete in under one second at the 95th percentile, excluding hashing and network transfer.
- **NFR-003**: Every catalog, plan, progress, evidence, diagnostic, preview, and test-vector field MUST have explicit count and size ceilings; model payload bytes are never embedded in general API or log records.
- **NFR-004**: Identical verified content and material package/runtime identities MUST yield identical test-vector outcomes and evidence digests across supported CPU platforms, within declared numerical tolerances.
- **NFR-005**: Cancellation MUST reach a deterministic test runtime within one second, and cleanup MUST finish within five seconds or report explicit bounded residue.
- **NFR-006**: Library, detail, plan, progress, verification, test, reference, update, rollback, and removal journeys MUST be keyboard operable, usable at 320 CSS pixels and 200% zoom, convey status with text as well as color, manage focus, and produce no serious or critical automated accessibility findings.
- **NFR-007**: An unclean shutdown at any state transition MUST recover to the last durable truthful state without presenting partial bytes as verified or an untested model as ready.
- **NFR-008**: The feature MUST remain fully useful for installed and offline-imported models when air-gapped; loss of the external catalog cannot disable local inspection, verification, testing, enablement, inference, rollback, or removal.

### Key Entities

- **Model Catalog Snapshot**: Immutable bounded metadata and trust evidence for model packages and variants from a bundled or approved source.
- **Model Package**: Versioned declaration of one model revision's task, contracts, variants, artifacts, license, runtime, resources, tests, limitations, and remote-code policy.
- **Model Variant**: A concrete precision/format/platform/resource choice with its own files and compatibility.
- **Model Artifact**: One declared content-addressed data file with source identity, size, digest, format, verification state, and references.
- **Model Install Plan**: Expiring preview of exact sources, bytes, effects, blockers, confirmation state, rollback, and cleanup.
- **Model Operation**: Durable state machine for download, import, verify, install, test, enable, update, rollback, export, cleanup, or removal.
- **Model Installation**: Local package/variant state linking verified artifacts, runtime, health, test evidence, active revision, predecessors, and references.
- **Runtime Adapter**: Approved provider-neutral contract implementation for health, resource admission, model lifecycle, typed inference, and cancellation.
- **Model Test Vector**: Versioned deterministic input, expected typed outcome/tolerance, limits, and result evidence.
- **Model Capability Binding**: Workspace-scoped reviewed mapping from a typed model task to one exact installation and runtime identity.
- **Model Reference**: Durable reason an installation or artifact must be preserved, such as a workspace, workflow, run, or offline export.
- **Model Validation Evidence**: Immutable bounded record of catalog, compatibility, integrity, runtime, test, security, cleanup, and limitation results.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: An engineer can determine whether a model is useful, licensed, compatible, safe, and within storage/resource limits in under two minutes without starting a download.
- **SC-002**: One Wright-owned deterministic model and one approved external engineering model traverse catalog, plan, acquire/import, verify, install, mandatory test, enable, offline use, disable, rollback or removal with exact evidence.
- **SC-003**: In deterministic negative tests, 100% of corrupt, truncated, oversized, path-escaping, undeclared, unsafe-format, remote-code, license, gating, compatibility, resource, runtime, schema, cancellation, and reference failures block readiness and report the correct stable category.
- **SC-004**: Repeating installation from the same verified cache transfers zero model bytes and creates no duplicate content while preserving package-specific references.
- **SC-005**: An interrupted operation followed by restart never exposes partial content as verified, installed, enabled, or loadable in 100% of state-transition fault tests.
- **SC-006**: A standard typed test vector for an installed model operates offline and records identical material evidence and outcomes across repeated supported CPU runs within declared tolerances.
- **SC-007**: A reviewed workspace can discover and call an enabled model through Wright, while cross-workspace, stale-binding, unreviewed, disabled, and direct-runtime attempts fail in 100% of deterministic authorization tests.
- **SC-008**: Update failure preserves the previous healthy revision in 100% of verification, test, resource, and cancellation fault injections; rollback uses cached content when available.
- **SC-009**: Removal and cache cleanup never delete bytes referenced by an installed package, enabled workspace, reviewed workflow, or retained reproducibility record in deterministic reference tests.
- **SC-010**: Normal gates complete with no network, credentials, gated terms, paid services, proprietary apps, GPUs, physical hardware, large downloads, global dependency mutation, committed weights, or physical actuation.
- **SC-011**: Automated accessibility checks report no serious or critical findings across the model library, detail, plan, progress, test, update, rollback, and removal journeys.
- **SC-012**: A maintainer can add a deterministic model package and compatible test adapter using documented public contracts without editing the lifecycle service, and invalid additions fail before acquisition.

## Assumptions

- Loop 071 establishes the provider-neutral model library and deterministic runtime contract; Loop 072 supplies the production Chatter package and Chatter-aware Rivet scenario.
- The current public `keras-io/PointNet` repository is a provisional external-candidate baseline because it is public, ungated, small, Apache-2.0-tagged, pinned at an immutable revision, and describes a ModelNet10 point-cloud classification task. Gate D must still approve its license evidence, legacy runtime cost, artifact format, test vectors, and limitations before Wright labels it installable. If it cannot pass safely, Loop 071 must select and validate another public, ungated, permissively licensed, bounded, data-only engineering model rather than treating the deterministic Wright fixture as satisfying the external-model requirement.
- Models whose public metadata requires repository code, pickle-style deserialization, gated access, unknown terms, or unbounded runtime dependencies remain evaluation-only or blocked even when technically downloadable.
- Model payloads live in a Wright-managed user data root outside the source tree. Git tracks only manifests, schemas, small generated non-weight fixtures, and bounded evidence.
- Existing local authentication, secret storage, workspace enablement, gateway policy/review/run authority, content-addressed storage conventions, and durable embedded state remain authoritative boundaries.
- User-approved integration-branch execution supersedes the default one-branch-per-loop hook; Loop 071 remains a distinct numbered Spec Kit feature identity and commit sequence on `codex/rivet-engineering-program`.

## Out of Scope

- Training, fine-tuning, quantization, conversion, benchmarking leaderboards, or publishing models.
- General conversational LLM provider configuration or replacement of Hermes/Codex model selection.
- Silent installation of GPU drivers, CUDA, compilers, system packages, containers, or model-specific global environments.
- Automatic license acceptance, gated-repository access requests, subscription purchase, or disclosure of personal information.
- Executing arbitrary repository code or providing a generic `trust_remote_code` escape hatch.
- Committing or redistributing third-party model weights in the Wright repository or application wheel.
- Cloud inference, paid hosted endpoints, distributed training, or multi-node serving.
- Physical machine, printer, spindle, robot, PLC, motion, heat, or extrusion control.
