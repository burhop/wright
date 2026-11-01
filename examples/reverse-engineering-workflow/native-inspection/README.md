# Independently inspect an existing CAD export

This reusable segment takes an exact supplied STEP, runs the qualified independent
AgentCAD native measurement tool, and validates its unchanged JSON response with
Wright's existing process validator. A measured defect is retained and holds the
revision. A passing report releases only the checks in its pinned profile.

`build_workflow.py` authors ordinary source using discovered tool metadata, a
workspace-relative STEP input and explicit profile/baseline references. It has no
executor, provider transport, model call or private run-state authority. Use the
existing Workflows editor and common working view. Closing a view does not cancel
or restart the backend run. No new UI contract or client is introduced.

The `structured-json-container@1` reader selects one explicitly configured
JSON-encoded string, for example `/content/0/text`, then observes declared fields
such as `/metrics/volume`. It strictly parses both documents and preserves the
outer artifact's hash and both selectors in evidence. It does not infer which
message to trust, rewrite measurements, execute embedded content or treat a
provider's success flag as proof of geometry. Profiles must check the relevant
actual measurements and failure indicators.

Windows pilot qualification on 28 October 2026 used the preserved pocket STEP
revisions 1 and 2. The same six-check synthetic regression profile measured
5952 mm³ for the defective revision and held it against the exact rectangular
fixture expectation of 5808 mm³. The corrected revision measured 5808 mm³ and
passed. The input files were not rebuilt or edited. These are arithmetic controls
for the known fixture, not newly supplied Roadster tolerances or proof that volume
alone establishes pocket shape/depth. The complete original engineering checks
remain separate.

Evidence is retained in the private Windows pilot state under
`research/20261020-roadster-goal/connected-native-inspection-1913/`, with canonical
runs `a683ea13030244d2ad018f7c4b0ac369` and
`b20c0c11829e4218831913c971345560`. All model and human-review authority stays with
the existing runtime. No model call was needed for these configured operations.

This is an implemented inspection segment of the general photo-to-CAD workflow.
The supplied STEP is explicit preparation. Automatic SteveCAD export transfer,
the complete connected authoring/correction chain, durable resume qualification,
workspace browser acceptance and portable bundle qualification remain open.
Do not present this segment as a completed general reverse-engineering process.

`validation_reference(...)` now resolves the parsed profile and baseline through
the existing core canonical digest function. These semantic identities differ
from a pretty-printed JSON file's byte hash. It confines the profile path and
requires every subject role; runtime readiness remains authoritative. An initial
forward-body declaration using byte hashes was held before any tool dispatch.
The corrected declaration used the same STEP and profile without relaxing checks.

Fresh Windows run `75813056335b4600be2f11749f017b0e` used this same segment on a
separate Roadster forward print component: AgentCAD measured one closed valid
114-face solid, and Wright passed seven explicit native structure checks. The
exact STEP SHA256 is
`c03543d527ab7d6399a8cbce3be823101359abeaab03acee70ba5366cf0344d4`.
Assessment `3296785b99d74eeabb2949e62d80ef93` covers those checks only. Separate
STL intersection checks failed, so it establishes neither print readiness nor a
completed Roadster. Source/native report/assessment receipts remain in private
pilot evidence under `forward-native-inspection-2038/` and the canonical run.

Selected native tools must be installed and qualified before execution. A missing
reader/provider, schema drift, missing input or stale profile holds dependent
work. A changed STEP, tool definition or profile requires fresh dependent results;
an older passing assessment cannot release a new artifact. Portable use must carry
the referenced profile/baseline and required assets, map provider bindings through
the registry and transfer no credentials, live runs or previous approvals.
