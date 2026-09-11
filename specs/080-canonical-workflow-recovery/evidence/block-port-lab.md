# Block and Port Treatment Laboratory

**Subject**: `port.approved-geometry-out` → `port.approved-geometry-in`
**Artifact action**: inspect `artifact.approved-geometry`
**Evidence class**: interactive expert comparison in a disposable browser concept; representative engineer study pending

## Tasks held constant

For each treatment, the evaluator must:

1. identify the connection target without prompting;
2. identify the artifact-inspection target without prompting;
3. state type, direction, requiredness, and cardinality;
4. distinguish missing, incompatible, pending, produced, failed, and stale states;
5. perform a connection without triggering artifact inspection.

## Treatments

| Treatment           | Handle                          | Artifact action                            | Result                                                                                |
| ------------------- | ------------------------------- | ------------------------------------------ | ------------------------------------------------------------------------------------- |
| A · round socket    | 22px outlined circle            | adjacent icon/label                        | familiar and compact; artifact action competes at dense scale                         |
| B · terminal block  | 30×34px square terminal         | adjacent icon/label                        | unmistakable connection metaphor; too heavy and electrical for the workflow hierarchy |
| C · hybrid terminal | 27px asymmetric outlined socket | separate `▧ Inspect` / `▧ artifact` button | clearest differentiation by shape, label, location, and hit target                    |

## Selected concept treatment

Treatment C is used on the recovery canvas. Connection remains a React Flow `Handle`; artifact inspection is a distinct button and never starts a connection. Both have independent accessible names and stable semantic selectors.

The browser acceptance test proves the pointer gesture from `port.approved-geometry-out` to `port.approved-geometry-in` creates `rel.review-to-export` and advances the semantic revision once. Artifact preview/replace and run activity leave that revision unchanged.

## Required human gate

This comparison does not claim representative usability. During the final walkthrough, an unprompted reviewer must connect the typed ports and inspect the artifact. Any hesitation, mistaken target, or misclick stops approval. The current choice remains provisional until that gate is signed off.
