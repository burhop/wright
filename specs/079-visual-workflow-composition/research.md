# Research: Visual Workflow Composition Foundation

## Decision 1: Use a distinct provisional draft contract

**Decision**: Introduce `workflow-draft` schema `1.0.0-draft.1`; do not make the immutable EPP-F02 process-definition contract editable.

**Rationale**: EPP-F02 intentionally fixes a released identity and GET-only boundary. Authoring needs explicit connections, versioned revisions, candidate validation, and layout without changing that contract or implying release authority.

**Alternatives considered**: Extend EPP-F02 JSON (rejected: breaks its approved boundary); reuse Rivet projects/types (rejected: preserves the dependency being replaced); adopt prototype JSON (rejected: provisional evidence only).

## Decision 2: Separate semantics from layout and ephemeral UI state

**Decision**: Persist a semantic document and integer-grid layout in one revision envelope, but compute their digests separately. Selection, viewport, open panels, drag previews, and invalid form input remain ephemeral.

**Rationale**: Stable IDs and relationships survive movement or renderer replacement, while save/reopen still restores intentional positions.

**Alternatives considered**: Renderer-native serialization (rejected: lock-in); position-derived identity (rejected: unstable); no layout persistence (rejected: fails the customer journey).

## Decision 3: Validate complete candidate edits before accepting them

**Decision**: Reduce an intent against an immutable copy, validate the complete candidate, then accept all or reject all. Explicit Save revalidates on the server and uses compare-and-set revision identity.

**Rationale**: This preserves the last valid in-memory and saved states and makes diagnostics deterministic. “Apply” means no release or execution action in this slice and is not used as the primary user label.

**Alternatives considered**: Persist invalid intermediate graphs (rejected: recovery and compatibility risk); browser-only validation (rejected: bypassable); raw JSON editor (deferred under `DEC-P0-002`).

## Decision 4: Use a feature-owned SQLite sidecar

**Decision**: Lazily create `workflow-drafts.sqlite3` under `DATABASE_PATH.parent`; store append-only validated revisions and a current pointer in a single local transaction.

**Rationale**: SQLite satisfies the constitution's embedded relational-state rule. A separate database avoids advancing the main migration ledger, so a rollback to the prior Wright binary ignores the inert sidecar instead of rejecting a newer main schema.

**Alternatives considered**: Main database migration (rejected for bounded rollback); browser IndexedDB (rejected: weakens system authority and violates the state rule); JSON files (rejected: not relational state); server database (prohibited).

## Decision 5: Ship a small replaceable SVG/HTML renderer adapter

**Decision**: Define one projection-and-intent interface and inject one first-party renderer. Use existing React/CSS/SVG primitives and no new production dependency.

**Rationale**: Four-block authoring does not justify a renderer/plugin framework or React Flow lock-in. A fake renderer can prove replacement without changing semantics, validation, persistence, or text.

**Alternatives considered**: React Flow (useful prototype evidence but not approved architecture); canvas library bakeoff (deferred until scale evidence warrants it); generic plugin registry (rejected overhead).

## Decision 6: Keep authoring default-off at both API and browser boundaries

**Decision**: Require `WRIGHT_WORKFLOW_COMPOSER_ENABLED=1` for draft API/service composition and `VITE_WRIGHT_WORKFLOW_COMPOSER=1` for navigation/route exposure.

**Rationale**: Browser hiding alone leaves mutation authority exposed. Independent flags provide honest removal and rollback tests.

**Alternatives considered**: Frontend flag only (rejected); modifying the EPP-F02 flag (rejected: couples unrelated boundaries).

## Decision 7: Use Windows writer and GB10 exact-candidate verifier

**Decision**: Windows owns source and UI evidence. GB10 fetches a committed candidate into an isolated worktree and performs Linux/aarch64 backend, build, Docker, packaging, and independent verification.

**Rationale**: This uses each host's strengths without duplicate work or concurrent writes and produces independent exact-subject evidence.

**Alternatives considered**: Shared worktree (prohibited); duplicated full suites (wasteful); GB10 commits (weakens writer/verifier separation).

## Unresolved by design

- `DEC-P0-002` remains open for permanent editable syntax, human/LLM editing studies, migration policy, and release/Apply semantics.
- Renderer choice beyond this bounded adapter remains provisional.
- Multi-user collaboration, draft-to-released promotion, execution, and large-canvas usability remain future decisions.
