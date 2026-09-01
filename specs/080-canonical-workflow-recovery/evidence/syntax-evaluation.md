# Workflow Syntax Evaluation

**Canonical subject**: `mounting-bracket.workflow` / `dadc3d6a2e274973a9fd16f6eecd95ac1c3dac2f6ebd38c5b83b4e6a2705acb6`

**Evidence class**: single-agent exploratory generation/edit evidence. This is not an independent mechanical-engineer study, model benchmark, or permanent syntax approval.

All three files validate against the same IR schema, parse to byte-identical canonical semantics, and receive the same five edit tasks.

| Treatment | Bytes | Lines | Max nesting | Readability /5* | Valid edits | Mean diff lines | Comments/format | Source maps | Parser cost |
|---|---:|---:|---:|---:|---:|---:|---|---|---:|
| JSON | 18858 | 622 | 5 | 2.5 | 5/5 | 2.4 | unsupported | custom parser required | 1 LOC |
| YAML | 13909 | 467 | 2 | 4.0 | 5/5 | 2.4 | lost by evaluated safe parser | event parser or CST required | 2 LOC |
| DSL | 13077 | 468 | 1 | 4.5 | 5/5 | 2.4 | leading comments preserved; canonical formatting normalized | section spans implemented | 96 LOC |

\* Readability is an explicit expert heuristic based on labels, nesting, noise, and direct correspondence to blocks/ports. It must not be treated as moderated-user evidence.

## Identical edit corpus

- rename geometry block
- change bracket thickness
- make material optional
- change exact export tool
- clarify feedback condition

Every formatter-produced candidate reparsed, schema-validated, and matched the intended canonical IR. Because the same agent authored the grammar and corpus, this is useful parser/edit evidence but optimistic AI-generation evidence. A permanent choice still requires independent model samples with invalid controls and representative engineers.

## Findings

- **Strict JSON** has the lowest implementation and migration risk and remains the best internal interchange baseline. It is verbose, deeply nested, has no comments, and is a poor primary mechanical-engineer editing surface.
- **YAML** is substantially easier to scan and has low parser effort, but the evaluated safe parser discards comments/formatting and does not expose stable source spans. A concrete-syntax-tree policy would add complexity and compatibility risk.
- **Small DSL** has the clearest one-section-per-concept correspondence, implemented semantic-ID source spans, and preserved leading comments. It has the highest grammar/parser/migration ownership and the weakest ecosystem maturity.

## Provisional recovery decision

Use strict JSON as canonical interchange and the small DSL only as the disposable recovery concept's Code treatment. This is reversible and maximizes evidence about block/port correspondence. Do **not** select a permanent user-facing syntax until independent mechanical-engineer readability and multi-model generation/edit studies, comment/CST policy, migrations, and unknown-version behavior close `DEC-P0-002`.

## Reproduce

```powershell
python scripts/recovery/evaluate_workflow_syntaxes.py --write-fixtures
```
