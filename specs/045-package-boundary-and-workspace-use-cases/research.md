# Research: Package Boundaries and Workspace Use Cases

## Decision 1: One machine-readable boundary policy

**Decision**: Store owned source roots, allowed direct dependencies, forbidden modules/behaviors, and temporary exceptions in one reviewed repository manifest. Validate both source imports and package metadata against it.

**Rationale**: The existing test detects only imports of API code from packages and cannot catch reverse internal edges, local imports, dynamic imports, or metadata drift. A single policy makes exceptions visible and allows seeded negative tests.

**Alternatives considered**: Hard-coded test dictionaries (less discoverable and duplicates documentation); external architecture framework (unnecessary dependency and weaker dynamic-import control); relying on dependency metadata alone (misses undeclared/dynamic imports).

## Decision 2: AST analysis plus explicit dynamic-import recognition

**Decision**: Parse every production Python source file and recognize `import`, `from`, relative imports, aliases, `importlib.import_module`, and `__import__` when targets are statically knowable. Treat non-literal dynamic package targets in owned source as violations unless explicitly exempted.

**Rationale**: This closes the exact `core` reverse-import escape identified by the roadmap and produces deterministic, offline checks on Windows and Linux.

**Alternatives considered**: Text search (false positives/negatives); runtime import tracing (coverage-dependent); banning all local imports (unnecessarily restrictive and still misses dynamic loading).

## Decision 3: Ports live at the lowest owner that defines their vocabulary

**Decision**: Put universal domain values/errors and side-effect-neutral contracts in `core`; put workspace workflow capability ports in `workspace_service`; put concrete persistence in `data_vault`, agent implementations in `agent_adapters`, and registry implementations in `tool_registry`.

**Rationale**: A port belongs to the consumer that needs the capability, while adapters depend inward on that vocabulary. This avoids moving concrete behavior into `core` under a different name.

**Alternatives considered**: All ports in `core` (creates a dumping ground); adapters defining interfaces (dependency inversion is reversed); an additional shared package (expands topology without need).

## Decision 4: One facade, decomposed use cases

**Decision**: Preserve `WorkspaceService` as the stable application facade but make each public operation delegate to a focused lifecycle, file, Git, context, or tool use case constructed from shared ports.

**Rationale**: API callers retain a stable seam while direct tests gain small units. It avoids a big-bang second graph and allows safe extraction by vertical slice.

**Alternatives considered**: Replace all callers with dozens of injected classes at once (high composition churn); keep a monolithic service with methods (does not solve ownership/testability); event-sourced rewrite (out of scope and requires migration).

## Decision 5: Bounded async execution at the application boundary

**Decision**: Use an injected blocking-work executor with explicit operation deadlines and cancellation propagation. Production uses bounded worker capacity; direct tests use inline/recording executors.

**Rationale**: Existing async routes call synchronous filesystem, Git, subprocess, and SQLite work directly. Central bounding protects responsiveness and makes timeout semantics testable.

**Alternatives considered**: Route-level `to_thread` calls (duplicates policy and leaves use cases unsafe); making every adapter async (needless wrapper complexity for local primitives); unbounded default executor (does not satisfy lifecycle or load safety).

## Decision 6: Data-vault repositories return application-neutral records

**Decision**: Move workspace/session/context/settings SQL from `core` into typed data-vault repositories. Return immutable records or mappings without importing workspace use cases.

**Rationale**: `data_vault` owns SQLite; `workspace_service` owns orchestration. This keeps the graph one-way while preserving the Feature 044 schema.

**Alternatives considered**: Keep SQL compatibility functions in `core` (violates target); let use cases execute SQL (moves violation upward); introduce an ORM (large dependency and migration risk).

## Decision 7: Notification after mutation is observable best effort

**Decision**: Publish tool/workspace refresh through an injected notification port after the durable mutation succeeds. A notification failure is logged/recorded but does not roll back the completed state or Git operation.

**Rationale**: Existing behavior already treats notification as best effort. Making the rule explicit preserves compatibility and removes route-to-route imports.

**Alternatives considered**: Transactional outbox (schema and lifecycle expansion); rollback a completed filesystem/Git operation (often impossible); silent failure (not operable).

## Decision 8: Compatibility is contract-driven, not implementation preservation

**Decision**: Preserve HTTP shapes, error categories, state/file formats, and externally visible effects. Remove implementation entry points after static and dynamic call-graph evidence shows no supported caller; retain only delegating shims with removal conditions.

**Rationale**: Keeping unsafe/reverse dependencies merely because tests import them would defeat the feature. Contract tests distinguish real compatibility from accidental internals.

**Alternatives considered**: Keep all legacy functions indefinitely (two graphs); break all internal imports at once (unnecessary downstream risk); duplicate old logic behind adapters (divergent behavior).
