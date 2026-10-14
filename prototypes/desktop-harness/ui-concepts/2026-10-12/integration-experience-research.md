# R0 — Desktop integration patterns and customer experience

Requested 12 October 2026. Status: task defined; initial official-source scan
recorded below. Comparative research and customer validation are not complete.
Feeds the [UI integration plan](integration-plan.md) before substantial UI work.
The narrow native-panel qualification can proceed alongside this research.

## Objective and scope

Find what others are doing inside the OpenAI desktop harness, which emerging
interaction patterns have credible evidence of value, and how Wright can feel
easy, capable and pleasant there. Recommend a few concrete improvements to the
approved concepts, rather than an exhaustive market report or more framework.

Primary users are engineers creating/editing processes and engineers/reviewers
running existing ones. Examine first use and returning to work separately. Keep
the approved shared neutral canvas and Wright's execution/permission boundaries;
research can refine entry points, controls, navigation and interaction flow.

Start with six to eight relevant examples from several independent integrations,
including an engineering/data-analysis or complex-document experience and one
weak/frustrating experience. Record actual host, mode, version, OS and date where
known. Desktop, ChatGPT web, CLI, cloud development and generic MCP clients are
different surfaces; success in one is not evidence for another.

Study complete user journeys:

- Discovery/setup and the first useful result, including hidden prerequisites.
- Selecting files/items, carrying context into chat and avoiding repeated input.
- The balance between conversation, direct editing, previews and full panels.
- Long-running work, status freshness, review, failure and recovery.
- Closing, reopening and reusing work without losing context or creating copies.
- Familiar controls, readable density, keyboard access and restrained feedback.

Candidate ideas include contextual mentions, file handlers, result cards that
open documents, selection-aware chat, starter prompts, editable previews and
explicit review handoffs. These are hypotheses, not feature commitments. The
research must be willing to challenge the concepts, not merely confirm them.

## Evidence and customer value

Use official OpenAI docs to establish host behavior; use each integration's
current documentation, source and demonstrations for its implementation. Seek
separate customer evidence in identifiable firsthand reports, support issues,
observed usability sessions and accounts describing a concrete job/outcome.
Treat vendor-selected case studies as self-reported and potentially selective.
Public complaints reveal possible friction without establishing its prevalence.
Stars, downloads and announcement engagement alone do not establish usefulness.

Ask what people would repeatedly use the integration for: faster useful results,
fewer manual handoffs, less rework, easier reuse or greater confidence in saved
outputs. Compare that benefit with doing the same job in ordinary chat or the
standalone application. State why evidence from a design/productivity customer
might or might not transfer to Wright's engineering users.

Record the following for each meaningful finding:

| Field | Required content |
| --- | --- |
| Source/freshness | Direct URL, publication/update date if known, retrieval date |
| Context | Actual host/platform/version, user and job; unknowns explicit |
| Pattern/outcome | What the person does and obtains; setup and interaction cost |
| Evidence class | Documented capability, hands-on observation, firsthand user report, vendor claim or Wright hypothesis |
| Friction/value | Benefits, delays, confusion, lost context, recovery; strength and limits of customer evidence |
| Wright decision | Adopt, test, defer or avoid; why and which journey it changes |

Cross-check consequential recommendations with independent evidence when
available. Documentation or a promotional demo alone cannot establish that a
pattern is “proven useful.” Mark missing customer evidence rather than inventing
quotes, adoption statistics or usage data. Public desk research needs no
outreach; prepare any interview invitation for the user instead of sending it.

## What “positive vibe” means for Wright

| Desired experience | Observable behavior |
| --- | --- |
| Easy to begin | Create/open a workspace and get a useful workflow without reading setup notes or pasting service URLs after connection |
| Familiar and uncluttered | One conversation, clear active document and expected keyboard/focus behavior; no duplicate host navigation |
| Clear control | User can distinguish edit, save, start, review and continue, and predict their consequences |
| Understandable progress | User can tell working, waiting for chat, waiting for review, disconnected and failed apart, and identify what to do next |
| Rewarding results | A relevant artifact/preview is easy to find and tied to the task; diagnostics are available on demand |
| Confidence after interruption | Returning restores the intended work without lost drafts, duplicate starts or replayed actions |
| Comfortable daily use | Clear labels, readable contrast, restrained motion, accessible controls and little repeated context entry |

A pleasant interface must not manufacture progress, hide failure, celebrate an
unverified result or bypass required reviews/permissions. Use plain helpful
wording and show technical detail where it helps the user's decision.

The reported “Run looks stuck” episode in
[reasoning progress](../../reasoning-progress.md) is a concrete local friction
case: users need to understand and complete the current desktop-chat handoff.
A themed waiting indicator alone does not solve it. Those are reported
prototype observations, not a customer study performed by this task.

## Outputs and completion

Produce one short findings memo containing:

1. An annotated comparison of six to eight examples, with direct evidence links
   and useful screenshots or demonstration timestamps.
2. Up to five actionable findings, separating customer-supported patterns from
   promising ideas and unsupported claims.
3. An updated Wright journey: open/create → edit/save → run → inspect → respond
   to a declared checkpoint → reopen/continue, including failure and return use.
4. Adopt/Test/Defer/Avoid decisions and **at most three small experiments**, each
   with a hypothesis, task, observable success criterion, effort and required
   host capability. Prefer less work and fewer surprises over more UI.
5. Specific implementation-plan amendments and one labelled visual for reviewing
   the findings. Explain departures from the concepts; publish nothing externally.

**Desk-research exit:** the next UI slice has evidence-backed interaction choices
and explicit gaps. This is not a customer-validation claim. Missing market data
does not indefinitely block prototyping; proceed with labelled hypotheses.

**Formative validation after a usable slice exists:** prepare short, uncoached
tasks for three to five representative people when the user can arrange them.
Ask them to start useful work, change a requirement, find a result, handle a
wait/review, and close/return. Compare with the same tasks in the current
prototype. Record completion, time to first useful result, help requests,
repeated context entry, wrong turns and state/next-action comprehension. Ask
separately about ease, confidence, pleasantness and willingness to use it for
their own work; optional 1–5 ratings supplement observed behavior.

Do not generalize a small sample into market-wide findings. If participants
are unavailable, report an expert walkthrough as such and keep customer
validation pending. Prioritize lost work, misleading state and blocked tasks
before cosmetic changes. Reuse these checks for the later Hermes shell refresh.

## Initial source scan — starting points, not customer findings

Official pages checked 12 October 2026:

| Reference | Documented pattern | Wright hypothesis |
| --- | --- | --- |
| Canva in [Plugin extensions](https://developers.openai.com/plugins/build/extensions) | Design creation/preview through sidebar tabs | Keep the useful artifact beside the conversation |
| Figma in [Plugin extensions](https://developers.openai.com/plugins/build/extensions) | File search/selection through desktop composer mentions | Refer to a workflow/result without copying paths or restating context |
| Adobe in [Plugin extensions](https://developers.openai.com/plugins/build/extensions) | File extension handlers open appropriate editors | Open `.wflow` and engineering evidence directly in suitable views |
| [UI guidelines](https://developers.openai.com/plugins/concepts/ui-guidelines) | Focused inline interactions, direct edits and no duplicate chat inputs | Keep small actions near results and larger tasks in the work panel |
| [Use-case planning](https://developers.openai.com/plugins/plan/use-case) | Start from user expectations and complete paths to useful results | Evaluate whole Wright tasks, not just whether tools or tabs open |

These are documented examples/guidelines, not hands-on plugin tests or measured
customer outcomes. Availability in the exact Windows build is separate. The
comparative review must add independent integration and user evidence before
calling a pattern established customer value.

No plugin was installed, account connected, customer contacted, application code
changed or workflow run started to prepare this brief.
