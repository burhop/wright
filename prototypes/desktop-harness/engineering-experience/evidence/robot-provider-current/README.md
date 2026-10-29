# Current Robot provider qualification

29 October 2026. **PASS at the direct provider boundary only.**

The pinned, separately built ROSBag provider and existing offline operations ran
all three original copied datasets in a network-disabled, read-only-root ARM64
container. Five-topic extraction retained 61/61/56 external observations; each
case preserved its one event. Independent metrics met the unchanged 1% tolerance;
event timing differences were zero. Case 03 retained the 13.5–16.5 s missing interval.
The receipt records exact outputs and image identity. No physical robot was used.

This prerequisite does not establish canonical desktop workflow execution,
Wright gateway registration, human review, rerun/recovery, or Windows acceptance.
Those remain required regression work. Raw evidence and reproducible build/probe
inputs are preserved privately under
`.local-run/experience-review/candidate-036/robot-provider-{build,proof}-01/`.
Use the existing ROSBag usage guide and original workflow requirements.
