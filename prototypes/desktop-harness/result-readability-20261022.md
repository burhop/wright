# Result readability follow-up

Base: `3a77e1b4ac9d9db06fe3b086fb4ffa3a319e44e5` (current remote dev).
Branch: `codex/desktop-result-readability`.

The user opens a workflow, selects its recorded run, and inspects its results.
Some common-view headings currently repeat a complete artifact path, including a
run ID. Use the filename when the recorded title is exactly one of that result's
representation paths. Preserve meaningful titles, including titles containing a
slash. Keep the original path in File details and the heading tooltip.

Reuse the shared ResultCard in `@wright/ui-kit`, the existing scoped process
client and representation reader, and the native navigation acceptance harness.
The backend continues to own source/run/result identity, permissions, currentness,
validation and recovery. This presentation change creates no new schema, executor,
saved UI compatibility version or invalidation. Existing saved custom UI bundles
retain their builds; the common view remains the fallback.

Tasks:
- [x] Reconcile current remote dev and Windows follow-up; preserve prior work.
- [x] Reproduce the heading problem and correct the shared presentation.
- [x] Verify filename headings, meaningful titles, duplicate filenames and exact
      representation/navigation identities using the existing component suite.
- [x] Build and inspect the served desktop panel with a retained run; verify
      preview, producer navigation, reopen and narrow layout without execution.
- [x] Exercise the normal workspace entry/editor and a different existing
      workflow using the established acceptance harness.
- [ ] Record source/build/evidence identities, run appropriate repository gates,
      and prepare the next integration candidate without repeated unchanged runs.

Windows boundaries: PR165 routing/restart repairs and PR167 research fixes are
already integrated. Latest Windows reports (PR165 comments6307620020 and6308007167)
identify an engineering helper correction and request no further integration fix.
Exact PR167 optional-research acceptance and desktop0.19 observation are still
unproven. The independently active Windows engineering goal owns its own work;
this UI follow-up does not authorize a Roadster run or alter its requirements.

Evidence and limitations will be appended after verification. Rendered local host
simulation is distinct from observation of the actual Windows desktop panel.

Verification: 216 component checks, TypeScript, changed-test ESLint, eleven served
Workflows/editor authoring cases and both native navigation journeys pass. The
retained PNG checksum and all35 original retained file hashes are unchanged.
[Evidence index](evidence/result-readability-20261022/qualification.json) records
rendered screenshots and exact verification boundaries. Full repository gates,
publication and actual Windows observation remain pending.

## Required dependency correction

The first full gate stopped on CVE-2026-114603 in the old OpenTelemetry1.42.1
lock. The subsequent Node preflight also rejected DOMPurify3.4.14 for
GHSA-cg2g-xh64-v4q7 and GHSA-mrv2-3pqr-j5jr. Their upstream fixed releases are
OpenTelemetry1.45.1 and DOMPurify3.4.17; the evidence index links the official
advisories. Raise the existing package floors and resolve only the affected
families. Keep the audit policy and existing exceptions unchanged.

Both corrected audits pass. Nine existing tracing/correlation tests and167
sanitizer/result/common-view checks pass. A bounded actual TraceState parser
probe rejects100,000 spaces in under two seconds. This is a dependency control,
not evidence of workflow execution. The native panel rebuild is byte-identical,
so the existing rendered native screenshots remain applicable. Full current-head
repository gates and exact-image installed smoke remain required. Existing live
prototype packages and user configuration have not been updated.
