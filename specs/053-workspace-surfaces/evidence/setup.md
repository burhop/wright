# Workspace Surfaces Setup Evidence

Date: 2026-07-30

Platform: Windows development host, PowerShell, Python via `uv`, Node/npm

Scope: Phase 1 tasks T001-T010 only; this record is not user-story or release
acceptance evidence.

## Result

The setup and contract scaffold passes its required lock, import-boundary,
schema-sync, configuration, browser-project, build, and package-manifest checks.
All Workspace Surfaces feature flags remain off by default, so this phase does
not change the existing viewer behavior.

| Check | Command/evidence | Result |
|---|---|---|
| Exact frontend dependency pins | Node JSON validation of `apps/web/package.json`, `apps/web/package-lock.json`, and root `package-lock.json`; `npm ls @modelcontextprotocol/ext-apps dompurify plotly.js-dist-min @types/plotly.js --workspace web --depth=0` | PASS: `1.7.5`, `3.4.12`, `3.7.0`, and `3.0.10` respectively in both lockfiles and the install tree |
| Python lint and formatting | `uv run ruff check ...`; `uv run ruff format --check ...` on the Phase 1 Python files | PASS |
| Policy/configuration, contract, wheel, and boundary tests | `uv run pytest packages/workspace_service/tests/test_surface_config.py tests/contract/workspace_surfaces/test_schema_sync.py tests/packaging/test_wheel_contents.py tests/test_import_boundaries.py -q` | PASS: 19 tests |
| Production web build | `npm run build --workspace web` | PASS: TypeScript and Vite production build completed |
| Browser/desktop project discovery | `npx playwright test --config playwright.config.ts --list` | PASS: existing Chromium suite discovered; Firefox, WebKit, and desktop-surface projects are scoped to the Workspace Surfaces suite and activate as those tests are added |
| Public wheel build | `uv build --wheel --out-dir C:\tmp\wright-workspace-surfaces-setup-wheel` | PASS: `wright_engineering-0.1.9-py3-none-any.whl` built |
| Wheel manifest | `uv run --with check-wheel-contents==0.6.3 check-wheel-contents <wheel>` | PASS: wheel `OK` |
| Archive resources | `tests/packaging/test_wheel_contents.py` opens a real wheel and asserts the `wright` helper, version-1 schemas/OpenAPI, contract-set manifest, and renderer entry/asset manifest | PASS |
| Whitespace/worktree inspection | `git diff --check`; `git status --short`; `git diff --stat` | PASS; only intended Phase 1 implementation and setup-hygiene paths were present |

The web build reports the existing large-chunk warning for the current main
bundle. Workspace Surfaces Plotly rendering remains designed for a later lazy
chunk, and its performance/bundle acceptance is owned by the later renderer and
release tasks rather than waived here.

## Security Audit Observation

`npm audit --workspace web --omit=dev --json` reported two high-severity entries
in the pre-existing `react-router-dom` -> `react-router` chain for
`GHSA-qwww-vcr4-c8h2`. The four newly pinned Workspace Surfaces packages are not
in the reported path. This is not a Phase 1 lock/schema/package-manifest failure,
but it remains a blocking input to the later dependency/security and release
gates. No audit fix, force downgrade, exception, or waiver was applied.

Package identity, license, registry integrity, intended use, and this audit
observation are recorded in `docs/security/dependency-review.md`.
