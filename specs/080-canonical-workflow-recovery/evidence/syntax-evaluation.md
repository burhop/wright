# Workflow Syntax Evaluation

**Canonical subject**: `mounting-bracket.workflow` / `04cc79dad3b8177e52ab46d0c994d5d48b39f63d7483ccf504eb8d665b902b2d`

**Evidence class**: single-agent exploratory generation/edit evidence. This is not an independent mechanical-engineer study, model benchmark, or permanent syntax approval.

Strict JSON and YAML remain canonical IR treatments. When resolved against Wright's trusted installed item, tool, and reusable-step contracts, the engineering source explicitly represents every item, step, connection point, connection, tool assignment, reusable-step reference, and optional group needed to reconstruct the accepted definition exactly. Wright alone records version, ancestry, integrity, layout, and run state. All three treatments receive the same five user-visible edit tasks.

| Treatment          | Bytes | Lines | Max nesting | Readability /5* | Valid edits | Mean diff lines | Comments/format                                                | Source maps                        | Parser cost |
| ------------------ | ----: | ----: | ----------: | --------------: | ----------: | --------------: | -------------------------------------------------------------- | ---------------------------------- | ----------: |
| JSON               | 31900 |   941 |           5 |             2.5 |         5/5 |             2.0 | unsupported                                                    | custom parser required             |       1 LOC |
| YAML               | 24338 |   721 |           2 |             4.0 |         5/5 |             2.4 | lost by evaluated safe parser                                  | event parser or CST required       |       2 LOC |
| ENGINEERING_SOURCE | 15071 |   328 |           1 |             4.5 |         5/5 |             2.4 | generated guidance retained; arbitrary comments normalize away | friendly section spans implemented |     427 LOC |

\* Readability is an explicit expert heuristic based on labels, nesting, noise, and direct correspondence to engineering items/tasks. It must not be treated as moderated-user evidence.

## Identical edit corpus

- rename geometry block
- change bracket thickness
- clarify design-specification purpose
- clarify manufacturing-check prompt
- clarify feedback condition

Every formatter-produced candidate reparsed, schema-validated, and matched the intended canonical IR. Engineering-source edits reconstructed explicit connection points, routes, tool assignments, and reusable-step references while revisions, ancestry, digests, layout, and run state remained host-managed. Because the same agent authored the grammar and corpus, this is parser/edit evidence, not representative usability or multi-model evidence.

## Findings

- **Strict JSON** has the lowest implementation and migration risk and remains the best internal interchange baseline. It is verbose, deeply nested, has no comments, and is a poor primary mechanical-engineer editing surface.
- **YAML** is substantially easier to scan and has low parser effort, but the evaluated safe parser discards comments/formatting and does not expose stable source spans. A concrete-syntax-tree policy would add complexity and compatibility risk.
- **Engineering source** uses `workflow`, optional `group`, `item`, `input`, `task`, and `connection` sections with prompts, files, reports, explicit connection points, settings, tool assignments, and reusable-step references. Detailed installed item/tool/component contracts are resolved from the trusted base; version, ancestry, integrity, layout, and run records stay host-managed.
- **Legacy internal DSL** remains at `fixtures/mounting-bracket.workflow.internal-ir.wflow` only for exhaustive IR parser/conformance coverage. It is not the engineer-facing file.

## Provisional recovery decision

Keep strict JSON/YAML as canonical interchange and use the exact-round-trip engineering source as the recovery concept's editable workflow file, resolved against trusted installed contracts. Accepted source changes must still pass the canonical command/validation boundary and host compare-and-swap check. Do **not** promote it beyond the recovery treatment until independent engineer and multi-model evidence, diagnostics, migrations, and unknown-version behavior close `DEC-P0-002`.

## Reproduce

```powershell
python scripts/recovery/evaluate_workflow_syntaxes.py --write-fixtures
```
