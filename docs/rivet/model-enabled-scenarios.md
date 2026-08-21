# Model-enabled Rivet scenarios

Rivet can compose MCP application capabilities and local engineering-model capabilities in one reviewed workflow. Both travel through Wright's workspace gateway. Rivet receives a static namespaced tool, a one-run binding, and a short-lived authority; it never receives child commands, server configuration, model runtime endpoints, process handles, credentials, or independent lifecycle control.

## Provider-neutral review

Scenario manifest 1.1 adds a closed provider kind: `mcp` or `engineering_model`. Review evidence retains the distinction instead of representing a model as an MCP server.

An MCP binding records server, revision, tool, validation evidence, and workspace grant. A model binding records package revision/manifest, variant/artifact set, installation, adapter/runtime, mandatory test evidence, schemas, threshold, resource class, and workspace binding. A change to any material identity makes the review stale and requires fresh preflight.

Run Manifest v2 records the provider evidence digest on each reviewed binding and correlated child call. Workflow, provider, input, artifact, assertion, and policy identities are material. Timing, observed resource use, request/trace IDs, timestamps, and host diagnostics are observations and do not change the material reproduction digest.

## Chatter candidate review

The bundled Tier 1 example uses statically bound reviewed nodes for:

1. a deterministic CAD context MCP;
2. a deterministic simulated-CAM candidate MCP;
3. the exact enabled Chatter engineering-model task;
4. a deterministic advisory-report MCP.

The CAM node's structured candidate batch is connected directly to the model node's typed arguments. The system test captures that boundary and compares its digest with the durable model child receipt, so parallel calls or matching fixture labels cannot masquerade as candidate lineage.

Normal gates use the tiny generated Chatter forest. It proves the same contracts and gateway/Rivet path without claiming to be trained from private data. Real local qualification remains opt-in and is reported separately.

Preflight checks the workflow graph, every static node/tool/schema, MCP validation/grants, model package/install/adapter/vector/schema/threshold/resource evidence, policy, fixture identities, and simulation-only/Gate E boundary. Start stays disabled when any item is missing, stale, incompatible, resource-blocked, or untested.

The report correlates candidate producer provenance, model input/result, non-model invariants, rejected reasons, and provider evidence. The only positive label is **selected for human review**. It includes a fixed simulation-only and no-machine-authority notice and never contains executable machine instructions.

## Cancellation and recovery

Cancellation revokes run authority before provider cancellation. Active MCP and model calls receive the bounded cancellation, late success is ignored, resource reservations are released, and owned processes stop. A terminal report says either cleanup is clean or residue may remain with an inspect-before-retry action. Failed/cancelled runs do not publish an advisory selection.

Stable recovery distinguishes policy/review drift, missing capability, model readiness, resource admission, transport, timeout, provider failure, cancellation, and cleanup residue. Restart preserves the last truthful durable state and never recreates old authority.

## Adding another model-enabled scenario

1. Author a versioned 1.1 manifest with at least two independent MCP providers and one `engineering_model` provider.
2. Use only static tool names and static Rivet MCP nodes. Prompt-derived names and child configuration are forbidden.
3. Register bounded artifact normalizers and assertions through the public duplicate-safe registries.
4. Declare exact candidate producer/consumer lineage, units, schemas, resources, environment, cleanup, and physical-actuation prohibition.
5. Add generated, proprietary-free fixtures and a real Rivet/gateway system test.
6. Prove unchanged runs have the same material digest and every provider/package/vector/workflow/fixture/input/policy change appears in comparison.
7. Scan the generic gateway, runner, scenario service, and UI to ensure no model-ID-specific branch was added.

The generated affine extension fixture demonstrates this seam with another model identity and no changes to generic orchestration.
