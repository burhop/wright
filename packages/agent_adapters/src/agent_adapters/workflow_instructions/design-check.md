Return JSON with verdict (pass, revise, or needs_input), checks (a nonempty array
of objects with requirement, expected, observed, status (pass/fail/unverified),
and evidence (a nonempty array of successful tool-call numbers)), and corrections
(an array of concrete corrections or missing decisions). Pass requires every
check to pass and no corrections. Revise requires at least one failed check
with successful tool-call evidence and concrete corrections. It may retain
unverified checks: preserve each unknown and its missing evidence or decision
alongside the measured failures. Revision authorizes only the configured bounded
correction attempt, not acceptance or downstream release. With no evidenced
failure to correct, return needs_input for unresolved requirements or evidence.
Never turn absent measurements, unknown requirements, or unavailable capability
into a passing check. Inspect without changing the supplied model.
Use the datum definitions required by the specification. For physical or virtual
datums, establish their mapping to observed geometry; do not invent a requirement
for named native PMI or annotations unless the specification requests them.
