# CP2 engineer-comprehension comparison

This is a repeatable formative review instrument, not a completed study and
not evidence that CP2 has passed. Do not enter invented participants, answers,
or timing data.

## Hypothesis and gates

Mechanical engineers can understand the drill-bit-holder workflow materially
faster in the prototype than in the current Rivet presentation.

The CP2 gate passes only when:

1. at least five participants complete both surfaces without coaching;
2. at least 80% correctly identify all six scored concepts in the prototype;
3. prototype median comprehension time is at least 30% lower than the current
   Rivet baseline; and
4. the moderator confirms that both surfaces contained equivalent workflow
   information.

`usability-metrics.ts` calculates these thresholds from paired trial records.

## Required materials

- Prototype: `/prototype/engineering-workflow` at a 1680 by 950 viewport.
- Rivet baseline: the current Wright-embedded Rivet editor showing the same
  drill-bit-holder blocks, labels, connections, and inspector information.
- A timer visible only to the moderator.
- One answer sheet per surface and participant.
- The scoring key below, hidden from participants.

The repository does not currently contain an equivalent drill-bit-holder Rivet
project. Until that exact baseline is captured, timing comparison is **pending**.
Do not substitute a smaller or differently structured Rivet example; it would
make the 30% comparison invalid. Preparing equivalent content in Rivet is
baseline setup, not authorization to modify or migrate production Rivet code.

## Participants and order

Use five or more mechanical engineers or closely adjacent product-development
engineers who did not implement this prototype. Record role and relevant graph
editor familiarity, but no sensitive personal information.

Use a within-participant comparison and counterbalance learning effects:

- odd participant IDs: Rivet first, prototype second;
- even participant IDs: prototype first, Rivet second.

Reset pan, zoom, selection, inspector tab, and phase focus before every trial.
Give a neutral two-minute break between surfaces. Do not discuss answers during
the break.

## Moderator script

Read this verbatim before each surface:

> This canvas describes designing, verifying, and sourcing a sheet-metal
> drill-bit holder. Without running or editing it, answer six questions from
> what you see. You may pan, zoom, select blocks, change phase focus, and inspect
> Details or Evidence. I cannot explain the diagram while the timer is running.
> Tell me when you are finished.

Start the timer when the fully loaded, reset canvas becomes visible. Stop when
the participant says they are finished or after eight minutes. Record an answer
as observed; do not reinterpret it after showing the other surface.

Ask in this order:

1. What are the major phases, in order, and what does each accomplish?
2. What information starts the design-definition work?
3. Which steps use an external engineering or business tool, and how can you
   distinguish those actions from AI tasks and documents?
4. Where does a person or rule decide whether work may proceed?
5. If a check or approval fails, where does the work return for revision?
6. What reviewable artifacts are produced before supplier handoff, and what is
   the final approved handoff?

If the participant asks what a color, line, acronym, or block means, respond:
“Please answer from what the interface communicates.” Mark `coached: true` only
if the moderator accidentally supplies explanatory information. A coached
trial is excluded and must be rerun after a reset.

## Exact scoring key

Score each concept true only when the minimum answer is present:

| Concept        | Minimum correct answer                                                                                                                                                                                                                       |
| -------------- | -------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `phases`       | Define, Verify, Manufacture in order, with a materially correct purpose for each.                                                                                                                                                            |
| `inputs`       | Reference Images, Design Input, and Knowledge Lookup feed the specification; the FEA Test Definition and Fabrication Request are later inputs.                                                                                               |
| `toolActions`  | Identifies generic MCP/action blocks such as Bound MCP Tool, Run Bound MCP Tool, Create Flat Pattern, and Send to Selected Supplier, and distinguishes them from purple AI tasks and green artifacts using label/icon/badge—not color alone. |
| `reviewGates`  | Identifies Design brief accepted, Design Oracle, Meets criteria, and Designer Approval as proceed/revise decisions.                                                                                                                          |
| `feedbackPath` | Describes at least the failed verification return to design revision and recognizes dashed revise/reject connections as feedback rather than the forward path.                                                                               |
| `artifacts`    | Identifies Design Specification, Parametric Model/STEP, Analysis Results, DXF Flat Pattern, 2D Drawing/RFQ, Supplier Quote, and the approved Notify & Hand Off outcome.                                                                      |

The strict participant pass is all six concepts true. Preserve raw wording in
notes so disagreements can be reviewed without changing the scoring rule.

## Trial record

Record one object per surface. Use opaque participant IDs only.

```ts
{
  participantId: "P1",
  surface: "rivet", // or "prototype"
  sequence: 1, // 1 or 2 for this participant
  elapsedSeconds: 143.2,
  coached: false,
  correct: {
    phases: true,
    inputs: true,
    toolActions: false,
    reviewGates: true,
    feedbackPath: false,
    artifacts: true,
  },
}
```

Keep separate notes for raw answers, observed confusion, viewport, build/commit,
and any setup deviation. Do not put those free-text notes into the metrics
calculator.

## Report all results

Report, even when the gate fails:

- paired participant count and surface order split;
- median seconds for each surface and relative improvement;
- fully correct count/rate for each surface;
- per-concept correct rates;
- coached/excluded trials and deviations;
- three most common points of confusion;
- participant suggestions, separated from moderator inferences; and
- a `continue`, `change`, `stop`, or `defer` recommendation.

A formative result from the product owner alone is useful directional feedback
but cannot be presented as the five-participant CP2 exit gate.
