# Candidate 037 gate checkpoint

Source tested: `55ef86fe2936b182a9052d128e0f3f9e96925a05`.
Exact ARM64 image: `wright-desktop-gate:55ef86fe`, image ID
`sha256:6c854afb5420212596a2d33194b2358073889b3128c3fcf2e4920e04f3fc5d1f`.

The full local gate stopped at the history secret scan after scanning 1,728
commits. Two findings are the SHA-256 of `{}` in the Robot provider setup receipt,
not credentials. The API computes this field from boolean credential configuration
status in `apps/api/src/api/services/mcp_services.py`. Both introducing-commit
lines were checked against the independently computed empty-map hash.

Only the two exact commit/path/rule/line fingerprints were added to
`.gitleaksignore`. No history or receipt was rewritten, and no path/rule was
excluded. The pinned scanner synthetic control passed: one finding before the
exception, zero afterward, and a neighboring synthetic key still detected.
See [control](fingerprint-control.json). A full history rerun is still required.

Private logs: `.local-run/experience-review/candidate-037/gates/`.
The full gate is NOT yet a pass. Supported browser projects are being qualified
separately; WebKit lacks host libraries. Actual Windows acceptance is unverified.
