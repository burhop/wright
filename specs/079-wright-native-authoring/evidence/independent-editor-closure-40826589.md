# Independent closure of product editor findings

Correction reviewed: `408265893180aac3987dd40185c8f87dfb99f4b2`.
Correction tree: `2bf42663a85b6b48497e74b324f1b6d6a84adaa0`.
Parent integration identity reported separately: `572a5802838a33bc887f00edc456ef7a6d6ead23` (the independent replay below used the writer's exact correction).

CR-NATIVE-01 and CR-NATIVE-02 from the independent `997e5610` product review are **closed** for this correction.

Independently replayed the original Node model probes against the actual corrected TypeScript in this detached review checkout. The invalid `../outside.txt` edit now throws, preserving `safe.txt` in the last valid definition. A second producer on a many-valued draft input now throws, preserving its first edge. All 60 title edits are retained and all 60 undo operations return to `Untitled process`; the original candidate had retained only 50 and stopped at `Edit 10`. Added explicit assertions for those retained-history observations to the independently authored probe.

Inspected the new source and focused component regressions: the semantic path rule mirrors the backend path invariant; the producer rule is unconditional; the shared history limit is 100; the editor displays that limit, discarded-history behavior and live Undo/Redo counts, and exposes the explanation as the controls' accessible description. The invalid-path component regression checks source remains unchanged, save remains disabled, invalid text survives step selection, correction forms one undo unit, and Undo restores the prior valid path. The separate model regression covers the 100-command boundary and branching after undo.

No additional corrective finding arose from this small diff. The writer's reported 61 focused frontend checks and 21 authoritative path-vector checks were not repeated or relabeled as this reviewer's runs. Full candidate browser/build gates, governance findings and final independent record remain separate pending work.
