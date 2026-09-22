# Astra goal: complete the approved renewed campaign

Prepared 22 September 2026. Select GPT-6 Astra with High reasoning in the task.
The prompt does not change model settings. Preserve the campaign's separately
configured inference provider/model unless the user explicitly changes it.

This handoff was activated by the user on 22 September 2026. The active goal
authorizes finishing qualification/readiness and then executing the revised
campaign. Do not create a duplicate goal. The implementation dashboard is serving
this checkout on port 8765; its initially slow status refresh subsequently
responded successfully (observed 17:32:37 UTC). The campaign dashboard is on 8771.
See `campaign-astra-completion-progress.md` for the latest execution checkpoint.

```text
/goal Complete Wright's approved renewed 30-example engineering campaign to verified current-revision 30/30/30/30: 30 input datasets, 30 actually executed dataset/workflow combinations, 30 complete final output packages, and 30 current full-scope requirements passes.

Work in D:/repos/wright on codex/082-output-content-validation using Astra with High reasoning. The R1 lineup and proposed engineering inputs were explicitly approved on 22 September 2026; implement that agreement without asking me to approve it again. This goal authorizes completing renewal qualification and readiness, then launching and driving the revised campaign through completion. It supersedes the earlier renewal goal's instruction to finish ready but stopped. Qualification and preflight gates still apply.

Read AGENTS.md and docs/design/engineering-demonstration-principles.md first. Under specs/082-output-content-validation, read campaign-example-renewal-plan.md, its decision, lineup, engineering-input-proposal, revision, progress and qualification records, plus campaign-continuation-plan.md, campaign-continuation-progress.md and the checkpoint below this prompt. Follow the applicable constitution, validator contracts, MCP qualification and UI integration instructions. Reuse completed work and preserve unrelated changes.

Wright must demonstrate extended engineering jobs using multiple existing engineering tools through MCP servers. Actual geometry, models and analysis results must pass between meaningful stages. Deliver the approved final design packages with independent digital checks against fixed requirements, and matching design/analysis/manufacturing revisions. Preserve all 30 agreed subjects and useful existing stages. Tool counts, valid files, reports and green execution alone are insufficient. Do not invent requirements, weaken limits, substitute mock tools or present digital verification as physical testing.

First reconcile live services, credentials, owned runners, source/profile identities, native leases and durable retry state. Verify a minimal inference request through the actual campaign route. Finish the remaining harness, sheet-metal, water-heater and Robot qualification paths and any other gaps found in the existing all-family evidence. Prove material provider fixes in isolation before spending another campaign attempt. Prepare and preflight the complete approved 30-case queue, with the actual grants, tool schemas, mounts and required output contracts.

Once readiness passes, start one current canonical case through its full required checks, then run ready cases in controlled waves using the existing runner and native lease limits; serialize shared CAD resources. Continue monitoring, diagnosing, fixing and resuming within the approved scope. Routine local fixes, owned-service restarts, tests, isolated qualification, digital campaign execution and focused local commits are authorized. Preserve the campaign's existing inference settings; Astra is the implementation agent selection.

Keep immutable evidence and retry history. Use the existing bounded corrections, at most two persisted revisions for eligible configured segments. After two unsuccessful corrections to the same defect, quarantine it and progress independent cases. After three attempts with no new complete output or full-scope pass, stop expensive dispatch until a material fix is proven. A new attempt ID does not reset an exhausted episode. Revalidate all downstream results after a design revision.

Honor actual review authority. Automatic integration decisions may use only existing explicit grants; never impersonate a human approval or approve historical Robot 010. Present exact artifacts, checks and the requested decision when a required human review is reached, and continue independent authorized work. Missing evidence, stale results, unsupported checks and unresolved reviews do not earn a pass.

Keep the existing implementation and campaign dashboards available and progress records current. Clearly distinguish historical/retained results, isolated qualification, renewed campaign execution, automated checks and human acceptance. Reconcile the current-revision ledger and dashboard through supported evidence-derived projections; do not edit counters to meet the target. Keep final and intermediate outputs easy to open, with understandable tool names, plot labels, units, limits and engineering conclusions.

Persist through implementation and execution without routine milestone approval pauses. Run relevant tests and required gates, then proceed. Ask only for genuinely missing engineering decisions, credentials, authority or resources; first complete unaffected work and prepare a concrete reviewable decision. Do not modify another task's deployment, reset retry ledgers, push, merge, release, publish, order from suppliers or operate physical devices.

Finish only after an independent audit of the actual artifacts proves all four current-revision counts are 30, every mandatory requirement and review is satisfied, and every final package is accessible through the normal workspace. Save focused commits and an evidence-linked completion report. If an external blocker prevents this, retain a precise resumable checkpoint and report the unmet count and required action; do not declare success or silently reduce scope.
```

## Resume checkpoint (reverify before action)

- Renewal R0/R1/R2 are recorded complete; R3 is in progress and R4 is pending.
- Campaign API: historical ledger `30/30/24/0`; retained automated inspections
  supply 17 passes to the displayed `30/30/24/17`. Current metrics are 1 run,
  0 complete output sets and 0 passes. These are not renewed campaign completion.
- Focused commits: `9d24fdfc`, `fe512705`, `2492f8c6`, `f720f557`.
  Modelica enrollment, installer, native-export proof and binding-test changes
  remain uncommitted; preserve them.
- Harness 906/907 remain failed historical qualification attempts. Dedicated
  KiCad native-save proof passed; complete canonical ERC and correspondence remain.
  The dedicated runtime mounts attempt 907 only; recheck mounts for a successor.
- Water 901 failed with its Modelica container stopped. Water 902, run
  `9a39d55ceead467e84524ccc83d1be21`, completed the first native simulation then
  failed at `modelica_export_recorded_result` with `child_unavailable`. See
  `.local-run/renewal-qualification/water01-canonical-902/`.
  Inspection confirmed the container lacked attempt-902 export mounts; that is
  a demonstrated configuration gap. The dedicated runtime repair has since passed
  actual native simulation, ten-file same-attempt export/readback and idempotence
  through Wright's StdioRunner/GatewayService. See
  `artifacts/campaign-example-renewal/qualification/modelica-renewal-native-export.json`.
  This is repair qualification, not proof of the entire water-package workflow.
  New server `4328a581-59ea-49d4-a90e-fb40fe8f75b7` exposes 15 tools from
  `wright-082-modelica-renewal`, with exact qualification and attempt-903 mounts.
  Inspect the progress file and live state before staging or dispatching 903.
- Actual Solid Edge flat-pattern production and downstream DXF preservation,
  and the revised Robot CAD/CalculiX chain, still need qualification.
- Preserve Robot 010 run `1e10a25958694ce2ab4d9454029b1fcf`, checkpoint
  `checkpoint-46ef3ff2d5107b0b5f55455e`, pending manual review. Revised Robot work
  uses a separate successor under the approved new requirements.
- Dashboard URLs: <http://127.0.0.1:8765/> and
  <http://127.0.0.1:8771/?view=recovery>. A running dashboard does not imply a
  running worker or current engineering acceptance.

The OpenAI Docs skill informed explicit continuation authority, outcome-based
instructions and proportional verification, following the official
[Astra prompting guidance](https://developers.openai.com/api/docs/guides/latest-model#prompting-best-practices).
