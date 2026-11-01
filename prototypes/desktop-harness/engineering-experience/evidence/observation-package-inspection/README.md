# Recorded observation → passive manufacturing inspection

The existing passive inspector now supports the explicit recorded-observation
response contract. It selects an exact server/tool/schema/full-arguments identity,
requires a unique successful attempt and complete unredacted evidence, checks its
projection digest and call ordering, then applies the existing success/path,
package, profile, toolpath and native-preview checks. Selected call identity is
retained alongside the whole response-file hash. No executor or provider was added.

Tests cover both existing response forms, the new producer projection through the
actual inspector, two-orientation selection, incorrect/missing identities,
boolean-versus-integer arguments, duplicate attempts, failure, warnings, incomplete
and redacted records. Every rejected input leaves the output directory empty.
These are controlled fixture tests, not engineering qualification.

A fresh-copy offline check also uses the retained real 10 × 8 × 6 mm repaired
coupon response and 3MF. Native PNG and passive toolpaths pass. Every original
retained file hash is unchanged. See retained-report.json and replay_retained.py.
The old direct-gateway probe did not capture a canonical task schema digest, so
this compatibility test explicitly uses a synthetic selector identity. It is not
a reconstructed historical run, fresh provider operation, canonical workflow
proof, handle study, strength acceptance or Windows acceptance.

Private fresh-copy outputs:
.local-run/experience-review/observation-inspection/retained-01/.
Candidate accepted revision 6, installed plugin, original CAD and engineering
runs are unchanged. The source/runtime binding and full handle journey remain
open in docs/design/codex-engineering-experience-plan.md.

Independent review identified Python boolean/integer equality in supplementary
and expected response fields. The regression reproduced it, including the
producer's duplicate-text suppression. All three comparisons now use typed JSON
identity. Failed/intermediate logs are preserved; pytest-final.txt records the
final 176 passing affected checks. Ruff and diff checks pass.
