# Wright MCP curation and protocol support research plan

Historical planning artifact, prepared before implementation on 8 September 2026. See [the implementation runbook](curation-runbook.md) and [current review report](evidence/curation-2026-09-08/report.md) for subsequent changes and live qualification.

Scope confirmed by the user: the full engineering lifecycle. This is a proposal for later catalog and product work. No application code, catalog entries, installations, registrations, remote account settings, or scheduled jobs were changed in this research pass. No MCP servers were installed or exercised.

**Recommendation:** Maintain one evidence-backed integration registry with three dispositions—Curated, Follow up, and Remove from discovery—and publish a small selection organized around engineering tasks. Evaluate useful engineering outcomes, setup quality, and repeat use. Treat publisher authority, popularity, protocol compatibility, and Wright qualification as separate facts.

Start with a planning target of **15–20 curated integration families**, with one preferred choice and at most one justified alternative per important capability. This is a ceiling to guide selection, not a quota to fill with weak entries. A user's platform, installed engineering software, accounts, and process stage should narrow the choices further. Catalog inclusion must remain separate from installation and execution permission.

## Evidence established in this research pass

The local bundled [engineering catalog](../../packages/tool_registry/src/tool_registry/catalog/engineering-catalog.yaml) contains **70 records**. This is a count of that file, not of the user's active installation or of unique usable MCP implementations. Wright also has [managed servers](../../packages/tool_registry/src/tool_registry/wright_managed_servers.py), and deployments can have active catalog updates and custom entries. Reconciliation with the approximately 75 shown in the product belongs in the first inventory step.

| Current bundled installability label | Records |
|---|---:|
| tested | 14 |
| might_work | 35 |
| non_working | 9 |
| blocked | 12 |
| Total | 70 |

The separate validation-status counts are 12 passed, 22 not_tested, 19 dependency_missing, 9 failed, and 8 blocked. Verification classifications include three UI/standard records, three API-wrapper candidates, and two capability aliases. These classifications require reconciliation before reporting a count of available servers.

Several examples explain why existing labels cannot become recommendations automatically:

- `brep-mcp` and `playwright-mcp` are labeled tested but have top-level validation status not_tested. BREP additionally has a [Windows qualification record](../../docs/mcp-catalog/evidence/windows-qualification-2026-08-13/brep-mcp-windows-qualification.md) reporting a backend failure after successful protocol discovery. These are different evidence scopes that need a coherent presentation.
- `openscad-mcp` explicitly records a generated STL and a successful Wright/Hermes gateway call. That is stronger evidence than package startup alone, although it remains historical and platform-specific.
- `freecad-mcp-sandraschi` records success being reported without the requested STL being produced. Artifact verification must be a blocking acceptance check.
- `freecad-booleans-lucygoodchild` has a passing status with a caveat about operational logging on protocol stdout. A successful permissive-client probe does not establish reliable stdio behavior.
- `web3d-mcp` has a historical passing record that also reports dependency vulnerabilities and a Node version mismatch. Their current severity, applicability, and resolution need review; the historical vulnerability count alone is insufficient to declare it unsafe today.
- `rosbag-mcp-binabik` required a dependency pin to work. Preserve and retest the working dependency set, and check whether upstream has repaired the issue.
- `autocad-mcp` passed using an ezdxf backend on Linux. That does not establish Windows AutoCAD automation. `solidworks-api-mcp` records documentation-corpus operations, not SolidWorks model editing.
- The [GB10 evidence](../../docs/mcp-catalog/evidence/gb10-clean-container-mcp-validation-2026-08-12.md) explicitly calls its Ansys/NVIDIA results partial because gateway probes were not performed. A disconnected solver status is not a successful simulation.

These observations are a planning sample, not a completed audit of every record or a newly qualified shortlist.

Wright already has [signed catalog updates, exact previews, activation, and rollback](../../docs/mcp-catalog/dynamic-engineering-catalog.md), a [clean-container validation process](../../docs/mcp-catalog/mcp-server-testing-process.md), [native Windows qualification](../../docs/mcp-catalog/windows-mcp-qualification.md), and [MCP Apps/scoped WebMCP support](../../docs/workspace-surfaces/mcp-and-webmcp.md). The [weekly catalog workflow](../../.github/workflows/mcp-catalog.yml) checks catalog and bundle consistency; it does not establish that every upstream integration still works. Reuse these foundations.

Baseline for reproduction: repository HEAD observed as `1ada5de0aaa608baadafa41031e5877eb685bed3`; bundled catalog SHA-256 `d76edd32a1a94c8755c225ab3bee071b09dfe8bb7bf618730d03ed365b7d9d7f`. The checkout had pre-existing changes and another agent is working in it. Findings describe the files read during this pass, rather than a deployed-release certification.

## 1. Plan to create and maintain the curated list

### Define coverage using tasks and artifacts

Build a lifecycle matrix before ranking servers. A category tag does not establish coverage: each credited capability needs an acceptance scenario, an expected artifact or result, and an independently checked outcome.

| Lifecycle area | Representative user outcome | Evidence required for coverage |
|---|---|---|
| Requirements and systems definition | Retrieve requirements, identify constraints, trace a requirement to its design and test | Correct source identities, revisions, permissions, and trace links |
| Concept and architecture | Compare concepts and derive preliminary sizing or system models | Reproducible assumptions, calculations, and reviewable model outputs |
| Detailed design | Create or inspect mechanical geometry, schematics, PCB data, drawings, or software | Valid native/exported artifacts, dimensions, units, and stable object identities |
| Analysis and simulation | Prepare a case, solve it, inspect convergence, compare with acceptance criteria | Correct boundary conditions, solver identity, numerical tolerances, and result artifacts |
| BOM, sourcing, and costing | Extract a BOM, compare parts, identify availability and substitution risks | Part/revision fidelity, dated supplier evidence, explicit uncertainty; no purchasing in curation tests |
| Manufacturing and assembly planning | Derive process plans, setup sheets, CAM/slicer outputs, or assembly instructions | Traceability to design revision and usable planning artifacts; no machine actuation in ordinary validation |
| Verification, test, and quality | Compare measurements with requirements and produce a test report | Raw-data provenance, units, calibration context where applicable, and correct pass/fail results |
| Release and configuration management | Build a review package and follow an engineering change across artifacts | Versioned documents, approvals represented accurately, and unbroken traceability |
| Operations, service, and improvement | Inspect telemetry, diagnose an issue, and feed a change back into engineering | Correct asset/time-window identification and a reproducible diagnostic trail |

Documents, search, spreadsheets, data access, visualization, collaboration, and access control support all stages. Prefer Wright's existing capability when it already satisfies the task. Do not add an MCP merely to duplicate it.

Every matrix cell should say **qualified**, **partial**, or **gap**. Where no suitable integration exists, record an explicit manual/API alternative and a discovery priority. Do not claim complete automated lifecycle coverage until the relevant handoffs pass.

### Use three dispositions and scoped qualification

| Disposition | Admission rule | User experience |
|---|---|---|
| Curated | Required gates pass for a named workflow and environment; there is evidence of user value and a support owner | Recommended for applicable users, with setup prerequisites and last verified date |
| Follow up | A useful candidate has unresolved evidence, a repairable failure, a required host/account, or preview-only access | Kept in the research/admin backlog; available for deliberate pilot evaluation, outside default recommendations |
| Remove from discovery | Duplicate, misclassified, unverifiable after investigation, abandoned without a viable path, persistently broken, or unacceptable unresolved risk | Hidden from new-user discovery; a dated retirement record, reason, aliases, and replacement guidance remain |

Qualification belongs to a **server version + dependency set + Wright build + environment + capability scope**, not just a server name. One family may be curated for Linux x64 geometry export while its Windows desktop workflow remains in Follow up. A family-level recommendation must never imply that all tools or platforms passed.

Use separate dimensions for publisher identity, adoption, maintenance, installability, protocol results, backend results, gateway results, user experience, and curation disposition. Installation, enablement, authentication, and workspace permissions are operational state and should not be rewritten by a curation decision.

The current testing documentation says blocked entries remain visible. The later implementation should update that guidance explicitly: retain those records in research/admin views while showing curated choices by default. Preserve the required evidence and catalog-order testing rules.

### Apply blocking gates before ranking

1. **Identity and supportability:** establish the canonical publisher/repository/package/endpoint, ownership, current release or revision, license and distribution constraints, supported host versions, and a reproducible setup recipe. A well-known vendor's API does not make an unrelated wrapper vendor-official.
2. **Security and permission fit:** review the actual package/lockfile and tool behavior; identify arbitrary code execution, filesystem/network scope, secrets, data destinations, and consequential actions. Require enforceable scope and safe defaults for the qualified use. Tool annotations alone are not permission enforcement.
3. **Protocol and backend correctness:** establish installation/startup, initialization, discovery, real backend interaction, schema/error behavior, and the actual output. Never award a backend pass for a mocked host, missing-license message, or disconnected status response.
4. **Wright integration:** run the selected tool through Wright's gateway and the advertised user entry point. Verify workspace isolation, argument/result handling, cancellation, restart/reconnect, and usable diagnostics. Validate any claimed UI surface as part of the task.
5. **Repeatable user value:** prove that target users can complete a meaningful task using the documented setup and can use it again. Record setup time, manual fixes, failure reasons, and outcome correctness.

For normal software integrations, proposed initial acceptance is three clean setup attempts and ten representative task runs, with at least nine correct task outcomes and no unresolved critical failures. All deterministic artifact, isolation, and permission checks must pass. These are small-sample acceptance checks, not an asserted production reliability rate. Confirm task usefulness with at least two target users completing two sessions, or equivalent documented repeat use across independent projects. Physical control has additional qualification below.

After gates pass, use a versioned 100-point rubric: outcome reliability 30, setup/recovery experience 20, adoption/user demand 15, maintenance/support 15, incremental lifecycle coverage 15, and deployment/cost fit 5. Start with 80 as the recommendation threshold and calibrate it during the pilot. A score cannot override a failed gate, unknown critical evidence, or lack of useful coverage.

For each dimension, use anchored ratings: 0 = absent/unacceptable, 1 = weak evidence, 2 = partial evidence, 3 = meets the target scenario, 4 = repeatable strong evidence, 5 = sustained evidence across relevant users/environments. Multiply by the dimension weight divided by five. Record unknown separately and award no provisional points for it. Keep the raw evidence next to the score.

### Measure adoption without confusing it with attention

Prioritize existing consented Wright usage/support evidence and structured customer interviews: successful repeat tasks, repeat users/projects, abandonment, and support burden. No new telemetry is collected by this plan. Where product telemetry is absent, use voluntary pilot logs with counts and outcomes rather than private engineering content.

For external evidence, record named deployments, independent user reports, substantive issue discussions, release activity, maintainer responses, and package-download trends. Distinguish use of the engineering product from use of its MCP server. Downloads can include CI; stars show interest. Neither is proof of reliability. Closed-source vendor services need service and customer evidence in place of public commit metrics. Mark unmeasured adoption unknown.

### Select a coherent portfolio and prove the handoffs

Compare alternatives on the same scenarios. Prefer fewer tools that produce compatible artifacts. Keep an alternative only for a specific advantage such as a different licensed CAD ecosystem, local operation, a supported OS, or a capability the preferred option lacks. A new family should close a gap or improve an existing choice materially.

Test at least three reference journeys during the first pilot:

- A mechanical part: requirement → parametric CAD → small verified analysis → manufacturing package → inspection report.
- An electromechanical assembly: requirements → schematic/PCB or assembly data → BOM → sourcing review → test evidence → revision/change record.
- An operational issue: telemetry or recorded test data → diagnosis → proposed design change → rerun analysis/test → updated release package.

At every transition, verify identifiers, revision, units, coordinate conventions where relevant, file validity, ownership, and provenance. The next stage must be able to consume the output. A manual transition is acceptable when labeled, but does not count as an automated handoff.

## 2. Plan to review Wright's existing entries

### Inventory and normalize first

Take a read-only snapshot of the bundled catalog, active signed catalog, database-visible entries, Docker bundles, managed servers, import/custom entries, setup recipes, follow-ups, and all platform evidence. Record where every UI row originates. Reconcile the observed product count and retain user-owned entries separately from the maintained public recommendation set.

Normalize aliases and stable IDs without erasing independent implementations. Several forks of FreeCAD can be distinct servers while still belonging to one comparison family. Conversely, a skill package that installs an existing MCP server, a capability alias, an API-only wrapper idea, and a standard itself should not inflate the count of available servers. Two endpoints in one repository may have distinct capabilities and deserve separate qualification scopes.

For each record, capture primary source and observation date, exact artifact identity, current publisher status, advertised vs. observed capability, existing evidence scope/age, dependencies, account/license requirements, reported problems, relevant coverage cells, and its provisional disposition. Give every Follow up item an owner, next action, due date, and closure condition.

### Review in a useful order

First desk-review the entire inventory and identify immediate misleading listings. For live qualification, select priority candidates based on likely user value and then follow the repository's required catalog ordering within the approved run set. Do not execute discovery-supplied commands automatically.

| Review batch | Examples from this snapshot | Planned treatment |
|---|---|---|
| Strong historical evidence | OpenSCAD, OASiS, selected FreeCAD variants, Blender, Autodesk Product Help | Check current releases and evidence; prioritize requalification for specific workflows. No automatic promotion. |
| Conflicting or caveated labels | BREP, Playwright, FreeCAD Booleans, Web3D, ROSBag | Reconcile per-platform records; resolve actual failure, security, pinning, and protocol questions before recommending. |
| Known failed integrations | The nine non_working entries | Remove from default recommendations; determine whether repair/replacement is viable, then time-box Follow up or retire. |
| Vendor/account/host dependent | Autodesk Fusion/APS, Onshape Labs, MATLAB, Ansys, Rescale, Solid Edge | Preserve as legitimate candidates; qualify using appropriate licensed hosts/test accounts when available. Missing prerequisites are not proof the upstream is broken. |
| Non-server and uncertain identities | WebMCP Standard, MCP-UI, API-wrapper candidates, capability aliases, URL-needed entries | Move standards to protocol documentation, wrappers to the development backlog, aliases to canonical identities; investigate uncertain sources. Remove misleading standalone server listings. |

Current official [MATLAB documentation](https://github.com/matlab/matlab-mcp-server) also shows why a licensing/setup review matters: it has host/toolbox prerequisites and restrictions on shared server use. A successful local test cannot establish suitability for every deployment model.

### Requalify with the existing Wright process

Follow the [required clean-container loop](../../docs/mcp-catalog/mcp-server-testing-process.md): a clean Intel Linux Wright container for applicable servers, only the selected server's prerequisites, protocol probes, a safe real backend call, a gateway proxy call, redacted evidence, a reusable setup recipe, and reset before the next server. Do not add CAD applications, vendor SDKs, licenses, or hardware drivers to Wright's base image.

Use the [Windows qualification process](../../docs/mcp-catalog/windows-mcp-qualification.md) for desktop/vendor integrations; retain its reviewed recipe boundaries. Add separate native/macOS/ARM64 qualification where those environments will be advertised. Linux x64 does not imply GB10 ARM64, and a container pass does not imply a native desktop bridge pass. Test remote services from the relevant Wright client environment without installing irrelevant hosts.

Add scenario and user-experience evidence to these existing tests rather than replacing them. If a scenario uses the workflow editor, future verification must enter the served application through the workspace Workflow/Workflows control and preserve the reviewed authoring capabilities, as required by [workflow UI integration guidance](../../docs/contributing/workflow-ui-integration.md).

### Retirement and repair rules

- A verified critical security issue, corrupt artifact, false-success response, or permission bypass immediately disqualifies the affected recommendation scope. Apply any runtime containment under a separately established operational policy; changing discovery metadata must not silently stop user workloads.
- A reproducible functional failure moves the affected scope to Follow up with a proposed 30-day repair window. Confirm transient external failures with bounded retries and distinguish service, credential, local-host, Wright, and upstream faults. Repeated scheduled runs do not reset the repair deadline.
- An explicitly deprecated or replaced implementation can be retired after confirming the replacement and migration effect. A missing repository requires checking redirects, renames, the package publisher, and another observation before declaring it dead.
- Lack of commits for 120 days triggers maintenance review; it does not itself prove abandonment. A stable pinned server with current successful validation may remain suitable.
- Zero observed use over 90 days triggers review only when measurement exists. Preserve a useful niche integration if it fills a gap and remains maintainable. Missing telemetry is not zero usage.
- When repair has no owner or viable path, or an alternative is clearly preferable, move to Remove from discovery with a reason, replacement if available, and migration notes. Allow reinstatement only after new evidence and review.

Retain retirement records so discovery does not repeatedly re-add the same broken package. Preserve catalog aliases, custom configurations, stored credential references, intentional disablement, and existing user installations. Ordinary retirement should show a notice and replacement path rather than automatically uninstalling software or changing active workflows.

The output of this review is a reconciled inventory, three disposition views, an evidence index, a platform/workflow matrix, a repair queue, and a proposed catalog diff. It is not a bulk deletion based on old labels.

## 3. Plan to find and add new integrations

### Maintain a repeatable source register

Use the official [MCP Registry](https://modelcontextprotocol.io/registry/about) for public metadata and identity discovery, then verify against publisher documentation and source/package records. Its own [terms](https://modelcontextprotocol.io/registry/terms-of-service) say suitability needs independent evaluation. Registry inclusion does not establish Wright compatibility or quality.

Also watch vendor developer portals and release notes; established publisher organizations on GitHub; package releases; relevant engineering projects; customer requests; and partner/private integration submissions. The public registry excludes private-network servers, so it cannot cover enterprise engineering by itself. Public aggregators and community lists are useful lead sources, but promotion evidence should come from primary sources or reproducible tests.

Search by engineering outcome and by neglected matrix cells, including requirements/traceability, PLM/PDM, BOM, part sourcing, CAM, metrology, QMS, MES, maintenance, and telemetry. Searching only for CAD MCPs will reinforce the current concentration. Follow renamed projects and releases of known candidates as well as brand-new repositories.

Store the source/query, retrieval time, source identifier, cursor or last-seen revision, and fetch outcome. Use overlapping date windows and deduplicate by identity so a changed description or missed crawl does not lose a candidate. Keep a last successful checkpoint when a source is unavailable.

### Run the same qualification funnel for every source

Discover → identify/deduplicate → map to a user task → assess provenance/adoption/maintenance → desk review → Follow up/pilot → bounded qualification → score against alternatives → reviewer decision → proposed signed catalog update.

Every newly discovered integration begins in Follow up. An abandoned, duplicate, or clearly irrelevant lead can go directly to a retirement/rejection record with evidence. No search result should install, enable, or promote itself.

Compare the currently qualified version and the latest upstream candidate separately. Test new releases before replacing known-good pins. A pin must still be monitored for security and backend API drift; pinning indefinitely is not a maintenance strategy. Changes in publisher identity, package ownership, requested permissions, tool schemas, or data destinations trigger additional review.

### Concrete leads found during this pass

These are examples of discovery priorities, not claims of widespread adoption or Wright qualification. Their identities are absent from the 70-row bundled catalog inspected here; check the live/custom inventory before adding them.

| Lead | Lifecycle contribution | Evidence and next step |
|---|---|---|
| GitHub's official MCP server | Requirements/issues, code, engineering changes, CI and release evidence | [Publisher repository](https://github.com/github/github-mcp-server) and [configuration guide](https://github.com/github/github-mcp-server/blob/main/docs/server-configuration.md) provide local/remote configurations and restricted toolsets. Test a minimal read-only project workflow and the actual Wright auth path. |
| Atlassian Rovo MCP Server | Requirements, engineering knowledge, Jira work items, collaboration | [Atlassian setup documentation](https://support.atlassian.com/atlassian-ai-gateway/docs/get-started-with-the-atlassian-remote-mcp-server/) establishes the vendor offering. Evaluate authorized access and traceability on a test tenant. |
| Grafana MCP | Operations, diagnostics, service feedback | [Publisher repository](https://github.com/grafana/mcp-grafana) documents observability tools and read-only operation. Validate a known telemetry question against its underlying data. |
| Partuno | Electronic component research, BOM analysis, DigiKey/Mouser sourcing comparison | [Maintainer repository](https://github.com/JPMarhefka/partuno) describes a community implementation using operator-owned credentials. Verify identity/package, adoption, normalization, and source freshness. It is not presented as a DigiKey- or Mouser-official server. |

Also prioritize qualification of promising existing families—such as MATLAB, Ansys, Onshape, and Rescale—when they close a more valuable gap than another new entry. A skill collection around an MCP implementation should be represented as supporting material rather than automatically counted as an additional server.

## Supporting MCP, WebMCP, and MHS in later Wright updates

Use one discovery and curation framework with different execution/qualification profiles. A transport field alone cannot describe all three.

| Technology | Verified distinction | Planned Wright treatment |
|---|---|---|
| MCP | The published transport specification covers stdio and Streamable HTTP, with compatibility considerations for older HTTP+SSE deployments. [MCP transport specification](https://modelcontextprotocol.io/specification/2025-11-25/basic/transports) | Extend the existing gateway/registry. Track the negotiated protocol version, transport, authentication requirements, capabilities, and exact tested configurations. Audit legacy transport normalization rather than assuming SSE and Streamable HTTP mean the same thing. |
| WebMCP | The 4 September 2026 document is a Draft Community Group Report, not a W3C Standard. It exposes browser-side tools through document.modelContext. [Current draft](https://webmachinelearning.github.io/webmcp/) | Preserve Wright's scoped page bridge and distinguish it from native WebMCP conformance. Qualify the supported browser builds, active-page/session lifecycle, origin and Permissions Policy behavior, registration/disposal, cancellation, and native fallback. |
| Model Hardware Standard (MHS) | Anthropic announced a research preview on 27 August 2026. It describes standardized device drivers/metadata and access through MCP, CLI, and APIs, with open sourcing still presented as a future step. [Anthropic announcement](https://www.anthropic.com/news/model-hardware-standard-research-preview) | Track it as a hardware capability/qualification profile that may use MCP. Keep preview integrations in Follow up until accessible specification and implementation evidence support a real compatibility claim. Do not invent a wire format or label existing robot/PLC servers MHS-compatible. |

The June Chrome [origin-trial announcement](https://developer.chrome.com/blog/ai-webmcp-origin-trial) further supports treating native browser compatibility as version-specific. Recheck the current draft and actual browser behavior at implementation time. Maintain separate tests for Wright's bridge and for the native API; passing one is not conformance evidence for the other. Chrome also recommends [evaluating whether agents choose and use tools successfully](https://developer.chrome.com/docs/ai/webmcp/evals), which belongs in the user-outcome gate.

MCP Apps is an additional UI capability, not a fourth server transport. Preserve Wright's existing packaged UI resources, sandboxing, and useful text/structured fallbacks. A conventional server with a full web application is a managed application unless it actually publishes the MCP Apps contract. Standards and UI SDKs belong in integration documentation, not the available-server count.

For later metadata design, distinguish integration family/identity, access mechanism, protocol version, deployment environment, browser/UI capability, device-control capability, and curated scope. Keep preview or simulated support visibly separate from measured production support. Reuse existing catalog fields and evidence models where possible; add fields only after a gap analysis.

### Hardware qualification proposed for Wright

These are proposed Wright acceptance requirements, not claims about undocumented MHS guarantees:

1. Obtain the applicable preview/public specification and a supported device/driver implementation before planning a concrete adapter. Record driver, firmware, device identity, API/specification version, units, operating bounds, and required local configuration. No preview application or outreach was submitted in this research pass.
2. Begin with simulated devices, then observation-only access to known hardware, then a constrained supervised bench procedure. Promote only the exact qualified operation and environment. Simulation is not proof of physical safety.
3. Keep authorization, resource ownership, operating envelopes, and interlocks enforced outside the model. Preserve physical emergency stops and deterministic device/controller protections. Natural-language device descriptions do not replace them.
4. Exercise disconnected devices, stale measurements, conflicting controllers, out-of-range requests, expired authorization, interrupted actions, and an active emergency stop in an appropriate test environment. Record physical state as well as command acknowledgments.
5. Treat timeout/cancellation as an uncertain outcome until device state is reconciled. Do not blindly retry an action that may already have moved hardware or dispensed material. Require an explicit recovery procedure and an operator for ambiguous states.
6. Require domain-qualified review of bench evidence before promoting actuation. Keep observation-only and motion/process-control permissions distinct. A recommendation does not grant authority to operate a machine.

Existing robotics/industrial MCP integrations can be reviewed under this hardware policy without claiming MHS conformance. The MHS workstream remains useful even while preview access limits implementation evidence.

## Repeatable operating cycle and deliverables

### A run that can be repeated and audited

Each run starts with a manifest: catalog snapshot/digest, policy and rubric version, scenario-pack version, Wright build, target environments, upstream revisions, evidence cut-off time, owners, and allowed validation budget. Reusing identical inputs should produce the same disposition proposals. Manual exceptions require a named reviewer, reason, and expiry.

The run produces:

1. An inventory delta and source-health report, including failed fetches and ambiguous identities.
2. Updated evidence records and capability/platform coverage, with pass/partial/fail/not-tested kept separate.
3. Three disposition views with reasons, decision dates, owners, next review dates, and replacements where relevant.
4. A ranked, bounded qualification queue, including unresolved lifecycle gaps.
5. An exact proposed catalog diff and user-impact notes for promotions, demotions, changed prerequisites, and retirements.
6. A reviewer decision and, only in later authorized publishing work, a signed catalog snapshot using Wright's existing preview/activation/rollback mechanism.

Evidence records should include source/version/hash, resolved dependencies, host/browser/firmware as applicable, recipe and scenario identities, direct/backend/gateway/user-journey outcomes, output checks, redacted diagnostic references, setup time, observed errors, and evidence expiry. Store references to authorized account profiles without credentials or private customer content.

An ordinary rerun must not reinstall already qualified versions, reset repair deadlines, clear incident history, create duplicate follow-ups, or silently enable integrations. Source outages should preserve the previous verified snapshot and mark the refresh incomplete.

### Proposed cadence

| Cadence | Work | Decision/output |
|---|---|---|
| Weekly | Check publisher releases, registry/source deltas, deprecations, issue/security signals, watchlist deadlines, and coverage gaps | Review a bounded intake, initially 10–15 leads and up to five new qualification candidates |
| Monthly | Requalify curated software integrations on advertised environment profiles; review setup failures and repeat use | Renew, narrow, demote, or retire recommendations with evidence |
| Quarterly | Compare competing families, revisit lifecycle journeys and user experience, review niche/unused entries and hardware bench evidence | Portfolio changes and next-quarter gap priorities |
| Event-triggered | Relevant Wright/SDK/browser changes, upstream releases, schema/auth/ownership changes, reproducible failures, or security incidents | Run affected tests promptly and suspend affected recommendations when required |

Proposed evidence expiry: 60 days for software qualification, with monthly runs providing renewal margin. Material changes invalidate the affected scope sooner. Use separately defined device/firmware/installation expiry and change triggers for hardware; a quarterly review alone does not establish continued physical safety. These intervals are initial policy values to adjust after observing cost and failure rates.

Assign a catalog owner to the inventory/decision queue, qualification owners to platform evidence, and a reviewer to promotion/retirement decisions. Use engineering-domain reviewers for numerical correctness and hardware operations. Automate collection, comparisons, and reproducible probes later; retain review of recommendation changes and consequential scopes.

### Initial rollout proposal

| Phase | Expected effort, assuming access and operators | Deliverable |
|---|---|---|
| Inventory and policy | 2–3 working days | Reconciled count, classification rubric, lifecycle matrix, first three-way desk review |
| Evidence audit and recipes | 3–5 working days | Every existing row has a proposed disposition and next action; misleading claims identified; priority qualification recipes |
| Focused qualification and user pilot | 1–2 weeks | Evidence for the strongest 10–15 candidates, comparison results, three lifecycle journeys, explicit gaps |
| First curated publication and rerun rehearsal | 2–3 working days | Reviewed shortlist, follow-up/removal views, migration notes, and a second run demonstrating stable results |

This is a phased estimate, not a commitment that all 70 records or all commercial/hardware systems can be fully qualified in that period. Access-limited items remain in Follow up with a concrete blocker. The shortlist can be smaller than its planning target.

Before calling the first release complete, require every public recommendation to have an owner, named qualified workflow/platform, current evidence, accurate prerequisites, and a usable setup/recovery guide. Require every existing row to have a reasoned disposition, every important lifecycle cell to have evidence or an explicit gap, and every retired entry to have preserved history. Report setup success, time to first useful result, task correctness, repeat use, support burden, and verified handoff coverage. Raw server count is secondary.

The next implementation planning step should translate this operating policy into a small set of product changes: curated views and lifecycle filters; consistent scoped evidence/statuses; discovery intake and review outputs; scheduled qualification orchestration; native WebMCP conformance work; and an MHS research/qualification boundary. Keep these changes coordinated with the agent already modifying Wright.
