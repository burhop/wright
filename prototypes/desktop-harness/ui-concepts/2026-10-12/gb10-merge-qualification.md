# GB10 merge qualification and host limitation

Candidate code is rebased on SteveCAD dev `c1a8d009`. The experimental installed
0.4.0 plugin remains unchanged; prepared 0.5.0 is not installed. The panel resource
remains byte-identical at `08f146c976f273936b218408edd380e6936860e38d10ce2e0d9f054a1f0906ca`
after the scanner corrections. No gateway authority, model or provider was substituted.

## Local preflight and corrections

The full gate at `2832633a` passed dependency audits, exact ARM64 image security,
lint/types, native distribution build and clean install, governance/release,
API, adapters, core, storage, model registry, tool registry and workspace service.
Its repository suite ended with 1557 passed, 66 skipped and one leak-scan failure.
The findings were an inert fixture credential and a generation-counter identifier;
explicit fake naming and a descriptive counter name fix them without a scanner
exception. The unchanged scanner's five tests pass.

The remaining-stage preflight recorded 1836 frontend tests passed and four stale
palette journeys. They now open Add step and retain exact Request input, server
choice and scope-isolation assertions; the 30 affected tests pass. Strict docs pass.
The first complete browser preflight recorded 157 passed, five skipped and 22
failed. Three test contracts still assumed the old vertical palette. Their updated
journeys retain editor bounds, overflow, keyboard, source/CAS and declaration checks.
A fourth measurement raced the existing 150 ms console-collapse grid transition.
A private rectangle probe observed editor width changing from 842.84 to 1232 px;
readiness opening/closing at the settled width leaves geometry unchanged. The
fixture now observes hidden console and completed root animations. Both original
strict readiness geometry tests pass; their size assertions remain unchanged.

## Actual GB10 WebKit limitation

Playwright 1.62.1 / WebKit revision 2336 cannot start on this Ubuntu 24.04 ARM64
GB10 (65536-byte kernel pages). The first 18 WebKit cases failed for missing
GStreamer/AVIF libraries. Four Ubuntu packages were downloaded and extracted into
private test state, with no system package installation or change to Wright's image.
The ESM candidate rejected access; the explicitly selected public archive versions
and package hashes are retained. An isolated browser copy preserves official
launchers and the shared cache. After resolving libraries, an empty-browser launch
still aborts with SIGABRT before any Wright page or provider request. A bounded
GDB trace retains the inspector-initialization stack; stripped symbols do not
establish the exact root cause. [Upstream 64 KiB allocator discussion](https://bugs.webkit.org/show_bug.cgi?id=209360)
is context, not proof that this is the same defect. No kernel change, vendor patch,
sandbox weakening or claimed WebKit pass is proposed.

The runbook explicitly permits a documented local browser/runtime limitation.
The local full script may use SKIP_PLAYWRIGHT=1 only alongside a separate complete
Chromium, Firefox workspace-surfaces and desktop-surface matrix on isolated ports.
All current-head GitHub checks, including the normal WebKit matrix, must pass before
merge. CI retains its complete commands; this does not waive a product failure.
WebKit on this GB10 remains unqualified. Windows native 0.5.0 acceptance and live
SteveCAD CAD/image/export execution remain unqualified; headless OAuth requires
Windows browser consent plus a loopback callback tunnel.

## Retained evidence

Private logs/receipts are in `/tmp/wright-stevecad-merge-gates-20261013-01`,
and browser dependency/abort diagnostics in `/tmp/wright-stevecad-browser-deps-20261013`.
Failed gates and browser traces are retained. Native packaging's generated static
files are archived before restoring only those known generated checkout changes;
fresh wheel/source artifacts remain available. They are build outputs, not edited
accepted workflows or original engineering evidence. Actual final gate and current-head
CI outcomes belong in the PR description; this preflight record does not claim them.
