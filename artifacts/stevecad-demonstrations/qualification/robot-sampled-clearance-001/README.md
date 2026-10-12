# Robot revision 7: independent sampled clearance

The passive audit of the exact saved STEP completed in **583.623 seconds**.
It maps all 110 imported solids uniquely to native world bounds and volumes,
then evaluates the 28 printed instances using the saved native joint tree,
axis lines, couplings and linear animation keys.

- 5 named poses plus 33 samples over 8 seconds.
- 378 printed-part pairs per state: 353 non-seat pairs and 25 declared seats.
- 14,364 pair evaluations, with **0.400 mm minimum non-seat distance**.
- Zero measured overlap; no gap violations at the declared kernel precision.

`sampled-clearance.json` contains every measured pair, pose values, input hashes,
source hash, numeric tolerances and selected reader version. `audit.py` is the
exact executed source. `execution-environment.json` records the isolated offline
container and the post-run input/source hash checks. The script takes the saved
revision-7 media directory as its first argument and a fresh output directory as
its second. It refuses an existing result; keep previous evidence.

Open [the illustrated report](review.html) or [its PNG](sampled-clearance-review.png).
The browser check verifies all 33 sample cells and the native image load, without
horizontal overflow. The PNG was also visually reviewed. Presentation helpers
are retained for reproduction; their relative repository paths reflect the
original execution location under `.local-run/`.

This is an independent standard-format measurement in the existing selected CAD
library environment, **not an AgentCAD MCP call or a replacement Wright runner**.
It adds the missing sampled minimum-distance evidence to original R08, whose
recorded UNVERIFIED verdict remains unchanged. Continuous trajectory coverage,
other joint combinations, fastener-stack review, physical print/fit, strength
and powered operation are separate. No CAD was edited and no media was published.
