# Feature 084: bounded quality-cost evidence

Observed locally on 23 October 2026, based on source commit
`42e1edd941189e03cdf34b7de1aa7ab772e75f0a` and the recorded working-tree gate changes.
This closes the scoped baseline, selection and measurement claims for
T004/T012/T014. T013's implementation and focused proof are present; whole-gate
and integration qualification remain with T019 and the existing runbook.
No full merge gate, hosted CI, Windows runtime, push or merge was performed here.

## Change and measured result

Consolidate the local merge gate's three default-context release/native pytest
invocations into its existing coverage-bearing execution. Retain the otherwise
unique `tests/test_public_python_distribution.py` target. Ubuntu Python CI
similarly removes its repeated default-context native invocation and runs the
coverage check before the broader package suites. The Windows local wrapper
already invokes the same shell script; the Windows CI job is unchanged.

| Paired observation | Baseline stage | Consolidated stage | Saving |
| --- | ---: | ---: | ---: |
| 1 | 34.463 s | 18.457 s | 16.006 s |
| 2 | 33.895 s | 18.560 s | 15.335 s |
| 3 | 34.548 s | 18.876 s | 15.671 s |

The median stage decreased from **34.463 s to 18.560 s**, a **15.903 s (46.1%)**
reduction. This is a small, identified local stage saving, not a 46% reduction in
the complete quality process. Baseline range: 33.895–34.548 s; candidate range:
18.457–18.876 s. Three bounded repetitions characterize observed variation, not
a statistical confidence interval or a promise for another machine.

Measurements used Linux aarch64, Python 3.13.12, uv 0.9.17 and a private
`/tmp/wright084-quality-venv` synchronized from the unchanged lockfile. The normal
`uv run` environment and its existing `--with pytest-cov` overlay were preserved;
the overlay added only pytest-cov 7.1.0 and coverage 7.17.0. Downloads/setup were
completed before measurement and excluded. Both paths used identical collection,
JUnit and coverage-report observation hooks. Runs were sequential in order
B1, C1, C2, B2, B3, C3 to expose warm-cache/order effects. Concurrent feature work
was present; no claim of exclusive-machine benchmark conditions is made.

## Preserved proof

- The original commands selected 221, 163 and 364 tests: 748 invocations over
  **366 unique IDs**. The candidate selected precisely those 366 IDs once.
  Per-test source hashes, markers and fixture provenance matched, including all
  three measured repetitions. These checks ran before the gate/test edits.
- All three pairs produced identical per-test outcomes and skipped subjects.
  The candidate passed 359 tests and skipped seven. Six require Windows Job
  Objects; one requires an already-built `dist/native-candidate` wheel. These
  remain unqualified on this host; separate platform/install jobs are retained.
- Exact covered source lines matched, **2,418/2,798 = 86.4189%**. The existing
  **85% floor** and both coverage source roots remain unchanged.
- Later runtime/engineering-models and hardening contexts, isolated package
  collection, independent installed-artifact checks, OS matrices, browser tests,
  security gates and production qualification were not removed.
- A real native workflow-policy test received an isolated fixture with excessive
  `contents: write` authority. Both old and consolidated command segments failed
  that assertion and shell `-e` prevented a subsequent sentinel action. A separate
  candidate control passed its selected test but failed the unchanged 85%
  coverage floor and also stopped. These are focused failure controls, not full
  gate executions. Their durations are recorded, not compared as ordinary
  time-to-first-failure benchmarks.
- After the edits, the consolidated command passed **361 tests, seven skipped**
  with the same 86.4189% coverage. The two additional cases guard the local and
  CI target union, threshold, ordering and separation of runtime/extras contexts.
  Focused Ruff checks, formatting, shell syntax and diff whitespace checks passed.

The testing guide now points ordinary iteration at focused checks and leaves
push/merge boundaries with the authoritative runbook. No threshold, exception,
receipt reuse rule or release requirement was relaxed. Further consolidation
requires renewed equivalence evidence when environments, fixtures, markers,
source, thresholds or invocation contexts change.

## Evidence and reproduction

[Machine-readable summary](../../artifacts/first-contact/084/quality-cost/summary.json)
includes each exact command, source/lock identities, timings, negative controls
and final scoped validation. The
[raw evidence archive](../../artifacts/first-contact/084/quality-cost/raw-evidence.tar.gz)
retains collection/context manifests, JUnit reports, logs, coverage line maps and
failure-control commands. Its
[entry manifest](../../artifacts/first-contact/084/quality-cost/raw-evidence-manifest.json)
records every retained file's digest. Raw sources are stored once in the archive.

The adjacent `measure.py`, `capture_context.py`, `failure_control.py`,
`inject_policy_failure.py` and `summarize.py` are experiment drivers, not new gate
or product runtime owners. `summarize.py` verifies the retained comparison without
running tests. Reproduction requires a separately prepared environment, existing
test dependencies and fresh attempt names; `measure.py` never starts the full gate.

Setup initially failed because the default uv cache was read-only, then because
the writable cache lacked locked dependencies, and then because sandbox DNS was
unavailable. Authorized dependency download into the private environment resolved
setup. No measurement candidate failed, no required check was waived, and no
downloads were counted as a test-stage saving. User acceptance is separate.
