# Contract: Compatibility Fixture and Evidence

**Owner slice**: `055-rivet-compatibility-spike`

## Fixture Constraints

The fixture is a small synthetic Rivet project plus mock host harness. It MUST:

- contain no user workspace content, real credentials, live engineering tool call, or network-dependent model invocation;
- exercise project load/save tracing, one dataset operation, one Node executor run, one mock external call, one cancellation attempt, and one remote-debugger connection attempt;
- use two distinct synthetic workspace identities for every provider-isolation probe;
- record expected versus observed behavior in structured redacted output;
- reside exclusively under `integrations/rivet/spike/` after plan approval;
- remain excluded from production packages, application routes, user interfaces, migrations, and release artifacts.

## Probe Envelope

Each probe output MUST include a contract version, baseline ID, fixture digest, phase, synthetic context ID, environment identity, network policy, command digest, timestamps, result, ordered events, bounded diagnostics, output/asset manifest references, and limitation list.

The envelope MUST NOT include user IDs, workspace paths, session IDs, bearer tokens, browser presentation credentials, raw secret values, unrestricted URLs, or unbounded binary payloads.

## Required Capability Rows

The final matrix has at least these rows:

| Capability | Required evidence | Acceptable disposition |
|---|---|---|
| Editor build/base path | Static build and non-root serve | supported / adapter-required / blocked |
| Workspace IO injection | Two synthetic identities | supported / adapter-required / blocked |
| Dataset injection | Synthetic dataset read/write trace | supported / adapter-required / blocked |
| Native API assumptions | Complete invoked-API inventory | supported / prohibited / adapter-required / blocked |
| Browser/global persistence | IndexedDB/local storage/file picker/global directory inventory | prohibited / adapter-required / blocked |
| Node execution | Fixture graph terminal result | supported / blocked |
| Lifecycle/cancellation | Event order and abort observation | supported / adapter-required / blocked |
| External call | Typed mock request/result/error | supported / plugin-required / blocked |
| Remote debugger | Generated endpoint connection and stale attempt | supported / adapter-required / blocked |
| Offline operation | Denied outbound request log | supported / conditional / blocked |
| Supply chain | License/security/integrity inventory | supported / conditional / blocked |
| Deployment context | Browser/Hermes/native/Docker matrix | supported / unverified / blocked |

## Classification

- `supported`: repeatable evidence meets the umbrella boundary without unplanned production work.
- `adapter-required`: feasible only through a narrowly defined later Wright adapter/contract.
- `plugin-required`: a Wright-owned approved plugin is necessary; no third-party plugin authority is implied.
- `prohibited`: observed upstream behavior must remain unavailable in Wright.
- `unresolved`: evidence incomplete; cannot support a go decision.
- `blocked`: mandatory compatibility criterion fails.

## Cleanup

The spike cleanup command removes only downloaded/build/generated material under its controlled working location. It never deletes a workspace, vault, database, source checkout outside the spike root, or user-authored content. The cleanup proof is part of the evidence.
