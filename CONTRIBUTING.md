# Contributing to Wright

Thank you for helping Wright become a healthier public alpha. Contributions are
welcome across code, docs, issue triage, MCP validation, examples, and release
hardening.

Wright is alpha software. Please avoid claims that a change makes the project
production ready unless the supporting tests, docs, release notes, and security
review are already in place.

## Where to Report Things

- Reproducible bugs: use the Bug Report issue form.
- Feature proposals: use the Feature Request issue form.
- Usage questions and troubleshooting: use GitHub Discussions.
- Security vulnerabilities: follow `SECURITY.md`; do not open public security
  issues.

Remove API keys, tokens, private hostnames, proprietary files, and sensitive
screenshots from all public reports.

## Prerequisites

- Python 3.11 or newer.
- `uv` for Python workspace management.
- Node.js 22 or newer.
- Docker for appliance, smoke, security, and MCP validation work.

## Spec Kit Workflow

Wright uses Spec Kit for design-led feature work. Feature changes should follow
this lifecycle under `specs/<feature-name>/`:

Routine bug fixes, documentation edits, test-only changes, and CI maintenance do
not need Spec Kit artifacts unless they grow into feature work.

1. Specify the feature and user requirements.
2. Clarify ambiguous requirements.
3. Plan the implementation and check project constitution alignment.
4. Generate ordered tasks.
5. Implement the tasks and keep artifacts current.

Engineering MCP catalog work must follow
`docs/mcp-catalog/mcp-server-testing-process.md`. Do not add MCP-specific host
software to the base Docker image just to make catalog validation pass.

## Branch Discipline

- Use dedicated feature branches, normally named `###-feature-name`.
- Do not commit directly to `main` or `dev`.
- Keep pull requests focused and explain user-visible behavior, tests, and
  documentation changes.

## Quality Gates

For feature branches, `scripts/check-dev-merge.sh` is the authoritative gate
before merge to `dev`. The native Hermes candidate checks are mandatory and
have no skip flag: they validate the complete wheel, base/runtime isolation,
source isolation, forbidden executables, lifecycle behavior, and every claimed
platform. Release-train changes must additionally preserve the build-once
wheel/sdist hashes, runtime-extra lock, released-Hermes capability and stable
channel ordering, OCI candidate digest, mandatory Docker Hub mirror, full-SHA
Action pins, protected environment ordering, expiring vulnerability exceptions,
and the GitHub-Release-last contract. A fixture or dry-run rehearsal is evidence
of orchestration, not authorization to publish.

Before merging `dev` to `main`, run `scripts/check-prod-merge.sh`. Production is
not complete until published native Hermes and Docker paths both have terminal
evidence; the legacy Git-plugin mirror cannot substitute for native evidence.
The production gate also runs `check-wheel-contents` against the exact wheel
built by the dev gate. Wright intentionally ships a self-contained wheel with
multiple reviewed top-level package roots, so only `W009` is suppressed in the
root packaging configuration; all other wheel-content findings remain fatal.

The dev gate runs a focused security regression tranche before the complete
test suite. Changes that move request-controlled data into cookies, filesystem
operations, process execution, or error responses must extend those regression
tests. GitHub CodeQL remains the whole-program data-flow authority: new CodeQL
alerts block promotion even when the local gate is green, and the local gate
must be updated whenever CI exposes a security path it did not cover.

Run the relevant checks before opening a pull request:

```bash
uv run pytest
uv run ruff check apps/api/ packages/
uv run ruff format --check apps/api/ packages/
npm ci
npx -w apps/web eslint .
npx prettier --check apps/web/
npx tsc --noEmit -p apps/web/tsconfig.app.json
npm run test --workspace=apps/web
npm run build --workspace=apps/web
mkdocs build --strict
```

Convenience targets are also available:

```bash
make lint
make format
make typecheck
make test
make check
make security-scan
make alpha-release-check
```

Mypy is warning-only during the first public-alpha hardening window. Maintainers
will promote it to a blocking gate after the typing baseline is fixed.

## Local Pre-commit Hooks

Pre-commit is optional but recommended:

```bash
pip install pre-commit
pre-commit install
```

## Pull Request Checklist

- [ ] I read this contributing guide.
- [ ] I kept the public-alpha/BYO-AI contract accurate.
- [ ] I added or updated tests where behavior changed.
- [ ] I updated docs where user or maintainer workflows changed.
- [ ] I ran the relevant quality gates and included failures or skipped checks in
      the PR description.
- [ ] I removed secrets, local paths, proprietary files, and generated artifacts.

## Contributor Recognition

Wright uses the All Contributors convention. Maintainers can add contributors
with:

```bash
npx all-contributors-cli add <github_username> <contribution_type>
npx all-contributors-cli generate
```

Contributor metadata is tracked in `.all-contributorsrc` and displayed in the
README.
