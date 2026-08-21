# Engineering Journey Acceptance Contract

## Journey A: MCP-only first use

1. Open Capability Library and search for the deterministic engineering MCP.
2. Inspect source/trust/maturity/platform/auth/install evidence.
3. Review the bounded installation or connection plan.
4. Enable the approved capability for one workspace.
5. Open Rivet scenarios and preflight a compatible multi-MCP scenario.
6. Start the scenario through Wright's run-bound gateway.
7. Observe ordered progress and a terminal report with provider attribution,
   engineering assertions, cleanup truth, and a safe next action.
8. Trigger one deterministic provider failure and complete the offered recovery.

## Journey B: MCP plus local model first use

1. Inspect a bundled engineering model package, revision, license, hardware,
   remote-code policy, and limitations.
2. Install/verify the deterministic local model without network or repository
   code execution.
3. Bind the verified model and MCP capabilities to the reviewed Rivet graph.
4. Preflight and run the Chatter review scenario.
5. Confirm model and MCP identities/digests, uncertainty/units, simulation-only
   status, assertions, and cleanup in the report.
6. Preview a support diagnostic snapshot for the run.
7. Confirm that included/omitted/redacted/truncated categories are visible,
   explicitly export once, and verify replay is denied.

## Required recovery cases

- incompatible platform/architecture;
- unavailable or unvalidated provider;
- stale capability or model binding;
- insufficient local resources;
- child/provider failure;
- cancellation with cleanup proven clean;
- residue-possible failure requiring inspect-before-retry;
- expired/stale/replayed diagnostic preview;
- offline cache miss with a safe import/follow-up action.

## Evidence tiers

| Tier | Required evidence |
|---|---|
| Component | Default, loading, progress, blocked, failure, expired, consumed, and success states; keyboard actions and live-region semantics. |
| Mocked UI integration | Both ordered journeys, all required recovery cases, 320 CSS-pixel reflow, 200% zoom, logical focus, reduced motion, and Axe scan. |
| System E2E | Local FastAPI plus web UI, deterministic fake MCPs and bundled test models, complete happy path, one provider failure, one diagnostic export/replay denial. |
| Human-repeatable | Exact controls, expected text/status, elapsed-time bound, recovery action, and evidence location; no source-code knowledge. |

## Acceptance rules

- Journey A and B complete in the deterministic walkthrough without source-code
  knowledge; no required step is pointer-only.
- Blocked state never presents a misleading start/enable/export action.
- Long operations expose programmatic status without moving focus.
- Narrow viewport and zoom never hide a required action or force simultaneous
  horizontal and vertical reading of ordinary content.
- No test requires network, credentials, paid service, proprietary app, GPU,
  hardware, or physical actuation.

