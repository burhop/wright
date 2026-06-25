# Research: Fix Test Validation Failures

## Decision: Guard AppShell localStorage access behind safe helper functions

**Rationale**: The failing Vitest environment exposes a storage object that throws a security error. Wrapping reads and writes keeps the component resilient in tests, embedded browser contexts, and privacy-restricted environments while preserving saved preferences when storage works.

**Alternatives considered**:

- Mock `localStorage` only in the test: rejected because the production component can encounter similar failures in restricted contexts.
- Remove preference persistence: rejected because it would regress existing UX.

## Decision: Use a cross-platform environment variable helper for desktop build

**Rationale**: npm scripts execute through platform-specific shells. `BUILD_TARGET=desktop vite build` fails under Windows `cmd.exe`; using a package such as `cross-env` or a Node wrapper makes the command portable.

**Alternatives considered**:

- Add separate Windows and POSIX scripts: rejected because it increases documentation and maintenance burden.
- Require PowerShell syntax: rejected because npm defaults may still use `cmd.exe`.

## Decision: Treat Python import failures as environment/workspace validation failures first

**Rationale**: The baseline `uv run pytest` failure shows collection cannot import declared packages and dependencies. Before changing product code, validation should ensure the uv workspace is synchronized and that package metadata exposes test dependencies consistently.

**Alternatives considered**:

- Patch tests around missing imports: rejected because it hides environment setup issues.
- Ignore Python tests: rejected because the user asked for all failing test cases and the repo includes Python validation.
