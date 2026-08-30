# PROD-02 Preregistered Moderated Study

## Claim and comparator

The read-only Wright view lets engineers understand one exact process faster than formatted canonical JSON alone without reducing correctness.

The immutable subject is `product-definition-v1.sample.json`, content identity `4617a8a6424b7c15712cd951c0b97a8c4ec5e77e29633e46e105d30ec65d5883`. The comparator is that exact JSON pretty-printed with no annotations; the treatment is the exact candidate browser view of the same bytes.

## Independent sample and ordering

- Five engineering/engineering-software participants who did not author EPP-F02 implementation or fixtures.
- Counterbalanced within-participant order: three comparator-first and two treatment-first, frozen before sessions.
- Assignment is fixed before recruitment by participant slot: slots 1, 3, and 5 comparator-first; slots 2 and 4 treatment-first. Replacements inherit the vacated slot.
- One script; facilitator reads only the frozen prompts and does not explain semantics after timing starts.

## Frozen tasks

1. List the three phase IDs and the four action IDs in execution order. Answer key: `understand-needs`/`capture-requirements`; `define-and-review`/`define-product`, `review-product-definition`; `release-definition`/`release-product-definition`.
2. For every action, list each input port, output port, and expected artifact. Answer key: `capture-requirements` → input `customer-needs`, output `requirements-baseline`, artifact `requirements-specification`; `define-product` → input `requirements-input`, output `product-model`, artifact `product-definition`; `review-product-definition` → input `model-review-input`, output `review-decision`, artifact `definition-review-record`; `release-product-definition` → inputs `approved-model-input` and `approval-input`, output `released-package`, artifact `released-definition-package`. The input/output classification is part of the answer.
3. Name the gate ID, pass target, fail target, and feedback ID. Answer key: `definition-approval`, `release-product-definition`, `define-product`, `revise-definition`.
4. Locate `capture-requirements`, `definition-approval`, and `released-definition-package` in both text and diagram and report each ID exactly.
5. Answer two yes/no questions: “Does this view prove a process ran?” and “Does it prove an expected artifact exists?” Answer key: no/no.
6. Treatment only: recover from each of the three exact states frozen in `recovery-fixtures.json`: missing/unavailable definition, invalid definition, and unsupported version. This task is scored separately and is excluded from the speed comparison. The candidate must reproduce the manifest's exact request/payload SHA-256 identities and expected diagnostic classes; a mismatch invalidates the session.

For tasks 1–5, timing starts after the exact prompt is read and the assigned surface is visible; it stops when the participant submits a final answer or at 10 minutes. Correctness is one point per required atomic answer (29 total): task 1 has 7, task 2 has 13, task 3 has 4, task 4 has 3, and task 5 has 2. The same rubric scores both surfaces. A missing atomic answer or wrong port direction is incorrect. The comprehension score is correct points divided by 29.

## Pass thresholds

- At least 4/5 complete every core treatment task correctly.
- Treatment median is no more than 3 minutes and at least 25% faster than comparator with no lower correctness.
- No participant makes more than one identity-mapping error.
- At least 4/5 score at least 80% on frozen comprehension questions.
- 5/5 recover from all three frozen states—missing/unavailable, invalid, and unsupported version—without facilitator instruction or mutation.
- Zero serious/critical automated accessibility findings; keyboard-only completion; complete content at 200% zoom and 320 CSS-pixel width; non-color cues; reduced motion.

The speed claim compares only tasks 1–5 and uses each participant's total elapsed time per surface. Sessions are rejected before analysis only for wrong fixture/candidate identity, facilitator coaching after timing starts, recording/timer failure, duplicate participant, participant implementation involvement, or failure to attempt both tasks 1–5 surfaces. An abandoned or timed-out surface is retained as 600 seconds with unanswered items incorrect; it is not silently excluded. Task 6 recovery, cancel, reconnect, and stale-source behavior are not applicable to the JSON comparator and do not enter the speed statistic.

## Evidence and stop rule

Record participant role class, all three recovery-fixture digests, the immutable subject digest, order, outcomes, errors, elapsed time, recovery, accessibility results, and candidate commit. Do not tune tasks, thresholds, or exclusions after seeing results. A miss blocks the product-readiness claim but never changes benchmark qualification.
