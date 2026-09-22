# Ready-to-paste goal: improve the examples and prepare campaign restart

Select **GPT-5.6 Sol** and **High** thinking in the task before submitting.
The prompt does not change those settings. No token budget is specified.

The [plan](D:/repos/wright/specs/082-output-content-validation/campaign-example-renewal-plan.md)
defines R0–R4, the engineering acceptance criteria and the readiness boundary.
Submitting this goal approves that bounded plan, not unspecified new engineering
requirements; the proposed lineup and material changes require the R1 agreement.

```text
/goal Improve Wright's existing 30-example engineering campaign into a compelling, realistic demonstration of connected engineering tools, implement and qualify the approved improvements, and finish ready to restart the campaign without launching the broad campaign.

Work in D:/repos/wright. Read and execute specs/082-output-content-validation/campaign-example-renewal-plan.md through R0–R4. I approve that bounded plan, including local implementation, focused tests, owned-service restarts, isolated qualification runs and focused local commits. Select Sol with High thinking for this task; preserve the campaign's existing inference settings unless separately agreed. Work as one agent.

Read AGENTS.md, docs/design/engineering-demonstration-principles.md, docs/design/engineering-demonstration-review-2026-09-21.md and the plan's required context. Reuse the existing canonical runner, validators, family preparers, working tools and input/output UI. Preserve user changes, frozen evidence, approval authority and retry ledgers. Do not restart completed feature implementation or rewrite all 30 examples.

The product outcome is a recognizable engineering job completed using multiple existing engineering applications through MCP servers, with real artifacts passed between meaningful stages. Most examples should produce a final design package tested against explicit engineering requirements, with the delivered design, analyses and downstream files all referring to the same revision. Digital verification is not physical testing or certification. Many nodes, valid files, custom scripts and reports alone do not satisfy the goal.

At R1 present one concrete 30-case lineup, including actual tools/handoffs, final deliverables, verification scope, fixed requirements, permitted design choices, reuse/replacements and missing decisions. Propose at least 24 design-package outcomes; any decision-only exceptions must be explicitly agreed and still demonstrate a substantive multi-tool process. Obtain agreement on the lineup and material engineering changes before implementing them. Preserve the old Robot/Modelica tests, but do not automatically count their unchanged narrow analyses as suitable renewed demonstrations.

After that agreement, proceed through implementation and isolated qualification without routine milestone pauses, while honoring genuine engineering reviews and external authority. Version changed definitions and baselines prospectively; never weaken requirements, fabricate evidence, approve on the user's behalf, or carry old passes into revised cases. Prove every family and materially distinct changed path with real native execution, and run preparation/preflight checks across all 30. Keep qualification runs separate from campaign credit. Apply the plan's bounded correction and no-progress rules.

Finish only when the approved set, complete verification coverage, qualified tool paths, normal-workspace results access and full prospective queue satisfy the plan's completion checklist. Deliver the revised lineup, evidence-linked readiness report, focused commits and exact tested restart/status/pause/resume instructions. Clearly distinguish prepared examples from actually executed and accepted designs. Leave broad dispatch stopped. If a required dependency or decision remains unresolved, report incomplete readiness and the precise blocker, not success.

This preparation goal takes precedence over older instructions to resume the 30/30/30/30 run. Do not launch the broad campaign, reset exhausted retries, push, merge, release, publish, submit to suppliers, operate physical devices or modify another task's deployment. Do not start another goal automatically.
```

## Prompt design notes

The OpenAI Docs skill informed the outcome-first structure, explicit authority
boundary and verifiable stopping criteria. The requested model is retained:
[GPT-5.6 Sol supports High reasoning](https://developers.openai.com/api/docs/models/gpt-5.6-sol).
The prompt follows the official
[Sol prompting guidance](https://developers.openai.com/api/docs/guides/prompt-guidance-gpt-5p6)
by keeping detailed implementation context in the plan rather than repeating it
throughout the command.

This file is a draft handoff. No goal or campaign was started by creating it.
