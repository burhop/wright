# Heat native execution and result inspection

Heat case01 attempt005, run `8cc25ce72af6421488b9f6fc2ecdb79f`, completed the
actual OASiS conduction operation but failed its model task afterward. The
provider returned four VTU paths while the operation also produced four CSVs
and three JSON reports. The OASiS-only task had no workspace file reader and
correctly refused to invent evidence or rerun a successful solve.

Fresh attempt006 definitions add one generic direct MCP execution step,
`execute_recorded_fe_call`, pinned to the actual OASiS tool name/schema. Its
arguments come through a canonical connection from the immutable uploaded
`exact-solver-call.json`. The direct step declares all actual native output
paths: 11 for case01's two candidates, 15 each for cases02/03's three candidates.
The existing runtime checks their presence and records hashes after that call.
The numerical operation source and `critic_approved=false` remain unchanged.

The original `solve_and_verify` task retains its semantic ID and original
connections. It now uses the confined workspace inspector to read all three
actual JSON reports with bounded paging and obtain metadata for every raw VTU
and CSV. Its report preserves the original two-percent analytical agreement and
mesh checks, one-percent heat balance, declared maximum temperature requirement,
candidate decision and all observed failures/limitations. It explicitly retains
the provider's unverified/pending-independent-critic warning. No OASiS-verified,
physical qualification or separate campaign correctness claim is permitted.

All three normal API-created attempt006 instances are saved and enrolled at
`.local-run/feature-081-live/campaign-execution/heat-attempt-006.json`.
The companion staging-verification JSON records current tool pins, complete
input maps, exact source/dataset/grant identities, original stages/edges and
absence of all declared CAD/solver outputs. Only native init CLI operations ran
in their three private project directories; no CAD or solver was dispatched.
Existing attempts and grants remain unchanged.

Twenty-three focused canonical-preparer and input-binding tests passed, including
exact runtime extraction of the connected JSON arguments and preserved critic
setting, original edges, full candidate-dependent file declarations and the
separate final inspection. Ruff passed. This source-only correction needs no
API/Hermes restart and changes no campaign execution counters.
