# Engineering Program Usability Walkthrough

This is deterministic acceptance evidence for Wright's first-use engineering
journeys. It is not an external moderated usability study. Repeat it against an
exact build and record the browser/runtime identity, viewport, elapsed time,
primary interaction count, failure step, recovery used, and evidence level.

## Common boundaries

- Use bundled/generated fixtures only: no paid service, credentials,
  proprietary application, GPU, large download, license acceptance, hardware,
  or physical actuation.
- A journey must finish within five minutes and 20 primary interactions.
- A blocked variant must expose its origin and recover in at most three primary
  interactions after the prerequisite is locally satisfied.
- Run at 320 CSS pixels, 200% zoom, keyboard only, and reduced motion. Status,
  cleanup, and recovery must remain textual and visible with zero serious or
  critical scoped Axe findings.

## Journey A: reviewed MCP-only bracket

1. Open the Capability Library and review one capability's evidence,
   compatibility, consequence, and blocker origin.
2. Create and approve an exact onboarding plan; enable it for one workspace.
   Refresh once and confirm the workspace handoff is restored without replay.
3. Open the workspace's Workflows surface and choose the structural bracket
   scenario.
4. Run **Check and prepare**. Review both MCP provider identities and evidence
   digests. Resolve any local blocker and create a fresh preflight.
5. Review the exact Rivet workflow/bindings, then run the scenario.
6. Review material artifact identities separately from observed assertion
   values/units, provider nodes/capabilities, terminal cleanup, and recovery.
7. Preview local support diagnostics, inspect omitted/redacted categories,
   confirm the exact preview, and export once.

## Journey B: reviewed MCP plus local Chatter model

Repeat Journey A with the Chatter candidate-review scenario. Preflight must name
the CAD and CAM MCP providers plus the local engineering-model provider. The
report must call the score an uncalibrated screening value, require qualified
human review, state `Machine authority: no`, and preserve provider evidence.
Model resource failure recovers by closing/cleaning the prior local run and
creating a fresh preflight; residue requires inspect-before-retry.

## Recorded deterministic evidence (2026-08-13)

`tests/ui-integration/engineering-program-journey.spec.ts` ran both journeys in
Chromium with separate timers and counters. Each used six primary interactions,
finished within the five-minute bound, passed keyboard operation at 320 CSS
pixels and 200% zoom with reduced motion, produced one explicitly confirmed
local diagnostic export, and had zero serious/critical scoped Axe findings.
Component coverage separately exercises loading, empty, unavailable, blocked,
failed, cancellation, residue, expiry, stale-preview, replay, refresh restore,
focus, and one-use export states.

The human-repeatable walkthrough generated the required chronological progress,
structured status, clickable HTML report, raw and numbered annotated screens,
browser diagnostics, and Playwright trace under the ignored local artifact root
`artifacts/ui-walkthrough/engineering-program/`. The first run
(`20260813-164018`) and first continuation (`20260813-164307-continuation`) are
preserved as stopped evidence: browser-local workspace layout state kept the
Workflows panel open, so the second journey's Open Workflows action closed it.
No product data changed. After isolating that browser preference per journey,
`20260813-164527-continuation-2` passed both journeys in 15.2 seconds total.
Each journey used six primary interactions. All three artifact roots pass the
walkthrough report validator; the two stopped records were not rewritten as
successful runs.

The existing structural-bracket and Chatter browser suites provide additional
failed-provider, blocked-preflight, cancellation, residue, advisory, and exact
recovery evidence. An external moderated engineer study remains useful follow-
up evidence and must not be reported as completed until it actually occurs.
