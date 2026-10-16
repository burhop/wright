# Next bounded demo slice: retrieve engineering files

Initial investigation, 15 October 2026. Superseded by the implementation checkpoint below; not installed.

Current status, 16 October: the patched 0.14.0 prototype is installed and locally
qualified. PR159 is under qualification; Windows native download acceptance and
complete engineering demonstrations remain outstanding. Earlier dated entries
below describe historical states, not the current installation.

The goal requires inspecting and retrieving real engineering deliverables. Native
Files currently offers metadata and 64 KiB text previews; STEP, meshes and PDFs
have no download control. Definition export in PR158 does not close this gap.

Reuse `WorkspaceFileUseCases.read_bytes(workspace_dir, path, maximum_bytes=...)`
in `packages/workspace_service/src/workspace_service/use_cases/files.py`. It
already owns bounded binary/text reads through the workspace path resolver and
bounded executor. Do not add another file service or arbitrary filesystem proxy.
The ordinary API `/api/workspace/files/content` returns binary FileResponse but
text JSON; it is not itself a uniform byte-download contract.

Proposed minimal follow-on after the current candidate is isolated: one app-only
native download port, exact workspace/session/path, explicit finite payload limit,
bytes plus SHA-256 and safe basename. Reuse existing native transport and local
Blob download pattern. Validate response identity, size and computed digest before
creating a download. Download as attachment; do not execute or inline arbitrary
HTML/SVG. Clear old preview state on file/workspace changes and discard late replies.
Use the existing owner scope and protected-path policies; inspect those policies
before implementation, including hidden/private state and symlink/reparse rejection.
Do not assume UI-only tool metadata grants authority.

Label this as the current saved file, distinct from exact recorded run evidence.
Run artifacts retain their owning digest/review checks. Never call a browser
request a confirmed Windows download. Unsupported/oversized files need a clear
reason; do not silently truncate or substitute another route.

Qualification: actual scoped owner bytes for existing retained CAD and a
substantially different Robot diagnostic artifact, exact hashes, denied traversal,
symlink/cross-session/private paths, malformed/oversized replies, workspace change
during read, and actual browser attachment. Retained files prove transport only,
not new engineering output. Windows native delivery remains a separate user test.
No provider/auth/grant change is needed or implied by this slice. Full SteveCAD,
Robot and manufacturing demonstrations remain required.

## Baseline and inspected access boundaries

Branch `codex/desktop-file-download` starts at `0da734d0`, currently PR158's
unmerged head. Reconcile with integrated dev before delivery. No existing
worktree, installed plugin, state, run or configuration was changed.

`WorkspacePath.resolve` rejects traversal, absolute/drive/UNC paths, ADS,
symlinks and reparse points. It does not reject dot paths. The current file tree
hides dot entries and `freecad_mcp_work`; this is presentation filtering, not
download authorization. The new port must reject hidden/private/reserved paths
explicitly before reading, keeping advertised file visibility and access aligned.
Only explicit UI requests may download current workspace files; model tools
receive no new file-read capability. Run artifact evidence keeps its own owner.

Tasks: inspect current required guidance and existing tests; implement the one
bounded UI port and Download control; prove byte/scoping/error/race contracts;
exercise actual MCP and browser on retained CAD/Robot files with honest labels;
reconcile dev and use repository gates; qualify named candidate before any
installation; retain actual Windows delivery as a separate acceptance check.

Evidence index: `/tmp/wright-desktop-file-download-evidence-20261015/`.
No current implementation or download qualification is claimed.

## Local implementation checkpoint — 15 October 2026

Implemented one app-only read port and a Download file control in the existing
Files preview. The port reuses the bounded file owner with a 16 MiB limit and
checks workspace/session and visible relative paths. The client checks scope,
size, basename and SHA-256 before requesting an attachment; closing the keyed
file view discards late replies. No run, review, provider or model authority changes.

Verification: 34 backend discovery/download checks, 26 focused UI checks,
TypeScript and lint pass. The same 26 UI checks pass after isolated `npm ci`;
Wright's Node dependency audit passes. Original dependency-setup, outdated-copy
test and sandbox AnyIO stall attempts are retained. The identical stalled test
and complete affected suite pass outside the sandbox.

Actual MCP and browser downloads preserve unchanged retained heat-spreader STEP
and Robot Tracking telemetry bytes. Hidden/traversal/symlink/oversized/wrong-session
requests are denied. Empty and 16 MiB synthetic files also pass actual MCP byte
verification. These are transport proofs, not new engineering outputs or runs.
A browser fixture's missing UTF-8 header was corrected after screenshot review;
both captures are retained. The rebuilt native resource has no external assets.

Evidence: `mcp-proof.json`, `mcp-boundary-proof.json`,
`browser-1792069211887/report.json`, `implementation-checkpoint.json` and
`social-preview.md` under the external evidence directory above. No content was
published. Actual Windows download delivery remains unverified.

Remaining: reconcile integrated dev, repository gates and full shared UI
regression, named-candidate package qualification/rollback before installation,
and Windows acceptance. PR158's current-head Windows backend CI is still running.
Full SteveCAD, Robot and manufacturing process acceptance remains incomplete.

## Integration checkpoint — 16 October 2026

PR158 merged to dev at `bcb5b52f1f7169eb0b5b71bc1a1ef704b6911a94` after
all current CI checks passed (28 successes and one intentional skip). This branch
was rebased onto that merge; its exact Git tree remained unchanged from the
qualified download head `74584fed`. The full local merge gate passed, including
1,921 frontend tests. Local full Playwright was explicitly skipped for the
retained GB10 WebKit limitation; separate actual Chromium/MCP download proofs
and hosted browser CI remain required. Generated build files were preserved
before restoring only those files. Normal push checks and PR CI remain pending.

Candidate 0.14.0 is prepared, not installed. Its exact packaged command serves
41 tools and the recorded native resource; actual MCP and simulated-host Chromium
downloads preserve both retained engineering files. Candidate service state is
isolated from installed 0.13.0. No new engineering output, Windows acceptance,
SteveCAD authentication, model routing change or tool grant is claimed.

Evidence under `/tmp/wright-desktop-file-download-evidence-20261015/`:
`merge-74584fed-receipt.json`, `dev-reconciliation.json`,
`candidate-014-preparation.json`, `download-source-review.json`,
`native-014-update.md` and `desktop-014-walkthrough.md`.

## Security gate correction — 16 October 2026

The normal push gate at `e19c48ff` stopped before its test stages because the
current dependency audit reported CVE-2026-59951 in locked MCP1.28.1. The previous
full gate is retained as historical evidence, not current dependency qualification.
Upstream fixes this stateful Streamable HTTP session-retention issue in1.30.0
on the1.x line: https://github.com/modelcontextprotocol/python-sdk/security/advisories/GHSA-84m7-p3x7-pcfv.

Both existing MCP requirements now require at least1.30.0 and retain the<2 bound.
The locked resolver changed only MCP to1.30.0; the existing native build helper
regenerated the runtime extra lock. A fresh isolated environment passes the
unchanged dependency audit with no findings. No exception was added. All769 gateway and
desktop compatibility checks passed; new full/push gates and a rebuilt
candidate are required. The previously prepared0.14 package must not be installed.
Installed0.13 and live services have not been changed.

Evidence: `push-e19c48ff-receipt.json`, `security-audit-followup.json`,
`mcp-130-lock.log`, `mcp-130-sync.log`, `mcp-130-audit.log` and
`mcp-130-compatibility.log` in the existing external evidence directory.

## Patched installation and engineering-image correction — 16 October 2026

Head `83c2ca70` passed full local merge and normal push gates with MCP1.30.0.
The full browser limitation remains explicit; separate Chromium checks passed.
The named plugin was updated to the independently qualified patched 0.14.0
package with exact configuration/cache backup and scoped rollback. Its installed
command serves 41 tools and the expected native resource. Actual MCP and
simulated-host Chromium proofs preserve the retained STEP and Robot CSV bytes;
actual Windows download acceptance remains pending. No engineering run, provider
grant or authentication was introduced. A fresh SteveCAD workspace holds the
unchanged original workflow and reports missing provider tools before start.

PR159's first CI cycle exposed both engineering manifests downgrading the shared
MCP SDK to1.28.1 after the base image passed. Disposable containers reproduced
the fourth dependency conflict. Both manifests now pin1.30.0; the unchanged
reconciler accepts only the three previously reviewed Hermes conflicts. A new
test in the already selected Docker bundle suite compares both pins with the
runtime requirement and resolver lock. Its negative control failed on both old
pins. Final-image qualification and new current-candidate gates remain required.
Wait for all first-cycle jobs to finish before the consolidated correction push.

Evidence in the same external directory: `merge-83c2ca70-receipt.json`,
`push-83c2ca70-receipt.json`, `candidate-014-mcp130/`,
`pr159-failure-triage.json`, `bundle-pin-negative-control.log`, and
`bundle-pin-regression-unsandboxed.log`. Scoped installation backup and receipts:
`/tmp/wright-desktop-plugin-update-014-mcp130-20261016-01/` (private configuration
must not be published). Full SteveCAD, Robot and manufacturing acceptance is
still required; these delivery and packaging checks do not replace it.
