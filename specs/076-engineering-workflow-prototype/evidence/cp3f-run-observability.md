# CP3F Evidence — In-Flight Run Observability

**Status**: Ready for hands-on discovery

**Date**: 2026-08-26
**Decision state**: Provisional UI and adapter experiment

## Ambiguity

When a workflow block takes seconds or minutes, can an engineer tell which
block is executing, what the executor is doing, whether it is still active,
and whether any useful output is emerging? The previous toolbar text
`Running selected AI` did not answer those questions.

## Hypothesis

A fixed diagram-level run monitor plus a stronger active-block state will make
the execution frontier understandable without forcing the user to discover and
open an inspector tab. Showing partial text as explicitly uncommitted evidence
will provide confidence that work is progressing without allowing downstream
blocks to consume an incomplete artifact.

## Smallest useful experiment

- The generic LLM adapter accepts an optional progress observer.
- The live adapter reports preparing, attachment upload, waiting, generating,
  and finalizing stages.
- Token output is throttled before being projected into the UI.
- A fixed run monitor shows active block identity, elapsed time, each block's
  state, current activity, and an output preview.
- The monitor remains after the AI completes so the committed output and next
  blocked frontier can be compared.
- Clicking a monitor step selects the corresponding diagram block.

## Deliberate exclusions

- No durable backend run or step event store.
- No cancel operation or total execution deadline.
- No reconnect or stale-run reconciliation.
- No MCP execution, schema mapping, or outcome evaluation.
- No claim that token text proves useful progress; a model may stream low-value
  content while still failing semantically.
- No final production placement or responsive-layout decision.

## Hands-on test

1. Open `/prototype/engineering-workflow?scenario=diagnostic` and select
   **Diagram**.
2. Select a configured model and a thinking level from Block 2.
3. Run the selected AI.
4. Confirm the monitor says `Executing block 2 of 4` and names the AI block.
5. Confirm the current lifecycle activity and elapsed time change while the
   request remains active.
6. Confirm emerging text is labeled `Uncommitted output preview`.
7. Click a step in the monitor and confirm the same diagram block is selected.
8. When the AI completes, confirm the monitor changes to Block 3 as the active
   frontier and relabels the text `Committed AI output`.
9. Repeat once with no attachments and once with an image to observe the
   preparation/upload stages.

## Automated evidence

A controlled component test holds the LLM promise open, emits a progress event,
and verifies active block 2, partial output, elapsed status, and the block's
running state. It then completes the promise and verifies that the monitor
moves to frontier Block 3 and displays committed output.

## Initial observations

- Progress needs to be an executor contract, not UI guesses or fixed timers.
- The active block and output preview can be tested without a browser journey.
- Throttling token projection avoids deliberately rerendering for every tiny
  provider event.
- A page-local timer is adequate to test comprehension but cannot establish
  whether the backend is alive.
- The first hands-on review was initially misclassified as stale UI state
  because the inspected temporary session was no longer active by the time it
  was queried. A clean rerun disproved hot-module replacement as the root
  cause: Wright registered a real backend stream and remained at zero model
  output.
- The running API process had cached `http://localhost:8642` from an older
  Hermes configuration. On this Windows host, `localhost` first attempted
  IPv6 `::1`, while the restarted Hermes gateway listened only on IPv4
  `127.0.0.1`. A health request through `localhost` took about 2.2 seconds;
  the same request through `127.0.0.1` took about 30 milliseconds. The chat
  stream then consumed its long connection/read timeout before surfacing an
  error.
- A direct no-tools `gpt-5.6-sol` request through the IPv4 gateway completed in
  3.2 seconds. After restarting only the Wright API so it reloaded the current
  `127.0.0.1` configuration, the complete Wright session and SSE path finished
  in 4.7 seconds with `stream_start`, `progress`, `token`, and `stream_end`.
  This separated model/authentication health from Wright-to-gateway transport.
- Restarting the API inside the restricted development sandbox failed before
  binding port 8000 because startup configuration discovery could not stat the
  installed Hermes CLI under user AppData. Relaunching the same local API with
  the host permissions used by the normal Wright launcher succeeded. Runtime
  liveness, endpoint reachability, configuration freshness, and sandbox access
  are therefore distinct states and need distinct diagnostics.
- The adapter still hides its temporary session/run identity, and the UI does
  not reconcile page state with the backend stream registry. It also labels
  the pre-response fetch simply as `waiting for model`, even though that period
  can cover gateway connection and provider startup.

These observations remain provisional until hands-on live-run review.

## Remaining questions

1. Does the fixed monitor obscure the workflow at smaller viewport sizes?
2. Which lifecycle stages are generic enough across LLMs, MCPs, approvals, and
   long-running engineering applications?
3. Should partial output be expanded by default or summarized behind a count?
4. What backend event and cancellation contract can survive reconnects?
5. How should a user distinguish continued token activity from useful semantic
   progress?
6. At what point may the UI claim `running`: before the backend registers a
   resumable stream, or only after it returns a durable run identity?
7. What bounded gateway-connect, first-event, first-token, and total-run
   deadlines should apply, and which of them are executor-specific?
8. How should an already-running process detect that a local gateway endpoint
   or binding changed without requiring an unexplained application restart?

## Recommendation

**Keep for the next experiment**: explicit active block, elapsed time,
lifecycle activity, all-step state, and uncommitted-versus-committed output.

**Revise/test further**: monitor placement, event vocabulary, update rate, and
whether completed output remains visible after the frontier moves. Before a
production experiment, expose run/session identity; distinguish API
registration, gateway connection, provider execution, and output; reconcile
against backend status; and transition missing jobs into an explicit
stale/interrupted state.

**Discard as production assumptions**: page-local timestamps, the five current
stage names, and the current fixed overlay dimensions.

**Implementation consequence**: Record the run identity, resolved executor
endpoint without credentials, connection phase, first-event and first-token
times, and terminal reason. Long-lived services must either reload local
executor configuration safely or report that a restart is required.

**Regression case**: Simulate an unreachable gateway, an IPv4/IPv6 loopback
mismatch, a reachable gateway with a silent provider, a provider sending
heartbeats, browser reconnect, cleanup delay, and user cancellation. Verify
that each produces a distinct visible state and bounded completion.
