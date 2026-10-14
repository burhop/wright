# Desktop engineering-demo baseline correction — 14 October 2026

M0 in progress under the submitted desktop engineering-demo goal. No live plugin,
workspace, credentials, provider or engineering run was changed by this correction.
The approved 0.4.0 installation and existing 0.5.0 proposal remain preserved.

## Rechecked baseline

Fetched `origin/dev`: `c1a8d00942d8a80ca6229ebed23d7b8f4153a7d9`.
PR 153 remains draft/open at `7035cf029aa988f411c6ab4e39bcc93315a27e3d`.
Every first-cycle check is terminal; Windows frontend and aggregate CodeQL failed.
Windows backend, hosted Playwright/WebKit and the remaining required reported
checks passed. Docs deployment was skipped for the PR as expected.

The six planning/index changes were the only pre-existing dirty tracked/untracked
files in this feature worktree. They are preserved in this correction checkpoint
so the submitted goal is durable and can move to the next feature branch.
The original checkout and other worktrees are untouched.

## Windows fixture

The CI failure occurs before login because Windows stat/chmod does not supply
the POSIX 0600 metadata required by this GB10-only private-LAN development entry.
The fixture now overrides stat metadata only for its exact temporary token file,
using a hoisted native-export spy because the Vite config imports outside Vitest's
virtual module mocks. All other filesystem calls pass through. Real file reads,
private-file rejection, forbidden peer/origin checks and credential non-disclosure
remain tested. A denied file must not call login. The native export is restored
after the suite. Production `private-lan.vite.config.ts` is unchanged.

The first ordinary module-mock and late native-spy attempts did not intercept the
configuration's captured export; their negative assertion failed locally. The
hoisted correction passes all four original tests. Windows CI is still required.

## Generated-bundle CodeQL findings

All nine new SARIF findings name `prototypes/desktop-harness/native-editor.html`.
The maintained builder emits it from `native-entry.tsx` with bundled dependencies.
The retained SARIF and exact snippets are in the prior private gate evidence:
`/tmp/wright-stevecad-merge-gates-20261013-01/codeql-js-01.sarif`.

| Findings | Source inspection and disposition |
| --- | --- |
| Five insecure-randomness findings | Three 0.185.1 graphics `Source`, `Texture`, `Object3D`, `BufferGeometry` and `Material` UUIDs. These identify renderer objects; they are not Wright permission/session credentials. Do not reuse those IDs as authority |
| One incomplete-sanitization finding | `mdast-util-gfm-table` 2.0.0 inline-code table serialization escapes pipe syntax; this is not an HTML/credential sanitizer. The shared document renderer uses ReactMarkdown; no sanitization authority is assigned to this helper |
| Two character-range findings | `micromark-util-sanitize-uri` 2.0.1 intentionally retains URI punctuation/alphanumeric ranges in `normalizeUri`; protocol checking is a separate operation. The warning is against the compact dependency expression, not a new Wright URL permission rule |
| One prototype-pollution utility finding | `extend` 3.0.2 has explicit `__proto__` own-property/getter handling and `defineProperty` guarded assignment. A local deep-merge probe with both `__proto__` and `constructor.prototype` leaves `Object.prototype` unchanged. This is a bounded reproduction, not a blanket dependency-security claim |

Apply the repository's existing generated-output analysis policy to this exact
HTML file only. Maintained TS/TSX, shared components, builder, Python bridge and
backend remain scanned. The new regression checks those sources against the
actual ignore patterns and rejects a restrictive include list. Scanner config
changes now select the gate policy tests. Node dependency audits remain blocking;
no query family or advisory is waived. No minified code or runtime dependency was
changed, and the generated HTML bytes remain unchanged.

## Qualification status

- Focused private-LAN test: four passed on GB10; Windows execution pending CI.
- Combined gate/source-coverage/scanner regressions: 43 passed.
- Focused ESLint, Prettier, Ruff check/format, TypeScript and shell syntax checks passed.
- Full local gate and corrected-head CI: pending; not yet claimed.
- Previously recorded GB10 WebKit launch limitation remains; hosted browser
  qualification must stay green. This correction does not qualify new native UI
  interactions, general engineering tasks, SteveCAD authentication or live demos.

Current private logs will be retained in
`/tmp/wright-desktop-demo-baseline-20261014-01`. Prior gate receipts and failed
attempts remain intact. No second push occurs before local gates and the complete
consolidated correction are ready.


The installed Wright connection was read successfully in this chat: connected,
with model identity and app build unreported and global native-tool ceiling
unverified. The observed 0.4.0 runtime remains on port 8123. A retained candidate
service on port 8126 uses `.venv-dev-gate`; therefore the new gate must use a fresh
isolated `WRIGHT_GATE_VENV` instead of reinstalling packages under that live service.
No service was stopped or restarted.


## Fresh security-database failure and correction

The full gate at `4747cb7c` stopped at the exact-image scan. Trivy's 14 October
19:14 UTC database reports CVE-2026-8286, CVE-2026-8927 and CVE-2026-92392 against
both curl and libcurl4t64 8.14.1-2+deb13u5, fixed in 8.14.1-2+deb13u7. The image
had reused a cached APT layer from the earlier qualified build. Its failing
receipt/log and public scan projection are retained, not overwritten.

A disposable container refreshed Debian's signed package indexes and confirmed
8.14.1-2+deb13u7 as the trixie-security candidate for both packages on ARM64.
Pin curl to that version in both existing Docker stages to invalidate those
cached layers; its exact-version libcurl dependency supplies the corresponding
fix. The existing Docker security contract now retains the pin. No exception,
host package installation or running-image change is made. Build and scan the
new committed image before repeating the gate; x64 remains separately qualified
by its CI build and checks.
