# Development Push Runbook

Read this page before every push to a branch with an open pull request targeting
`dev`, and again immediately before making that pull request ready to merge.
Direct pushes to `dev` are not part of the supported development workflow.

## The 60-second pre-push check

1. Confirm the branch contains one reviewable outcome. If unrelated work is
   present, leave it unstaged or move it to another branch.
2. Review `git status --short` and `git diff --check`. Never use a broad
   `git add .` in a dirty worktree.
3. Run the native fast gate:

   ```powershell
   scripts/check-dev-push.ps1
   ```

   ```bash
   scripts/check-dev-push.sh
   ```

4. Do not push when any gate is red. Reproduce and fix the exact failure first.
5. Push one validated change set, then inspect all CI jobs before making another
   change. Do not use CI as a one-error-at-a-time discovery loop.

If a branch predates this runbook, has not had a green cumulative CI run, or
adopts a materially changed gate, run the full merge gate once before relying
on the last-pushed-tip fast baseline. This one-time bootstrap prevents an older
branch failure from hiding outside the latest incremental diff.

## Delivery-speed budget

- Local commits are cheap and may be created whenever they leave a reviewable
  checkpoint. A feature branch normally gets at most **two pushes**: one complete
  candidate and one consolidated correction after every first-cycle CI result is
  terminal and classified.
- Merge to `dev` once per independently useful customer capability. Do not use
  either feature-branch pushes or `dev` integration as an incremental debugger.
- A test-, CI-, or gate-only correction that cannot change shipped behavior runs
  the directly affected deterministic checks and one CI cycle. It does not restart
  a previously completed full local gate unless the correction changes product
  behavior, a public contract, dependency resolution, packaging output, security
  policy, or the merge gate's substantive coverage.
- After a full gate has passed on the current pushed tip, one consolidated
  Playwright test-contract correction may use the focused correction mode. It
  requires a clean worktree, exactly one descendant commit, no product changes,
  and explicit previously failing Playwright targets. The mode runs its own gate
  regression plus those exact browser tests against an isolated API. It does not
  replace pull-request CI or the full merge gate:

  ```powershell
  $env:WRIGHT_FOCUSED_CORRECTION_BASE_SHA = "<current-pushed-40-character-sha>"
  $env:WRIGHT_FOCUSED_PLAYWRIGHT_TARGETS = "tests/ui-integration/example.spec.ts:42;tests/ui-integration/other.spec.ts:88"
  scripts/check-dev-push.ps1
  ```

- Scheduler-sensitive microbenchmarks marked `performance` are trend evidence,
  not PR correctness gates. They run in the scheduled/manual performance workflow;
  deterministic functional, security, compatibility, and customer-journey tests
  remain blocking.
- A consolidated **CI-readiness correction** can retain an actual green full-gate
  receipt on the current pushed tip. Set both variables below and commit exactly
  one descendant correction in a clean worktree. The scope owner rejects product,
  dependency, packaging, publication and workflow execution changes. Workflow
  changes must consist solely of the enumerated long-path/locked-compiler setup
  steps; the complete existing test commands must remain identical. The gate
  verifies the receipt's successful exact base and unchanged log hash, runs the
  policy/scope regressions, all affected compiler tests, lint/types and strict
  docs. Full current-head PR CI remains required. This is retained qualification
  plus affected checks, not a new execution of the full gate.

  ```powershell
  $env:WRIGHT_CI_CORRECTION_BASE_SHA = "<current-pushed-40-character-sha>"
  $env:WRIGHT_CI_CORRECTION_FULL_GATE_RECEIPT = "<absolute-green-full-gate-receipt.json>"
  scripts/check-dev-push.ps1
  ```

  Missing/failed receipts, changed logs, more than one commit, dirty worktrees,
  unlisted files or broader workflow changes fail closed. Use the normal gate
  when the correction exceeds that scope; never fabricate a receipt or waive CI.
- Track pushes per feature, CI cycles, first-push green rate, runner time, local
  gate time, product-versus-infrastructure failures, and customer capabilities
  delivered. Use these measures to remove process cost, never to weaken a red
  customer, security, compatibility, or release signal.

PR #159 also exposed a gap between the separately qualified desktop prototype
and normal gate collection. Python prototype changes now select its existing owner
tests as an isolated pytest root in both native gates. These include frozen routing,
authentication, private credentials, scope, recovery, and observable evidence.
GitHub CodeQL remains the whole-program data-flow check. Its name heuristic treated
the public `remote_oauth_flow` selector as a password; the internal selector is now
named `remote_signin_mode`, while the CLI flag, serialized key, and supported values
remain unchanged. No CodeQL rule or alert is suppressed. The synthetic credential
fixture compares its exact canary with `hmac.compare_digest`; it does not store or
hash customer passwords. Collect every current-head CI result before the next push.

The same CI cycle flagged two `credential_sha256` values in desktop test evidence.
Both are verified digests of the isolated HTTPS fixture canaries, not personal
credentials. `.gitleaksignore` lists only the two exact historical finding
fingerprints (introducing commit/path/rule/line). The current receipt uses
`fixture_value_digest`. The pinned scanner was checked to discover the repository's
ignore file and still flag a neighboring key. Prototype changes and fingerprint
changes select the existing history scan in the fast gate; the full merge gate now
runs that same scan. Existing allowlist rules and their selected contracts remain
unchanged. No history rewrite or whole-file exclusion is permitted.

The OCI scanner may fail before it writes a vulnerability report. Its public
projection now includes only an allowlisted reported category (for example DB
download or registry rate limiting), retaining raw details locally. An unclassified
failure remains blocking. These categories diagnose the scanner; they do not
establish a clean inventory, authorize retries, extend DB validity or waive policy.
PR #159's initial scanner failure lacked a public cause and remains unclassified.

Linked-worktree history scans normalize only the current candidate branch and
omit unrelated tags. Every candidate ancestor, including merged branches, remains
in the scan; unpublished sibling workstreams are outside the reported HEAD scope.
A real Git regression exercises both Bash and PowerShell clone commands with a
merged ancestor, an unrelated branch/tag and a main checkout on another branch.
History-runner edits select that boundary regression and the history scan;
allowlist-rule edits retain their existing scanner contracts. PR #159's first
expanded local scan found an off-candidate fixture from a separate local branch;
that branch and finding were preserved without adding an exception.

The fast gate selects Python, frontend/browser, and documentation checks from
the changes since the branch's last pushed tip, plus staged, unstaged, and
untracked files. A new branch falls back to `origin/dev`; the full merge gate
validates the whole pull-request diff. Outside the bounded correction modes above,
gate or workflow changes run all slices.
Frontend selection also runs the MCP onboarding Chromium suite, including its
read-only live source-entry check against the gate's isolated API. This catches
accessible-control regressions that component tests and editor-only coverage miss;
it does not enable live tests globally or install an MCP provider.
When the broad `tests` target and a nested `tests/...` target are both selected,
the fast gate excludes the nested target from the broad invocation and runs it
separately. This preserves suite-local pytest imports while preventing duplicate
collection of same-named test modules.
Container and engineering-image changes also select the Docker bundle, smoke
contract, and workflow-policy tests. Pull-request CI remains authoritative for
the native amd64 and arm64 image builds that cannot be reproduced on every
developer host; both images must build and pass their exact-image smoke tests.

PR #159 exposed a bundle downgrade after the base image passed: its provider
install list pinned an older MCP SDK in the shared Hermes environment. The
Docker bundle suite now checks both Linux manifests against Wright's runtime
requirement and locked SDK version. Both native gates run that check before
dependency audits and base-image scanning. Update these pins together; do not
add an SDK conflict to the reviewed Hermes dependency exceptions. Base-image
qualification alone does not qualify the final engineering bundle.

PR #162's first OCI scan also found fixable High aiohttp findings in the Hermes
environment: `CVE-2026-111064` and `GHSA-2g87-pp6c-29x5`. The image pins the
upstream patched version 3.14.4. Both gates check the existing security-pin
contract before long checks; image smoke also verifies the actual installed
aiohttp meets that known patched floor. The isolated patch changed only aiohttp
and retained the existing strict dependency reconciliation, without new exceptions.
The earlier local scan used a valid 13:35 UTC database; CI's newer 19:08 UTC
database identified the findings. Preserve both observations and their source,
image and database identities. A prior pass does not waive a later finding, and
the explicit known floor does not replace the fresh scanner or unchanged policy.
See the upstream [resource-exhaustion advisory](https://github.com/aio-libs/aiohttp/security/advisories/GHSA-2g87-pp6c-29x5)
and [initial-timeout advisory](https://github.com/aio-libs/aiohttp/security/advisories/GHSA-5wr8-gcqf-gqf3).

On 20 October, a newly published Critical certifi advisory
([GHSA-6q48-6c7w-9gw2](https://github.com/advisories/GHSA-6q48-6c7w-9gw2))
rejected the previously qualified lock. The patched candidate uses certifi
2026.10.19 in the workspace lock, Hermes environment and pip's independently
vendored bundle/inventory. Exact-image smoke checks all three installed bundles
and confirms the affected emSign ECC Root CA - G3 is absent. Earlier passing
audits remain dated evidence; they do not waive this new finding. No dependency
audit exception is added, and live user environments are not modified by the gate.
Hermes 0.19's exact older certifi pin prevents a combined resolver install. Apply
the patch through the existing security-override stage; retain the raw pip check
and reconcile only its exact 2026.5.20-to-2026.10.19 metadata conflict alongside
the three earlier reviewed conflicts. Changed versions or extra conflicts fail.
The separate actual-bundle smoke and vulnerability policy stay mandatory.

Windows-capable jobs enable `git config --global core.longpaths true` **before**
checkout. Local long-path configuration does not qualify hosted runner setup.
Both native gates run the workspace path-security contracts before long checks.
The portable cases check equivalent Windows extended DOS/UNC spellings, exact
relative subjects, metadata denial and reparse rejection on every host. These
model cases are distinct from the Windows-only controlled parent-creation race
and the unchanged eight-writer upload test, which require native Windows CI.
Concurrent parent creation can make Python retain an extended path prefix for
a missing file. Compatibility must preserve confinement and exclusive complete
file publication; serializing the test, weakening link checks or blindly rerunning
CI does not qualify the fix. Actual Windows desktop panel/file-delivery acceptance
is also separate from the native backend suite.
Backend Python CI also installs the pinned Node toolchain and runs `npm ci`, then
checks `BuildToolchain.describe()` before tests: workspace tests exercise the real
fixed interface compiler. `validate_scoped_workflows` checks this preparation in
both gates. Fixture rendezvous must surface an already-failed task and use a
bounded wait; absent compiler dependencies must not cause an hours-long wait.

Review actual stage durations before removing tests. A previously passing full
gate can be retained for permitted corrections; rerun affected checks and full
current-head CI. Duplicate execution can be consolidated only with exact unique
coverage and equivalent environment evidence. Keep security, review authority,
engineering identity, durable recovery and installed/browser compatibility checks.
No test is obsolete merely because its feature shipped or its failure is costly.

Changes to every bound Docker input also run `scripts.release.scan_image` in the
fast gate and select OCI PR CI, including `.dockerignore`, root package files,
`src/`, the Hermes plugin, both Rivet package trees and `README.md`. The full
merge gate always runs it. Build the candidate once from a
clean Git archive, then set `WRIGHT_GATE_DOCKER_IMAGE` to that existing image
before running either gate. The helper resolves the reference to an immutable
local image ID and checks its OCI revision against the current checkout. A
metadata descendant may reuse it only when the original revision is an ancestor
and no Docker build input changed. Committed, staged and unstaged differences
are checked separately, so reverting a dirty file cannot mask a changed HEAD
or index; untracked inputs are also rejected. It never builds or publishes. For a standalone scan, use
`python -m scripts.release.scan_image --image <image>`.

The local gates and OCI PR workflow use the same pinned Trivy 0.70.0 image,
fresh vulnerability database, OS/Python/Node coverage checks and unchanged
`docker/release-policy.json` evaluator. Dependency compatibility (`pip check`)
and Wright's own dependency audit do not cover the installed Hermes/OS image
inventory: PR #121 exposed this gap when Tornado 6.5.6 passed smoke but failed
the fixable High policy. The current image pins Tornado 6.5.9 and the other
reviewed security updates in `docker/Dockerfile`; it does not run an unrestricted
OS package upgrade. The exact-image smoke also checks raw Hermes dependency
metadata and exercises JWT signing/verification with invalid-token rejection.
Missing candidate images, source mismatch, unavailable databases, malformed
reports and policy violations fail. Every reported vulnerability must have a
valid identity, installed version and exact known severity. A missing fixed
version remains a valid unfixed finding, governed by the existing policy.
Only an unavailable supported local Docker
host can produce an explicit recorded host limitation; CI never uses that opt-in.

Each scan retains its raw report/logs locally and produces a public projection
with source/image/scanner/policy/database identities, installed/fixed versions
and hashes. OCI CI uploads that projection even when policy rejects the image.
Do not upload raw image environment, history or secret matches. Use the emitted
evidence directory; an existing report directory is never overwritten.

It uses dedicated browser-test ports, so the normal Wright UI on
5173 and API on 8000 can remain running. Python checks use the cached,
Git-ignored `.venv-dev-gate` environment instead of modifying the environment
used by a running Wright process.
The full gate builds the frontend once with the developer's installed lockfile
dependencies, then reuses that fresh output for native packaging. It does not
run `npm ci` against the shared `node_modules`, so an active Wright UI cannot
lock a native Node binding that the merge gate tries to replace.
Docker, the native builder and this reused frontend build enable the canonical
workflow editor, composer, process definition view and workspace surfaces. Verify
the actual packaged workspace entry as well as the flag contracts; a source UI
with manually enabled flags is insufficient proof of the distributed UI.
The source archive selects explicit source roots so npm's local package links
cannot hide the real process-client/UI-kit directories. Archive validation checks
every declared wheel `force-include` input, and the clean-install gate rebuilds
the wheel from the source archive. A directly built wheel alone is insufficient.
Before starting its long checks, the full gate verifies that both configured
browser-test ports can actually be bound. A conflict fails immediately with
the environment-variable override instead of surfacing after the test matrix.
The fast browser slice always includes the canonical workspace-entry smoke in
addition to directly changed browser contracts; detecting one changed spec must
not silently drop that baseline. It is normally a Chromium smoke. When the changed target is
a `tests/ui-integration/workspace-surfaces/*.spec.ts` contract, the fast gate
runs that selected spec across Chromium, Firefox, WebKit, and the desktop
profile because directory, iframe, and surface interactions are
platform-sensitive. Ordinary application-source fallback remains
Chromium-only; the full merge gate retains cross-browser coverage.

Browser contracts that round-trip source through the API must derive persisted
revision and digest expectations from the host-confirmed response. Do not assert
an absolute revision computed from checkout bytes: Git line-ending conversion can
make the same fixture a semantic no-op on Linux and a byte-level change on
Windows. Wait for asynchronous digests to reach their final value before
capturing them. A focused Windows pass does not replace the Linux CI check for
these portability-sensitive contracts.


PR #163 exposed a source-display test that compared a Windows CRLF checkout
with a textarea value, which uses LF. The unchanged Robot source opened; the
display assertion failed. Both normal frontend gate slices now run the owning
cold-reconstruction suite before expensive checks, with explicit LF and CRLF
inputs for both the spacer and Robot workflows on every host. Normalize only the
expected textarea display; retain exact parser inputs, semantic round trips,
port type/ownership rejection and the no-save assertion. Do not rewrite accepted
templates, fixture hashes or runtime behavior to satisfy a display comparison.
The full frontend suites and actual Windows CI remain required.

Keep browser fixtures aligned with the current workspace journey: Workflows
explicitly creates a uniquely named empty source; Workspace Files opens an
existing source with its exact `workflowPath`. A passive link to a missing file
does not authorize creation. Mock storage must retain separate documents and
enforce each file's CAS identity, including when multiple tabs remain mounted.
Do not restore implicit example creation to satisfy an older browser fixture.

An empty Curated catalog is a valid environment result; custom onboarding tests
can select All records to prove discovery loaded without inventing a
recommendation. Common-view tests must open the accepted working tab before
leaving a local draft, keep required-answer validation blocking, and use the
current file-viewer close control. Advanced declaration JSON is an explicit
disclosure and Request input belongs to the input palette. Viewport assertions
may tolerate fractional CSS-pixel intersection rounding while still checking
the full thumbnail's bounds and exact natural dimensions.

Browser tests running against the managed frontend must send application API
requests through same-origin `/api/...` paths. Do not hard-code the default
backend port: both local gates intentionally support configurable API and UI
ports, and Vite routes same-origin requests to the selected backend.

Iframe attachment is not document readiness. Sandbox browser contracts use
locator assertions for proxy readiness and inner content before evaluating the
inner document; polling raw `frame.evaluate` during its initial navigation can
fail when Firefox destroys the initial execution context. Retain the distinct
origin, denied-network, permissions and opaque-origin assertions. Save generated
screenshots with `testInfo.outputPath` so profiles have separate evidence and a
rerun cannot replace a tracked historical review image.

Polling-recovery browser contracts control the browser clock and wait for the
specific failed refresh response before checking retained evidence. Initial or
cancelled Strict Mode requests do not prove that a refresh occurred. Keep both
last-valid evidence and no-prior-bundle assertions; do not widen their deadlines
to accommodate an unobserved poll.

Presentation tests return focus to Wright after inspecting a browser popup and
wait for the exact presentation-close acknowledgement before checking removal.
Close owned browser presentations through Wright before disposing test pages;
retain the shared-instance and application-still-running assertions.

Digest assertions over Git-managed text fixtures must likewise canonicalize
checkout CRLF to committed LF before hashing. Keep binary fixture hashing byte
exact; never apply text normalization to binary artifacts. This ensures the
Windows merge gate and Linux CI verify one recorded content identity. Pin
digest-protected repository text to `text eol=lf` in `.gitattributes`; test-side
normalization is a defensive check, not a substitute for stable checkout bytes.
The dependency `uv.lock` also uses `text eol=lf`: native packaging hashes its
actual bytes into the runtime-extra lock. A CRLF checkout would otherwise dirty
that generated lock and give Windows and Linux different dependency identities.

Accepted campaign-renewal inputs, their generated revision records and the
wall-dock R5 amendment also pin their committed LF bytes. The 30 qualified source
packs preserve their captured mixed LF/CRLF bytes with `-text`; their complete
264-file inventory retains its original hashes and lengths across platforms.
Preserve their recorded hashes; do not regenerate engineering baselines to accept
checkout conversion. Required retained-output regressions use the versioned,
byte-exact `tests/fixtures/retained-process-validation` inputs instead of requiring
a developer's Git-ignored campaign output directory. Their fixture manifest
records the original paths and hashes; no live campaign or approval is replayed.
The renewal generator retains the accepted historical manifest identities from
their immutable snapshot and verifies current semantic content before generation.
It does not recalculate past identities from a new platform's checkout encoding.

Engineering-process control-plane changes have an explicit focused route. Changes under `docs/programs/engineering-process-platform/**`, `specs/076-control-plane-validator/**`, `scripts/program_control/**`, the `scripts/validate-engineering-process-program.py` entrypoint, or `tests/program_control_plane/**` select `tests/program_control_plane`. Python source and tests also enter Ruff/format/MyPy scope. The full merge gate and Linux/Windows CI run the focused suite before broader test roots so contract failures remain attributable. On either Windows or POSIX, the repeatable focused command is:

```text
uv run --extra runtime python -m pytest -q tests/program_control_plane
```

The corresponding Ruff and format checks cover the entrypoint, package, and focused tests. No gate copies validator semantics; all invoke the same committed implementation and tests.

Changes under `scripts/program_status/implementation-dashboard/` select
`tests/program_control_plane/test_dashboard_http_boundary.py` directly in the
fast gate. These regressions cover exact static routes, trusted MIME values and
public error messages. The full gate includes them in its focused control-plane
suite. They complement the API download-header/error regressions; actual CodeQL
analysis remains CI-authoritative.

Before a program-control change can pass the fast push gate, its committed feature
state must be `PUSH_AUTHORIZATION_PENDING`, `PR_READY`, `DEV_MERGE_READY`, or
`DEV_INTEGRATED`, its mutating lease must be closed, and the authoritative
validator must pass against the exact `HEAD`. `DEV_INTEGRATED` permits bounded
maintenance after the reviewed feature is already on `dev`; the validator still
protects the reviewed product paths and limits its own maintenance exemption to
the exact gate, validator, status publisher, documentation, and regression files.
This mirrors the
non-mutating identity used by GitHub's synthetic merge checkout and prevents a
locally named implementation worktree from hiding a lease/worktree mismatch that
would fail pull-request validation.

A `BLOCKED` state may be pushed only as a bounded recovery: every changed path
must be program governance, the dev-push gate/runbook, or a test contract, the
mutating lease must remain closed, and the exact committed validator must pass.
Runtime and product paths are rejected in this state and must use the normal
reviewed lifecycle. This exception exists so a post-merge CI failure can be
recorded and corrected without fabricating a successful integration state.

EPP-N01 may use the [prospective scoped implementation delivery rule](../programs/engineering-process-platform/coordinator-state-machine.md#prospective-native-implementation-delivery-revision-98-onward).
It passes through these same states and gates with an exact-candidate independent
technical review, a closed lease, and an explicit partition of delivered and
pending tasks. Human usability, actual dev deployment, and final reporting may
remain pending without being counted as passed. This does not waive tests, CI,
independent review, security/compatibility failures, or any required merge gate;
the authoritative validator enforces the scoped record and code freshness.

The full merge gate, Linux quality job, and Windows backend job fetch or retain
full Git history because the program-control tests verify immutable historical
objects. After their focused program-control and native-runtime runs, their broad
`tests` pass excludes those two already-executed roots. The gate-policy regression
and workflow-policy test selected by the fast gate enforce these requirements so
local and CI validation do not silently fall back to duplicate pytest collection
or shallow history. Pull-request runners attach GitHub's synthetic
merge commit to the governed feature branch name locally before validation. This
preserves merge-result coverage while giving branch/worktree-bound leases an
honest checkout identity; it does not update the remote feature branch. Windows
pytest steps also enable native-command fail-fast behavior so an early failing
suite cannot be hidden by a later passing command.

Committed program-status evidence also selects the scanner-configuration and
CI-route regressions in the fast gate. The Gitleaks exception is limited to the
`generic-api-key` rule, the exact three ledger/test/packaged-status paths, and a
matched lowercase, exactly 64-hex `run_key` value; other matches on the same minified
line and other key names or paths remain scannable. When Docker is responsive,
the fast gate runs both a scanner-backed positive/negative allowlist contract
and the pinned Gitleaks history scan. It reports an explicit bounded host skip
otherwise, and GitHub security CI remains authoritative. Application and
package changes select the container smoke contract because they trigger the
OCI PR build. The current Trivy database and exact image scan remain
authoritative in CI when a local Docker host is unavailable.

## Before merge to dev

1. Fetch `origin/dev` and resolve integration drift on the feature branch.
2. Run the full gate from the operating system where the change was developed:

   ```powershell
   scripts/check-dev-merge.ps1
   ```

   ```bash
   scripts/check-dev-merge.sh
   ```

3. A skipped gate requires a written host limitation in the feature quickstart
   or pull request. A real failure cannot be documented away.
4. Make the pull request ready only after the full gate passes and every current
   required GitHub check is green.
5. Merge through the pull request. Do not push directly to `dev`.

## CI failure protocol

Engineering-image release assets use bounded retries for interrupted build-time
GET downloads and remove incomplete output on terminal failure. The Docker bundle
test, selected by the container slice of the push gate and the full merge gate,
guards this contract. This does not permit retrying workflow external actions.
The local HTTP partial-body fault probe reproduces the interrupted-transfer class;
the native image CI remains the proof for the actual publisher and architecture.

PR #133 exposed a Python dependency-audit gap: an exact-image scan does not
replace the runtime environment audit performed by public-alpha CI. The full
merge gate and Python slice of the fast gate now run
`scripts.release.audit_runtime_dependencies`, using CI's locked runtime
`pip-audit` command and the same expiring-exception policy. Missing, empty or
malformed audit reports and audit-service failures block the gate. Network
access to the advisory service is required; do not treat an unavailable audit
as a clean result. The PowerShell entry points delegate to these same gates.

The full merge gate and frontend slice of the fast gate also run
`scripts.release.audit_node_dependencies`: CI's `npm audit --json --audit-level=high`
against the workspace lockfile and the same exception policy. Empty inventories,
malformed reports, audit-service errors and unexcepted High/Critical advisories
block the gate. An exact-image scan does not replace this workspace dependency
audit. Update compatible dependencies and validate their consumers before retrying;
do not turn a patched advisory into a new exception.

Concurrency regressions must control the failing interleaving, rather than
depend on repeated lucky schedules. The metrics replay test forces competing
pre-insert reads if that unsafe pattern returns. Native API functional tests
use a bounded 15-second completion wait; the former five-second deadline was
shorter than a successful Windows CI execution and was not a performance SLA.

Provider-cancellation regressions establish that the monitor entered its actual
poll wait, then observe that cancellation woke it. Do not combine durable disk
publication, a deliberately lost observer, provider confirmation and final record
writes into a three-second wall-clock SLA. PR #158 exposed that test assumption
on Windows (3.166 seconds). Keep the wakeup deadline shorter than the 30-second
poll and retain exact durable-request, single-dispatch, provider-outcome and
uncertain-publication assertions. A suppressed wakeup signal must fail the test.
Both native gates already collect this suite; the correction changes its
controlled interleaving, not gate selection or production cancellation behavior.

Chat restoration regressions must hold the initial history response until a new
turn completes, then release that older response and verify the new messages
remain visible. PR #159 exposed initial-history delivery erasing a completed
turn on Windows. Waiting longer for the missing diagnostic does not fix that
ordering bug. Keep ordinary history restoration, reconnect and queued-turn checks;
the existing full frontend suite runs the deterministic interleaving regression.

- Collect every failed job and its first actionable error before editing.
- Let the complete CI browser run report its full failure set; do not cap the run
  after an arbitrary number of failures that forces serial discovery pushes.
- Classify the failure as product behavior, test contract, test isolation,
  platform/profile drift, packaging, or infrastructure.
- Reproduce the failing command locally or in the matching clean container.
- Long-running independent analysis may overlap deterministic local
  reproduction, but do not push a replacement commit until every job from the
  previous commit has reached a terminal state.
- After two failed pushes for the same cause, stop pushing. Build a deterministic
  reproducer and make one consolidated correction.
- When CI catches a failure class the local gate missed, update the gate and
  this runbook in the same correction.
- Never rerun a failed job without evidence that the cause is transient.

## Definition of development-ready

A change is not development-ready when the PR merely merges. The exact merged
`dev` commit must build the development image, deploy to the development
environment, pass service health checks, and pass a browser smoke covering the
changed user journey. Record the deployed commit/image digest so failures can
be rolled back without rebuilding.

## Maintainer expectations

- Keep pull requests small enough that one owner can state the user-visible
  acceptance outcome in one sentence.
- Keep frontend unit and Playwright CI independent so both report in one run.
- Keep test browser storage and ports isolated from other tests and developer
  services.
- Keep `scripts/check-dev-push.*`, `scripts/check-dev-merge.*`, and GitHub
  Actions commands aligned. The merge script remains the authoritative full
  gate; the push script is the fast feedback subset.

### Hash-bound sources outside dataset directories

Baseline and coverage generators also hash references under `specs/`. Preserve
those exact accepted bytes with explicit Git attributes; do not regenerate
accepted hashes merely to match a platform checkout. When correcting a byte
binding, compare the committed blob with its recorded hash and run baseline and
coverage reproducibility checks from a clean Git archive. A Windows worktree
pass alone can conceal Git line-ending conversion in Linux CI.


### Generated desktop panel scanner coverage

The minified `prototypes/desktop-harness/native-editor.html` is a generated
resource from `apps/web/build-native-panel.mjs`, not maintained application source.
CodeQL excludes that exact resource, as it does the existing built web/Rivet
assets. Keep the builder, native TS/TSX entry, shared components, Python MCP bridge
and backend in analysis; do not exclude the prototype directory or disable query
families. Dependency audits remain required. Changes to `.github/codeql/*` select
the gate/workflow policy checks, including the maintained-source coverage guard.
Review each finding against its original source before classifying bundle alerts;
an exclusion does not establish that a dependency is safe.

The private-LAN frontend fixture controls POSIX stat permission bits explicitly
on all platforms while retaining real token-file reads. Windows chmod does not
model GB10 permissions. Keep the production private-file rejection, forbidden
origin/peer checks, credential non-disclosure and denied-file/no-login assertions.

### Windows run-record read contention

The workspace-service suite exercises bounded retry of Windows access-denied
reads during durable-record observation, plus permanent denial and malformed
record failures. Native Windows tests hold actual exclusive file handles and
verify recovery after release and failure while a lock persists. Linux fault
injection is not native Windows qualification. Both normal Python gate slices
already collect this suite; keep the Windows backend CI tests required. These
retries only read the same exact record and never resubmit cancellation, replay
a tool or replace an unreadable record with a successful outcome.

### Late native artifact cleanup

PR #165 exposed a Windows test observing the filesystem 600 ms after the durable
timeout while a late worker was still cleaning its unindexed artifact. The
regression now holds promotion until the run actually times out, releases the
worker, and waits for that worker's completion before checking both the durable
artifact index and disk. A deliberately disabled cleanup still fails. Both
native gates run this controlled interleaving before long suites, in addition to
normal workspace coverage. Do not replace completion observation with a longer
sleep or weaken the no-leftover-artifact assertions.
