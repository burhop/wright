Before planning or changing workflow execution, process UI, validation, external
actions, or tool integration, read `docs/design/workflow-platform-vision.md`
and `docs/architecture/workflow-platform-refactoring-plan.md`. Apply V1-V7.
Start from the general engineering user journey and shared platform mechanisms;
a reference prototype's vendor difficulties do not determine the product roadmap.

Preserve two complementary experiences on one accepted process and durable run:
the flowchart/blocks/source/inspectors for building and inspecting, and an optional
working UI for inputs, results, questions, decisions, and progress. Process UIs
open in Wright workspace tabs by default and link to exact blocks and evidence.
A dashboard, comparison view, interactive model, questionnaire, or guided sequence
may suit the job; no mandatory layout or manufacturing lifecycle applies.

For process UI work, read `docs/design/process-apps.md`. Design around an explicit
interaction contract describing available inputs, outputs/evidence, pending
interactions, observed state, and permitted actions with exact subjects. Reuse
the existing runtime, gateway, validator, results, surfaces, and storage. The
backend owns execution, state, reviews, permitted actions, and recovery. Generated
UI code must not contain another executor or independent job-status authority.

AI authors and refines interfaces using shared Wright style/components and a
scoped process client. Users request UI generation and updates through Wright,
initially using its default LLM with prepared API/UI instructions. Map a coding
role/profile into existing agent configuration/adapters; keep role, model,
versioned instructions, and platform replaceable and record resolved provenance.
Save and version interfaces with their workflow bindings
and supported contract/client/kit versions; reuse them across runs and check
compatibility after changes. Keep a usable common view. Closing/reopening a tab
reconciles with durable state without replaying uncertain actions. Current MCP
App/WebMCP hosting does not itself provide the proposed general process client.

Resolve user-supplied requirements and readiness before starting a process.
Required inputs must be supplied, explicitly defaulted, automatically produced
by declared upstream work, or assigned to a declared user-interaction step.
Long-running unattended sections do not ask opportunistic AI questions. At a
declared human review/action step, persist waiting state and resume the same run
after the response. Predictable missing
configuration is a readiness defect; changed external conditions follow the
configured wait/recovery/failure policy without guessing or uncertain replay.

Prefer existing independent MCP providers. Keep vendor protocols and compatibility
workarounds external; no new Wright-owned Bambu MCP is planned. Catalog metadata,
example bindings, and historical evidence may name vendors. Embedded vendor
prototype code is migration debt, not a pattern for new platform features.

Applicable specs, plans, tasks, and PRs must explain the user journey, shared and
external ownership, reused mechanisms, interaction/evidence identities,
invalidation, missing-capability behaviour, and UI compatibility/fallback where
relevant. Prove new shared mechanisms with a substantially different existing
workflow. Keep engineering requirements and exact-output verification intact.
Distinguish agreed direction, proposed work, implementation, verified behaviour,
and user acceptance. Preserve existing evidence and the refined workflow editor.
Keep this guidance outside the managed Spec Kit section during context refresh.

<!-- SPECKIT START -->
For additional context about technologies to be used, project structure,
shell commands, and other important information, read the current plan
at specs/083-process-working-interfaces/plan.md

Feature 083 implements the complete common and AI-created working-interface
experience on the existing accepted process and durable source runtime. Read its
implementation-goal.md, tasks.md, contracts and acceptance-cases.md. The user
submitted the saved goal and approved local implementation/testing through M0-M5
without routine intermediate lifecycle approvals. Real process reviews and
external effects retain their separate authority. No push, merge or release is
authorized. Keep progress/evidence current and preserve existing dirty work.

Reuse Feature 082's validator/rework/result contracts; its per-subject checks
remain authority and its implementation evidence is retained. The earlier 081
campaign is reference material and remains separate. Use fresh isolated digital
proof runs; do not resume or approve protected campaign subjects. Reporting UI
belongs to another branch. Existing independent MCPs own vendor implementation.
<!-- SPECKIT END -->

Before selecting, describing, changing, or evaluating engineering workflow
examples or planning their campaign, read
`docs/design/engineering-demonstration-principles.md`. Wright's central
demonstration is an extended process using multiple existing engineering tools
through MCP servers, with actual engineering outputs handed between meaningful
stages to accomplish an overall job. A long graph, valid files, or campaign
counts alone do not establish demonstration value. Show engineering tools and
their contributions; keep software plumbing secondary. Align and reuse the
existing 30 examples, not a wholesale rewrite without explicit agreement.

Before changing the workflow/process editor or its workspace entry point, read
`docs/contributing/workflow-ui-integration.md`. Locate the latest reviewed UI
implementation and preserve its authoring capabilities when integrating runtime
work. Verify the served build through the workspace Workflow/Workflows control;
component tests or a separate editor route alone do not establish UI completion.


Before every push to a branch with a pull request targeting `dev`, read
`docs/contributing/dev-push-runbook.md` and run `scripts/check-dev-push.ps1`
on Windows or `scripts/check-dev-push.sh` on Unix. Direct pushes to `dev` are
not supported. Before merging a feature branch to `dev`, run
`scripts/check-dev-merge.ps1` on Windows or `scripts/check-dev-merge.sh` on Unix,
or document why a local host limitation prevented a specific gate. Before merging
`dev` to `main`, run `scripts/check-prod-merge.sh`. These scripts are the
merge-gate source of truth; when CI catches a failure that the scripts miss,
update the scripts and contributor docs in the same fix.

A production integration is not complete when the PR merges or the `main`
push checks pass. Follow `docs/release/release-runbook.md` and track the release
workflow through public PyPI verification, identical GHCR and Docker Hub
digests, published native lifecycle tests on Linux, macOS, and Windows,
versioned docs, and the GitHub Release published last. If a registry has just
accepted an artifact but public lookup fails, check for bounded propagation
delay and retry verification; never rebuild or republish the same version.

After merging `dev` to `main`, compare their Git tree hashes when checking
content synchronization. Different commit IDs are expected because `main`
contains PR merge commits; matching tree hashes mean the files match.

For engineering MCP server validation, follow the clean-container process in
docs/mcp-catalog/mcp-server-testing-process.md. Do not add MCP-specific host
software to the base Docker image just to make catalog validation pass.
