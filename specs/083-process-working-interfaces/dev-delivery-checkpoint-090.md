# Development delivery checkpoint — 10 October 2026

## Authority and stopping point

The user authorized committing current work, pushing it to GitHub and following
the PR/check process into `dev`. They also requested current README/documentation
and screenshots where useful. No direct dev push or production release is planned.
The latest dock run remains at declared intent review; no new engineering decision
is made to deliver software. The full mechanical goal remains incomplete.

## User-visible scope

- Build and inspect workflows in the established editor; carry out the same process
  in common or saved tailored working views using shared backend authority.
- Save portable instructions and explicit assumption policy; declare input questions
  and engineering reviews as separate durable interactions.
- Inspect actual model/image/document/numerical outputs, exact validation evidence,
  previous attempts, progress and actionable failure diagnostics.
- Reopen a current-source recorded run from history, including when its diagram
  cannot be drawn, without starting or approving it.
- Update ordinary workspace navigation, provider selection, settings and Git controls.

This is the accumulated Feature 083 source and local verification work. Existing
engineering examples verify product behavior and retain their separate limitations.
Generated bulk traces, private runtime state and presentation archives stay local.
Curated screenshots and evidence descriptions may be committed after inspection.

## Remaining work

1. Complete native deliverables and validation for the separate 130 mm sheet-metal
   study after its explicit review; resolve the source's port-type mismatch in a
   visible new revision. Do not change the waiting run's accepted source silently.
2. Locate/reuse the reviewed swim-lane implementation and prove engineering handoffs.
3. Complete the remaining final fresh engineering journeys after the last shared
   repairs; preserve earlier digital verification and required human holds.
4. Treat Codex-as-agent runtime integration as a separate project. The current
   Codex MCP profile does not implement that replacement.
5. User acceptance, supplier release and physical engineering acceptance remain
   separate. Slide-deck work is deferred.

## Verification and delivery

Completed locally before the candidate commit:

- 89 focused frontend tests across navigation/history, Git controls, recovery,
  provider settings and preview routing; type checking and production build 47.
- Python Ruff checks pass. Frontend ESLint has zero errors and 12 retained hook
  dependency warnings; the required whole suites remain pending.
- Browser235: three served steps pass, exact run and 23 outputs restored after
  reload, no process mutations or browser diagnostics. Report structure validates.
  Earlier browser230–234 stopped evidence remains, including harness mistakes.
- Current README/tour screenshots visually inspected; two immutable capture hashes
  recorded. Historical Rivet documentation is labelled legacy compatibility.
- Explicit staging manifest excludes 1,896 local generated artifacts and the
  unrelated historical Studio-automation note. Staged credential scan is clean.

Full native merge gate, image build/scan, pre-push gate, GitHub CI, PR merge and
exact dev health verification remain pending. No pending check is counted as passed.

Local receipts are under `.local-run/process-interfaces-083/mechanical-engineering-20261008`
and `.local-run/dev-delivery-*`. Failures and corrected reruns are retained.

## Candidate repairs before publication

- `cd836801` records the accumulated source/docs checkpoint; `732946ac` fixes
  the clean Docker build's missing local process-client/UI-kit packages.
- `b550da6f` updates PyJWT to 2.15.1 and urllib3 to 2.8.0. The runtime dependency
  audit then reports no known vulnerabilities. The strict documentation build
  passes after repairing published-site links; repository evidence links now
  target tracked GitHub files and local-only evidence is identified honestly.
- Full gate attempt 01 stopped at the dependency audit. Attempt 02 passed that
  audit and found fixable image dependencies. The clean image built successfully;
  its scan remains blocking until the separate OS/npm/pip/Hermes repairs pass.
- The first whole frontend run recorded 1,782 passes and seven failures. A bounded
  two-worker reproduction passed 237/238 and isolated a stale route assertion.
  The correction preserves all test cases, bounds JSDOM worker contention and
  waits for two actual asynchronous readiness events. The complete rerun is pending.

These are local candidate repairs, not GitHub CI or dev integration evidence.

## Verified candidate d4156470

The complete frontend rerun passes: 198 test files and 1,789 tests. The exact clean
image `sha256:70533e9695cc104a94beb0d9ca9075dd34a76e4e9f3c01aba7478e9a2c57dd21`
built from `d4156470280de860b820753c58a9cc667be5a249` passes the current Trivy policy.
The runtime Python dependency audit reports no known vulnerabilities. Twenty
container security/packaging contracts and ten README/scanner-setup contracts pass.
The final strict docs build passes after the adapter-support/API corrections.

Full merge gate 03 stopped because port 18000 was occupied. Attempt 04 uses
verified free ports 18183/15283. It has passed the audits, Ruff/format, ESLint,
Prettier, TypeScript and the blocking release/control-plane type check, and is
running backend tests. The broad warning-mode MyPy check reports duplicate test
`conftest` modules; it is not reported as a pass.

The history credential scan found 47 public evidence fields: independently checked
file hashes, generated vault filenames and typed idempotency identifiers. Automatic
approval review rejected changing scanner configuration under delivery authority.
The [exact proposed handling](scanner-findings-proposal-090.md) awaits user approval;
no scanner policy has been changed and no push has occurred.

## Packaging follow-up

Gate 04 passed 391 control-plane tests (one skipped), then stopped on two release
contracts. The OS update is now bounded to exact PCRE2/OpenSSL packages rather
than an unrestricted upgrade. The private-package check now respects the existing
external FreeCAD provider submodule's independent publication ownership. All 212
focused release, dependency and container contracts pass after those corrections.

The exact-image smoke exposed Hermes 0.19's strict PyJWT 2.13.0 metadata pin. The
security-fixed 2.15.1 version is recorded alongside the two existing exact security
overrides. Changed versions and unrelated conflicts still fail. An additional
image-level check verifies RSA JWT signing/verification and rejection of invalid
signatures, expired tokens, wrong issuers and wrong audiences. These checks pass;
the new bounded OS package build and complete gate remain pending.

The corrected clean image from `2e3011906820` is
`sha256:d0937408b6add3f54325fed71dedc85af3bfb03e361a75891ba37af3a5fdf19c`.
Its vulnerability scan and offline API/Hermes/JWT smoke pass. Release/native
coverage passes with 323 tests, nine skips and 85.42% coverage. The independent
API suite passes 752 tests with one skip. Gate 05 again passes 391 control-plane
tests and the release suite, then exposes the same independent-provider assumption
in `test_public_python_distribution.py`. Both ownership checks are now corrected
and their four focused tests pass. A complete merge-gate pass is still pending;
the scanner-configuration approval remains pending and no publication has occurred.

## Native source-archive correction

Gate 06 passed the control-plane, release and native suites, coverage and frontend
build, then exposed a real installation defect: the source archive omitted the
shared process-client/UI-kit build inputs. Its direct wheel installed, but rebuilding
the wheel from the source archive failed. npm's local package links could be visited
before the real directories during the archive builder's whole-tree walk.

The source archive now selects the same explicit source roots directly. Its validator
also requires every declared wheel `force-include` source, with negative checks for
similarly named files and paths outside the archive. The retained failing archive is
rejected by this new check. The corrected archive validates, builds its wheel and
installs into a clean environment; both clean installations import successfully.
The direct and rebuilt wheels are byte-identical. All 192 release tests pass, along
with the focused packaging checks. These are local artifacts, not a public release.

The broader core, workspace, agent-adapter, registry and API verification passes.
Two stale storage migration assertions were updated for the already implemented
schema versions 22 and 23; the vault suite then passes 209 tests with one skip.
The native distribution now includes the freshly built current UI and runtime lock.

The corrected source needs a fresh clean candidate image and complete merge-gate
pass. Scanner approval, pre-push validation, GitHub CI and dev integration are still
pending. The 130 mm engineering run remains at its declared human review.

## Packaged UI alignment

Reviewing the user documentation against the build exposed inconsistent frontend
flags. Docker defaulted the process view off and omitted the editor/composer and
surface flags; the merge gate's reused frontend build omitted all four. The native
builder enabled the first three but omitted workspace surfaces. A successful build
therefore did not prove the UI shown in the current screenshots was reachable.

Gate 07 passed the new exact-image vulnerability scan and static checks, then was
stopped during control-plane tests to correct this packaging discrepancy. It is
not a completed gate. Docker, native and reused gate builds now explicitly enable
the same four features. Their focused contracts, rebuilt assets, actual packaged
workspace browser journey and complete gate must pass before delivery.

## Remaining regression corrections

The broad root-suite preview exposed older draft generators that omitted the
saved action-intent instructions. Newly prepared Modelica, drill-jig and sheet-metal
drafts now use the existing instruction materializer with packaged, versioned
instruction bodies and their prior `require_specified` policy. Existing embedded
instructions remain unchanged, malformed snapshots fail, and the legacy renderer
is unchanged. No accepted engineering run or review was modified. The actual
runtime readiness checks remain enforced.

The Modelica test now constructs the real runtime instead of bypassing its
initialization. Sheet-metal assertions require the supplier manifest plus all eight
raw HTML/text pairs, and permit only the deliberately empty sealed-output directory
before dispatch. The README again explains workspace artifact ownership. Four
redaction fixture values are explicitly named synthetic/fake; their redaction
assertions remain in place. No scanner policy was changed.

The exact affected checks pass: 48 example/documentation/lightweight-scanner tests,
21 redaction tests and 81 packaging/gate/migration tests. The production frontend
build with all four flags passes. Native restaging, exact-image verification,
the packaged browser journey and the full gate remain pending at this checkpoint.

## Exact packaged-browser findings

Local commit `fa40c6771ae5c6eb9940cfdefb7dd0fd7a350d1e` contains the UI alignment
and new-draft instruction corrections. Its clean archive image builds, passes the
image security policy, and passes offline cold-start/API/Hermes/JWT checks. Its
native wheel and source archive validate with UI manifest digest
`b62a5fa50b82b731af52561b585cfed8637dee41bcab6f4dd7bc24d1eb5ed51c`.
The full merge gate 08 is running; it is not reported as passed.

The first packaged browser attempt stopped on static-asset HTTP 403 responses.
The isolated test setup omitted `WRIGHT_ALLOWED_ORIGINS` for its custom port;
the documented Docker env template already declares its standard ports. A fresh
setup declares only its exact test origin with enforced authentication unchanged.
The environment-variable guide now names the actual setting instead of the obsolete
`CORS_ALLOWED_ORIGINS`. Both failed walkthrough records are retained and validate
against the walkthrough report contract.

The second attempt proves ordinary Workflows entry opens a blank editor, adding
one input block works, Save succeeds, and reload restores the same saved source.
It submits no run/review/dispatch action. It nevertheless stops on repeated model
picker HTTP 404 errors, so it is **not a successful complete browser journey**.
The actual response incorrectly classifies the upstream model-service failure as
`WORKSPACE_NOT_FOUND`. Source inspection of the exact bundled Hermes 0.19.0 confirms
that `/api/model/options` and the confirmed session-model-lock contract are absent.
This is a real packaged-adapter capability gap, independent of the synthetic model
configuration used for the authoring proof. Startup health did not cover it.

Next work must qualify the packaged adapter's real discovery/routing/lock capability
through an existing supported adapter/provider boundary and correct its unavailable
diagnostic. Do not synthesize model choices, bypass frozen-route verification, hide
the error, or treat the successful authoring checks as proof of model execution.
The operator guide records this qualification limit. No protected engineering
source or review was changed. Publication and scanner approval remain pending.

The model-service boundary now diagnoses HTTP 404/405/501 from `/api/model/`
as an unavailable required service (HTTP 503), rather than a nonexistent workspace.
It returns a bounded compatibility/setup message without echoing the upstream
response, issuing another request or changing model selection. Authentication
failures retain their original status. All 23 affected model-service/health tests
pass. The missing provider capabilities remain unresolved; this correction does
not claim model execution support.

Gate 08 is deliberately stopped because the corrected candidate needs a fresh
exact-image check. Its retained partial evidence includes 391 control-plane tests
(one skip), 192 release tests, 154 native tests (nine skips), and 326 coverage tests
(nine skips) at 85.46%. Its frontend build and native archive checks pass, and its
clean wheel and rebuilt-source installations import successfully. These are scoped successes, not
a completed merge gate. The previous candidate and failed browser records remain
retained. The full current gate must still complete before publication.

## Packaged model transport repair, in progress

The user journey is configuring a real model, starting a saved workflow, and
inspecting the same frozen routing and submitted request on continuation. The
offline exact-image inspection confirms that bundled Hermes 0.19.0 exposes the
existing SDK resolver/client used by Wright's confined authoring and image paths.
It does not expose the HTTP discovery/session-lock contract. Reuse that SDK seam
for the explicitly configured packaged workflow transport; retain the HTTP route
for hosts that qualify it. There is no automatic fallback after a failed request.

The shared core routing contract must distinguish the SDK route, profile,
provider, model, endpoint and SDK identity. The existing workspace service freezes
and revalidates it. The existing tool-decision bridge translates proposals; the
worker executes no tool and the existing runtime/gateway retains execution and
approval authority. Preserve complete request/repair evidence at the actual SDK
boundary, including failures. An accepted HTTP run cannot silently acquire an SDK
route. Missing configuration stays an explicit readiness/setup failure.

Discovery should report only the configured model observed by the resolver. SDK
mode must disclose that remote selection is unavailable and direct intentional
changes to Model Setup, rather than synthesize a catalog or session-lock receipt.
Existing interface/common-view compatibility remains unchanged. Prove isolated
SDK text and tool-decision requests, changed-route rejection, continuation,
multimodal input and error evidence, then qualify the stock package and ordinary
packaged workspace journey. Synthetic endpoint responses prove transport and
runtime mechanics only, not real model inference or engineering acceptance.

The SDK repair is implemented locally. All 539 affected adapter/workspace/API and
Docker checks pass (one skip), alongside 337 shared-contract checks and three
workspace UI tests. The strict documentation build passes. Stock Hermes 0.19.0
in the retained `fa40c677` image passes the saved offline SDK qualification using
the current adapter mounted read-only: text with an inline image, one validated
tool proposal, retained failed-request evidence and changed-route rejection.
The synthetic loopback endpoint receives three requests; no MCP operation or
real inference is submitted. The reproducible check is
`scripts/test-hermes-workflow-sdk.py`, with explicit installed SDK Python/root.
The first attempt used the image's system Python instead of its application
environment and failed import; its record is retained separately.

The production UI and restaged native distribution validate with UI manifest
`9d6cf79fd990ec47c0a68e50187b1a7c6121a7a251a7c96d4c7c439c0b91c052`.
This restaging does not qualify the native host's actual model configuration;
source/native SDK selection remains explicit. A fresh clean candidate image,
actual packaged-browser journey and complete delivery gates are still required.
