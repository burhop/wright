# Wright workflow platform vision

**Decision date:** 30 September 2026; includes the agreed process UI clarification.  
**Authority:** The user's explicit architectural direction and request to retain
it for future coding agents.  
**Status:** Agreed product direction. Implementation support remains subject to
the evidence and limits of each delivered feature.

## Purpose

Wright enables engineers to arrange existing tools, AI capabilities, data,
validation, human decisions, and external actions into connected workflows that
accomplish useful work. Workflow definitions determine the steps, dependencies,
and decisions. Wright supplies reusable mechanisms for authoring, execution,
interaction, evidence, and recovery.

Users and AI can create both a process and an interface suited to carrying out
its job. Wright provides the shared foundations for those interfaces so each
process can have a useful experience within a consistent workspace.

Prompt to manufactured part is an important early reference workflow because of
customer interest. It must be proved well. It does not prescribe Wright's
workflow structure, required stages, supported domains, or user interface.
Printing is one manufacturing process. Manufacturing also includes machining,
fabrication, and exchanging engineering packages with third-party manufacturers.
Other workflows may analyse measurements, compare alternatives, investigate a
failure, coordinate suppliers, or produce engineering documentation without
manufacturing anything.

## How users work

Provide two complementary experiences on the same accepted process and durable
run records:

- **Build and inspect:** the flowchart, blocks, source, and contextual inspectors
  for authoring, configuration, detailed inspection, and debugging.
- **Carry out the job:** an optional process-specific UI for providing inputs,
  inspecting results, answering questions, making decisions, and following work.

The typical journey is:

1. Create or open a process with AI, a template, or the flowchart editor.
2. Use Wright's common working view, or ask Wright to compose a tailored interface
   through its configured AI/coding-agent role and shared UI foundation.
3. Review and save the interface with the process as a reusable, versioned asset.
4. Resolve required user inputs and run readiness, then start the process in a
   workspace tab presenting the inputs, results, and declared decisions for the job.
5. Move from a result or problem to its corresponding block, evidence, or run
   details; refine the process or interface when needed.

A working interface may be a dashboard, comparison table, interactive model,
questionnaire, or guided sequence. The process determines the useful form. Users
can run processes without generating custom UI. Closing a view leaves the run's
lifecycle with the backend; reopening reconciles with its current state.

## Architecture supporting the experience

| Foundation | Responsibility |
|---|---|
| Accepted process definition | Engineering steps, dependencies, tool bindings, requirements, and decision points. |
| Wright runtime services | Execution, durable state, validation, review, permitted actions, and recovery. |
| Process interaction contract | The inputs, outputs, pending questions/decisions, evidence, current state, and allowed actions available to a view. |
| Shared UI kit and scoped client | Wright styling, inputs, viewers, progress, findings, review controls, navigation, and calls to existing process services. |
| Coding-agent role | A model and versioned starting/system instructions prepared for Wright's APIs and UI kit, executed through the existing agent-adapter boundary. |
| Workspace hosting | Tabs, context, restoring views, and connections to the flowchart and run details. |
| Process-specific UI | Job-appropriate layout, explanations, and specialised interactions composed from those foundations. |
| Existing engineering capabilities | Actual engineering work through MCP providers and other supported tool boundaries. |

The interaction contract connects a process to its UI. AI composes against an
explicit description of available interactions; it does not invent workflow
behaviour from a prose description. The runtime determines which action is
currently permitted for which exact subject. The diagram and working interface
can present that same fact differently.

Map this foundation to existing services and contracts before adding anything.
Workspace surfaces, process services, and style tokens exist; a complete shared
process interaction contract, client, and UI kit remain proposed work. This
document records the intended architecture, not delivery of those additions.

## AI authoring through Wright

Users request UI creation, preview, saving, and updates through Wright. The first
implementation uses Wright's configured default LLM. Introduce a configurable
coding-agent role/profile by reusing existing agent configuration and adapters:
it identifies the model choice, versioned starting/system instructions for Wright's
API and UI contracts, and permitted capabilities and work scope.

The role describes the job; the agent platform supplies its execution environment.
Hermes is the current platform. Codex, OpenClaw, or future platforms can implement
the role through qualified adapters. Keep role, model, prompt, and platform
replaceable rather than coupling the UI generator to one vendor. Record the
resolved profile/model/instructions and runtime adapter for each generation.
Future adapter support is a direction, not a claim that every platform already
implements every role capability. This does not create a second process runner.

## Prepare runs and declare human interaction

Processes can be long running. Resolve user-supplied requirements and check
readiness before starting. A later step's required choices must already be
provided, have an explicit configured default, be produced automatically by
declared upstream work, or come from a deliberately declared interaction step.
Do not require intermediate engineering results to exist before their producers run.

The accepted process defines where user review or action is required. At those
steps, persist the waiting state and resume the same run after the declared
response. Between them, an unattended process continues without opportunistic
clarification questions from its AI. Missing predictable configuration is a
readiness defect, not a reason to invent a runtime question or form.

Readiness does not freeze the external world. Recheck current prerequisites
before consequential actions. Unavailability, failure, or insufficient evidence
follows the configured wait, bounded recovery, or failure policy and is reported
honestly. It does not grant permission to guess inputs, bypass verification, or
replay an action with an uncertain outcome. Authoring-time clarification remains
available while preparing the process; runtime interaction follows its definition.

## Decisions agents must preserve

### V1: Workflow definitions own the process

Do not require every workflow to follow design, validation, review, manufacture,
and monitoring. Those are useful capabilities and a common pattern. A definition
may use them at different points, repeat eligible work within explicit bounds,
branch, converge, or omit capabilities its job does not require.

Treat branching, parallel work, review, and bounded iteration as general workflow
needs. Document the actual compiler and runtime support before promising a
particular arrangement. Product intent does not make unsupported graph semantics
implemented. Extend the existing canonical runner when an approved feature
needs more support; do not create a domain-specific executor.

### V2: Wright owns reusable mechanisms

Wright owns workspace and workflow identities, execution state, capability
binding, artifact handoffs, provenance, validation gates, review decisions,
external action records, and recovery. Reuse the gateway, result model, validator,
workspace surfaces, storage, and established editor before adding new contracts
or services.

Domain concepts and open engineering formats can appear in configured workflows,
validation profiles, and reusable viewers/readers. The ownership question is
whether code expresses a shared engineering operation or implements a particular
vendor's application, device, service, or protocol.

### V3: Vendor implementation belongs in independent integrations

Consume independently installed and versioned providers, preferring existing
MCPs. Application/device protocols, authentication, native profile handling,
vendor state interpretation, and desktop automation belong to those providers.
The independent Solid Edge MCP illustrates this ownership boundary.

A prototype's vendor compatibility problems do not determine the platform
roadmap. Record the provider's real operating requirements and limitations,
and leave vendor workarounds to the provider ecosystem. Creating or maintaining
a new Bambu MCP is not part of the current plan; Handy compatibility remains
Bambu's and its providers' concern. A new external integration would need a
separately justified project.

Apply the same boundary to new vendor-specific integrations. Renaming code,
putting it in a Wright plugins directory, or wrapping a bundled vendor branch in
a generic class does not establish an independent integration.

Wright may retain catalog metadata, reviewed connection configuration, capability
references, example workflow bindings, and historical qualification evidence
that name a vendor. These records must not implement its protocol. Existing
in-process vendor adapters are migration subjects, not precedent for adding more.
Audit them in bounded features; this decision does not authorize a wholesale
rewrite of unrelated integrations.

### V4: A consistent experience can include specialised interfaces

Wright provides common ways to inspect outputs, configure decisions, see
findings, approve work, follow progress, and recover. Workflows select the
interactions they need. Input, review, monitoring, and external-action controls
are composed according to the job; there is no required stage list or layout.

Integrations describe supported options and return meaningful structured results.
Common options can use reviewed declarative descriptions. Complex interactions
may use a packaged MCP App or an authorised managed application through the
existing workspace-surface mechanisms. Preserve useful fallback results when a
specialised interface is absent or cannot render. A working tool need not
provide an MCP App to be usable.

Preserve two complementary experiences: the flowchart and block inspector for
authoring and detailed inspection, and an optional process UI for running the
same accepted workflow. A process UI opens in a Wright workspace tab by default.
An external browser presentation remains an explicit user choice when needed.

AI can create and refine a process UI using Wright's shared styling, interaction
components, the process interaction contract, and a scoped client for existing
process services. Wright owns the
run, evidence, decisions, and recovery. Generated presentation code must not
contain a second executor, direct vendor protocols, or browser-only run state.
Persist and version the UI with its workflow compatibility information; do not
require generating a new application on every run. Simple processes retain a
usable common view without custom UI. AI can update affected bindings when the
process changes. A visual layout change alone need not invalidate engineering
outputs; changes to inputs, decisions, and actions retain revision-bound checks.
See the proposed
[process app design](process-apps.md) for reuse, hosting, and contract boundaries.

Label the actual action: review, export, submit RFQ, request assessment, send
package, start operation, or another workflow-defined operation. Explain missing
capabilities and the consequences of a changed option. A material, geometry,
profile, or destination change can invalidate dependent outputs and reviews;
the declared dependencies determine which work must be repeated.

### V5: Engineering verification follows requirements and exact outputs

The accepted process and requirement profile define mandatory checks and their
acceptance basis. Available tools determine how evidence can be obtained; they
cannot silently remove a requirement or lower its standard.

Evaluate actual bound output revisions. Record method, source, units, tolerances,
limitations, findings, and evidence. Keep tool execution success, artifact
existence, measured compliance, human acceptance, and physical verification
distinct. A preview, model-written verdict, or provider success message alone
does not prove engineering correctness.

Use the existing process validator and qualified local/native/MCP inspection
capabilities. Generic measurement and evaluation may remain in Wright. A
vendor-specific reader or native application interaction belongs in its external
integration. Domain-specific profiles are configuration with explicit scope, not
new workflow engines.

A missing mandatory check holds the relevant downstream step with an actionable
reason. An optional check can remain unavailable with that limitation disclosed.
Profiles, outputs, and reviews are revision-bound. Changes require appropriate
revalidation. Human review remains separate from automatic measurement.

### V6: External actions preserve evidence and uncertainty

Treat a machine operation, supplier request, service submission, or similar
external action as a capability invocation with durable identity and evidence.
Record the reviewed inputs, authority, attempt, destination, provider reference,
receipt, and observations appropriate to that action.

Submission, provider acceptance, observed execution, and completion can be
different facts. Some destinations provide only a receipt; others provide rich
status and cancellation. Describe available evidence without inventing stages
or presenting another job's progress as this job's progress. Missing confirmation
must not trigger automatic replay of an action whose effects are uncertain.
Cancelling an MCP request does not prove a physical operation has stopped.

### V7: AI and integration changes stay replaceable

AI may propose workflows, generate engineering outputs, explain findings, and
perform explicitly permitted corrections. Deterministic constraints, configured
revision budgets, actual evidence, and review authority still govern release.

Discover tool capabilities dynamically, but bind a run to recorded definitions,
schemas, implementations, profiles, inputs, and outputs. Replacing a model or
server requires the compatibility and validation appropriate to that change.
Do not infer semantic equivalence from a tool name. Preserve specialised tool
features through explicit extensions rather than forcing every provider into
one minimal interface.

## How to demonstrate the architecture

Prove the prompt-to-manufactured-part reference with substantive tools and actual
artifact handoffs. Then prove the reusable mechanisms with a different workflow
whose purpose and arrangement do not require manufacturing or device monitoring.
Use existing examples where suitable and follow the
[engineering demonstration principles](engineering-demonstration-principles.md).
Retain the existing 30 examples and their evidence; do not redesign the campaign
or invent requirements under this vision.

Use separate evidence for protocol compatibility, engineering capability,
workflow behaviour, browser experience, physical execution, and user acceptance.
Mocks and fixtures establish only their tested scope. No number of passing
campaign cases establishes unrestricted workflow or vendor support.

## Applying this decision to changes

Before planning or modifying workflow execution, review UI, validation, external
actions, or tool integration, read this document. A feature plan must identify:

1. The general user journey and outcome, then any supporting reference workflow.
2. Which existing Wright mechanisms it reuses and which existing provider owns
   each vendor-specific behaviour; justify any proposed new integration.
3. The inputs, outputs, option dependencies, review subjects, and evidence.
4. Required versus optional capabilities and the behaviour when one is missing.
5. The applicable V1-V7 decisions, deviations, and acceptance evidence.
6. A different workflow or integration that will expose accidental coupling when
   the change introduces or generalises a shared mechanism.
7. For process UI changes, the interaction contract, shared components/client,
   workspace-tab behaviour, saved compatibility bindings, and common-view fallback.

Implement only the approved feature scope. A broad architectural direction does
not authorize a new executor, unbounded graph replay, weakening checks, accepting
vendor terms, changing device modes, physical actuation, publication, or release.

## Existing foundations and migration

- [Package ownership](../architecture/package-boundaries.md)
- [Capability Library](../getting-started/capability-library.md)
- [Gateway](../architecture/gateway-service.md)
- [Process validation](../workflows/process-output-validation.md)
- [MCP Apps and managed UI](../workspace-surfaces/mcp-and-webmcp.md)
- [Workflow editor integration](../contributing/workflow-ui-integration.md)
- [Process app design](process-apps.md)
- [Workflow platform refactoring plan](../architecture/workflow-platform-refactoring-plan.md)

This is the durable product direction. It does not amend the constitution or
rewrite historical approvals, frozen campaign data, feature evidence, or release
records. New feature plans must reconcile their implementation with both this
vision and the existing constitution and contributor gates.
