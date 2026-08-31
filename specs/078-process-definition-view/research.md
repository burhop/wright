# Research: EPP-F02 Canonical Process View

## Read-only interchange and deferred authoring boundary

**Bounded decision proposed in ADR 0021**: EPP-F02 may use versioned semantic JSON with stable IDs only as one immutable bundled read-only interchange contract. Text and diagram are projections. Editable syntax, round-trip behavior, persistence, migration, and Apply remain open under `DEC-P0-002` and blocked for EPP-F06.

**Rationale**: Wright already ships JSON-schema validation and deterministic identity. One source prevents projection drift and supports later API, CLI, and LLM adapters.

**Alternatives considered**: Waiting for the full authoring study delays customer learning; declaring JSON permanent authoring syntax lacks evidence; YAML or a DSL adds premature ambiguity/tooling. The bounded read-only choice creates no persisted user data and can be removed.

**Approval**: Exact human material-change and implementation approval must accept ADR 0021 before local T001–T019. That approval does not close the EPP-F06 authoring decision.

## Rendering

**Decision**: Complete semantic HTML plus a lightweight derived SVG/HTML diagram using existing browser capabilities.

**Rationale**: The diagram is small, read-only, replaceable, and secondary to text. A new renderer expands licensing, packaging, and security scope.

**Alternatives considered**: Rivet imports editing/runtime semantics; a diagram library adds a dependency; image-only output is not accessible or inspectable.

## Validation boundary

**Decision**: Bounded reading, strict JSON, schema, digest, and cross-reference validation live in `tool_registry`; FastAPI routing stays declarative and browser validation is defensive only.

**Rationale**: Invalid content never reaches presentation, and native packaging shares one authority.

**Alternatives considered**: Browser-only validation duplicates authority; route-layer validation violates architecture; persistence is unnecessary.

## Sample

**Decision**: Bundle one product-definition process explaining EPP-US-001 through EPP-US-005.

**Rationale**: It is customer-relevant and demonstrates phases, gates, feedback, and artifacts without falsely claiming execution or qualification.

## Delivery efficiency

**Decision**: Focused deterministic checks during implementation, one full candidate gate, normally one push, and at most one consolidated CI correction. Scheduler-sensitive timing remains non-blocking observation.

**Rationale**: Repeated exact-identity and timing reruns consumed more time than customer capability; functional/security/compatibility gates remain blocking while duplicates are removed.

## Host allocation

**Decision**: Benchmark Windows and GB10 before routing work; move only repeatably faster/capacity-limited workloads with separate worktrees and digest manifests.

**Rationale**: Evidence-based routing uses Linux capacity without weakening Windows UI/native authority or provenance.
