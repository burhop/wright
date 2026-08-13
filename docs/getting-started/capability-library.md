# Capability Library

The Capability Library is Wright's engineering integration center. It helps an
engineer discover MCP servers and related capabilities, understand the evidence
and requirements, add one through a reviewed plan, validate the real local or
remote MCP boundary, and make it available to one workspace.

These are deliberately separate decisions:

| Term | Meaning | What it does not mean |
|---|---|---|
| Discovery | A capability is visible with source, evidence, requirements, and compatibility metadata. | It is not installed or contacted. |
| Installation or connection | A reviewed Install Plan registers a remote endpoint or applies a local/host adapter. | It is not available to every workspace. |
| Validation | Wright initializes the MCP, lists tools, and may run one catalog-approved read-only probe; evidence is bound to the current capability, machine, server revision, and credential status. | It does not approve later tool calls. |
| Workspace availability | One selected workspace can discover the validated capability through Wright's gateway. | It is not blanket invocation or destructive-action permission. |
| Invocation approval | Existing safety and approval policy evaluates an individual tool call in context. | It is never implied by the four earlier states. |

## Engineer journey

1. Open **Capability Library** and search by task, vendor, application, or
   engineering domain such as CAD, ECAD, FEA, CFD, CAM, Grasshopper, or slicing.
2. Read the evidence badge, machine compatibility, concrete limitation/recovery
   reason, source records, host software, credentials, license, and alternatives.
3. Choose **Add capability**. Select a catalog entry, paste a supported MCP
   configuration, enter an HTTPS endpoint, provide a literal local command, or
   select a host bridge.
4. Review the exact, expiring Install Plan. Pasted configuration is normalized
   without command execution, variable expansion, endpoint contact, or source
   retention. Wright never accepts external vendor terms for you.
5. Store credentials through the secret boundary. The wizard shows only
   configured/not-configured status; values cannot be read back.
6. Apply the approved plan, then run validation. A passed result records protocol
   steps, schema/result digests, tool count, limitations, and redacted reason
   codes. A revision, endpoint, schema, credential binding, or machine change
   makes prior evidence stale.
7. Select exactly one workspace. Confirm the message that availability does not
   approve individual tool calls or destructive actions.

If no result matches, choose **Report this missing capability**. The structured
form preserves the visible search and filters and records vendor/source/domain/
task/platform/host notes in a review queue. A report is user-owned evidence; it
cannot become trusted, installable, active, or enabled merely by submission or
catalog refresh.

## Administrator journey

Administrators can perform all engineer steps plus manage catalog metadata:

1. Configure only a reviewed HTTPS update channel and its Wright-pinned public
   trust root. No channel means Wright continues with the complete bundled
   offline catalog.
2. Choose **Check for updates** and inspect the verified signer, expiry,
   increasing sequence, field-level diff, source provenance, and risk summary.
3. Activate the exact preview. Activation changes catalog-owned metadata only;
   it cannot install, start, authenticate, validate, or workspace-enable a
   capability.
4. After restart, verify the active snapshot and preserved custom/install/
   credential/workspace state. Use **Roll back** to return to the prior verified
   snapshot if needed. The packaged catalog remains the recovery root.
5. Export and review missing-capability reports separately. Matching a report
   requires an already reviewed capability id and does not publish a catalog
   entry.

## Honest blocked states

- **Incompatible** means an observed mandatory platform or runtime requirement
  does not match this machine.
- **Uncertain** means Wright lacks enough local evidence; it is not a prediction
  that installation will succeed.
- **Blocked** means an external term, credential, host application, approval, or
  reviewed adapter is missing.
- **Stale** means the evidence no longer matches the current snapshot, machine,
  credential binding, endpoint/executable, or server revision.
- **Not tested** means exactly that. A vendor name or catalog listing alone is
  never successful protocol or engineering-application evidence.

Normal acceptance tests use deterministic local MCP fixtures. Paid services,
proprietary CAD/CAE applications, GPUs, hardware, external license acceptance,
and physical actuation are outside the routine gate.
