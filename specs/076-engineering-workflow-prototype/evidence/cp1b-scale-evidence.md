# CP1B scale evidence

Date: 2026-08-24

## Fixture

`createScaleWorkflow` produces deterministic 25- and 100-block workflows from
the same canonical `WorkflowPreview` model used by the drill-bit-holder example.
Each fixture spans Define, Verify, and Manufacture phases and includes three
long feedback connections. Candidate routes accept `?scale=25` and
`?scale=100`, so the same fixture can be inspected in a browser without
candidate-specific workflow data.

This is a rendering and interaction benchmark, not a claim that a 100-block
workflow is good information design. Progressive disclosure, search, and
subflows remain product requirements.

## Results

The automated interaction renders the candidate, finds the last block, selects
it, and moves keyboard focus to it. The production canvas also requests an
initial fit-to-view.

| Candidate | 25 blocks | 100 blocks | Result |
| --- | ---: | ---: | --- |
| React Flow | 399.1 ms | 548.6 ms | Pass; deterministic DOM interaction and no candidate-specific warning flood |
| Rete | 4,528.2 ms | Did not settle within the 20 s selection wait | Fail; 100-block attempt took about 57.35 s overall and emitted a large volume of React `act(...)` warnings |
| LiteGraph | Not promoted to this benchmark | Not promoted to this benchmark | Prior first pass already failed the DOM reuse, accessibility, security, bundle, and component-testability requirements |

Timings are single-run development-machine observations, not a statistically
rigorous performance study. They are sufficient for this checkpoint's much
coarser question: can the candidate support fast, deterministic incremental
tests at the target scale?

The Rete failure is intentionally recorded rather than hidden by a longer
timeout or warning suppression. Rete creates independent React rendering roots
for nodes in this integration. That can produce an attractive canvas, but it
substantially raises the cost and fragility of component tests at scale.

## Repeatable checks

```powershell
npm run test --workspace apps/web -- src/prototypes/engineering-workflow/fixtures/scale-workflows.spec.ts src/prototypes/engineering-workflow/evaluation/candidate-scale.spec.tsx
npm run test --workspace apps/web -- src/prototypes/engineering-workflow/evaluation/candidate-scale.spec.tsx --reporter=verbose --silent=false
npm run build --workspace apps/web
```

Observed after the benchmark was narrowed to the viable regression candidate:

- fixture plus scale suite: 5 tests passed in 2.61 s;
- verbose React Flow scale suite: 2 tests passed in 2.69 s;
- production build: passed;
- LiteGraph still produces its previously documented direct-`eval` build
  warning.

## Decision impact

React Flow is the provisional canvas implementation for the next prototype
increment. The canonical workflow model, engineering block components, and
route-level adapter remain independent of React Flow, so this is a bounded and
reversible choice. Rete and LiteGraph remain in the branch as measured bake-off
evidence until the deletion-cost exercise is complete.

