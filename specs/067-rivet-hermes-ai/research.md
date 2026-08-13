# Research: Rivet Hermes AI and MCP Execution

## Decision 1: Use Hermes's existing agent API with a Wright compatibility translator

**Decision**: Rivet points to a Wright-local OpenAI-compatible endpoint. Wright forwards ordinary content through Hermes and translates Rivet's sequential tool-call contract into a strict structured Hermes request/response when tools are present.

**Evidence**:

- Rivet 2 already supports a custom OpenAI-compatible provider and stores its selection under the `ai` hybrid-storage group.
- Rivet's legacy Graph Builder calls `runChatV2Pipeline` with functions and consumes `function-calls`; it intentionally limits the legacy loop to one tool call per turn.
- The installed Hermes 0.20 API server accepts `tools`/`tool_choice` as request fields for idempotency fingerprinting, but `_handle_chat_completions` sends only the flattened conversation/system prompt into `_run_agent` and emits content/tool-progress events, not client-requested OpenAI tool-call deltas.

**Alternatives rejected**:

- Direct OpenAI API: the user has no API key and explicitly requires Codex subscription access through Hermes.
- Direct Codex OAuth client in Wright: creates the second agent path the user rejected and makes Wright own provider credentials.
- Patch Hermes API server: violates the no-Hermes-change requirement and creates an ongoing fork burden.
- Blind pass-through to Hermes `/v1/chat/completions`: plain text could work, but Rivet Graph Builder would not receive its required function calls.

## Decision 2: Do not depend on Hermes's subscription proxy command

**Decision**: Do not start or modify `hermes proxy` for this feature.

**Evidence**: The installed proxy is a minimal, fast, credential-attaching forwarder and would be ideal for latency, but its adapter registry currently contains Nous Portal and xAI only. It does not expose the installed Codex subscription. Adding a Codex adapter would be a Hermes change.

**Consequence**: The bridge uses Hermes's full agent loop and cannot equal a raw provider proxy's latency. The plan minimizes Wright overhead, streams progress immediately, records upstream versus local latency, and avoids claiming direct-API speed.

## Decision 3: Preconfigure Rivet through its host storage contract

**Decision**: Seed the host-provided in-memory hybrid storage before mounting `RivetAppHost`, selecting provider `custom`, model `wright-hermes`, and the same-origin Wright bridge URL.

**Rationale**: This uses Rivet 2's supported host/storage seams and avoids a broad upstream patch. The embedded canvas stays visually minimal while the sparkle action receives a complete provider configuration.

**Alternative rejected**: Showing Rivet's full Settings UI would expose irrelevant controls and invite unsupported provider/key configuration, contrary to the requested Wright canvas experience.

## Decision 4: Bundle the real Rivet Node runtime from the same pin

**Decision**: Build a checked-in single-file worker from `@valerypopoff/rivet2-node` at revision `4f4a165a03f8da89c3d1cce2cb1a8c6eb6aa2053`, inventory it in a manifest, and ship it in the wheel.

**Rationale**: The existing fixture proves lifecycle only and cannot run nodes. Runtime npm installs would violate air-gapped/native distribution requirements. Using the same pin as the editor prevents project-format drift.

**Alternatives rejected**:

- Invoke upstream CLI from the ignored source checkout: installed Wright packages cannot require a source checkout.
- Download the npm package at first run: violates offline-first and reproducibility.
- Reimplement the Rivet graph engine in Python: high divergence and incomplete node semantics.

## Decision 5: Put long-lived Hermes credentials only in the Python trust boundary

**Decision**: The editor and Node worker receive random, short-lived tokens for local compatibility endpoints. Only the Python adapter resolves the Hermes API key.

**Rationale**: The trusted runtime needs the key to call Hermes, but browser JavaScript and graph/code nodes must not receive it. Ephemeral tokens are scoped to Chat Completions, bounded in lifetime, and useless after host/run shutdown.

## Decision 6: Register an internal Wright-managed MCP separately from the public catalog

**Decision**: Add a dedicated reconciler for the built-in Rivet MCP. Seed it installed/active on first creation, preserve later user disablement, and publish it through the existing Wright gateway.

**Rationale**: The engineering catalog is for independently installable external MCPs and has a clean-container validation process. This server is part of Wright itself and ships in the same wheel.

**Alternative rejected**: Add it to `engineering-catalog.yaml`. Catalog reconciliation seeds entries as not installed and would misrepresent a built-in product service as an external package.

## Decision 7: Inject binding authority, never accept it from MCP tool arguments

**Decision**: The Wright-managed launch path supplies canonical workspace path, workspace ID, session ID, and database path through trusted process environment created from the gateway binding. Tool schemas accept only workflow slugs, template IDs, graph names, revision/digest, and bounded inputs.

**Rationale**: The current lifecycle already sets the child cwd to the authenticated workspace. Extending the Wright-managed binding with identities needed for review/audit keeps model-authored arguments from selecting another workspace.

## Decision 8: Share validation and execution across canvas and MCP

**Decision**: Extract reusable validation and execution services under `workspace_service`; both API operations and the MCP call them. Persist bounded run projections/events in SQLite, while keeping project content in workspace files.

**Rationale**: Separate canvas and MCP runners would drift on revision checks, review requirements, capability policy, cancellation, and output shaping.

## Decision 9: Test AI with deterministic doubles plus two opt-in live canaries

**Decision**: Mandatory tests emulate Hermes and provider streaming/tool calls locally. Live subscription use requires the `rivet_live_ai` marker and `WRIGHT_RIVET_LIVE_AI=1` and performs only the two specified smoke interactions.

**Rationale**: Routine tests must be fast, reliable, offline, and non-consuming, while a compatibility layer still needs evidence against the real installed Hermes/Codex behavior.
