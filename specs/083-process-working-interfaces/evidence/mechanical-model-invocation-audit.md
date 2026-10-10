# Mechanical workflow model-request audit

**10 October 2026.** Read-only examination of retained source, run records and an
existing model-only diagnostic. No workflow was started, resumed or approved.
This closes the bounded request-provenance review for the subjects below; it does
not close the mechanical goal or qualify every adapter/model path.

## What was examined

| Saved process / exact run | Captures | Ordered submission/response pairs | Recorded outcome |
| --- | ---: | ---: | --- |
| Imported focus wheel — `1f863b0308ff4516ac041bd2ab2bc889` | 14 | 4 | Required final human evidence remains held. |
| Sheet-metal requirement review — `82ae5957752b4289b5ab9f91b416a19e` | 118 | 30 | Awaiting the actual scope/requirements decision; no dock CAD claimed. |
| CAD and thermal sizing — `31266712e3e14948a6e9f12293c18db1` | 74 | 19 | Required final human evidence remains held. |
| Native focus-wheel correction — `3843a8c98e0f40e1a15f90790a33b6b8` | 44 | 11 | Awaiting actual engineering review after correction. |
| Retained failed wheel response — `564c6ddffcb546d48d6e4da25f4879c2` | 6 | 2 | Failed: no verifiable completion evidence. |

The 256 captures include prepared runtime inputs as well as adapter/transport
observations. They are **not 256 distinct model calls**. The 66 ordered pairs
are the observed submissions and responses at the retained boundaries.

## Verified from the records

- Each saved workflow's bytes match its run's source digest. All 34 embedded
  instruction bodies per source have their recorded digest. Profile versions
  remain 1.2.0 for the earlier three processes and 1.2.1 for the correction cases.
- Effective task and response-repair instructions were independently composed
  from saved bodies, bindings, typed policy, step variables and overrides. They
  match the retained system messages and effective-text identities. No current
  default instruction resource was used to reconstruct the accepted policy.
- Prepared MCP messages and schemas match the primary adapter captures. The
  actual bridge messages contain the saved bridge instructions, the same tool
  schemas, and the required task/instruction messages. Retained tool observations
  agree with their original primary messages. None of these selected calls used
  observation omission, reference projection or decoded tool-content compaction;
  this audit makes no new live claim about those paths.
- Submission snapshots precede their responses and retain the same request,
  messages and model lock. Every observed submission has its recorded response.
  Model configuration remains `hermes-http` / `openai-codex` / `gpt-5.6-sol`,
  including captures across same-run continuation. The HTTP responses report
  the alias `hermes`; that alias is not an independently reported upstream model
  revision. The goal's implementation-model preference did not change routing.
- Captured input-image identities resolve to the actual pinned workspace PNG
  bytes. File hashes, encoded data-URL hashes, media type and size match. The
  primary and bridge captures retain the same image references.
- Bridge payload digests without redacted images are independently recomputed.
  Primary request digests also include fields not fully retained in this record;
  they are not guessed from a partial snapshot.

## Recovery: preserve the failure and the repair's scope

The failed wheel run's malformed decision is retained in the following repair
request. That historical request has four messages: system, task, rejected
assistant decision, then a separate user repair instruction. Its saved evidence
therefore **does not prove the later context-preservation fix**. The existing
execution ledger records why the separate repair turn was inadequate for the
Hermes session behavior.

The separately retained `decision-repair-probe-031.json` is a real model-only
diagnostic of the repaired request. Its current user message includes the same
task, tool schemas, input image, rejected decision and saved repair instructions.
Its accepted frozen model lock matches the original run configuration. The
observed response was a valid tool-call decision. The diagnostic discarded that
decision without invoking a provider; it is not an engineering execution or a
successful replay of the failed run. Thirteen receipt comparisons confirm this
specific scope. No diagnostic was replayed during this audit.

The subsequent native correction run separately contains an actual completion-
format repair using the saved recovery role. Its primary and bridge messages
agree. That engineering run reached review, whose authority remains unchanged.

## Evidence and limits

The bounded report retains source/run hashes, instruction identities, indexed
checks, pair identities, observed model aliases, image identities and the
historical repair finding:

- [Audit JSON](D:/repos/wright/.local-run/process-interfaces-083/mechanical-engineering-20261008/model-invocation-audit-039.json)
- [Existing model-only diagnostic](D:/repos/wright/.local-run/process-interfaces-083/mechanical-engineering-20261008/decision-repair-probe-031.json)
- [Execution ledger](../mechanical-engineering-execution.md)

The audit performed 2,536 comparisons across five records plus the 13 diagnostic
comparisons. These are evidence checks, not a regression-suite pass count.
All 41 engineering run files match the pre-audit preservation baseline.

Provider-internal instructions, hidden routing and unreported model revisions
remain unobservable. Saved UI authoring has separate capture evidence in the
execution ledger. Instruction portability improves inspectability; it does not
guarantee identical generated designs. Engineering compliance, physical behavior,
human acceptance and external-action permission retain their own authorities.
