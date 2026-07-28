# Changelog

All notable changes to the Wright project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/), and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [0.1.5] - 2026-07-28

### Fixed
- Made Docker Hub publication, stable `latest` promotion, and public digest verification mandatory for every production release.
- Added exact-digest Docker Hub recovery for already-verified releases without rebuilding containers or republishing immutable Python artifacts.
- Extended release evidence and operator guidance to record both required container registries.

## [0.1.4] - 2026-07-28

### Fixed
- Moved PyPI Trusted Publishing into the top-level release workflow so the OIDC publisher identity and generated package attestations agree.
- Added regression coverage and operator guidance that prohibit PyPI publishing from reusable workflows.

## [0.1.3] - 2026-07-28

### Fixed
- Kept checksum evidence outside the directory passed to the PyPI publisher so only the verified wheel and source distribution are uploaded.

## [0.1.2] - 2026-07-28

### Fixed
- Prevented generated Hermes API secrets beginning with `-` from being parsed as CLI options during container and local profile startup.
- Made the container release smoke test exercise the leading-hyphen secret case deterministically and report captured startup failures.

## [0.1.1] - 2026-07-27

### Added
- Provider-neutral MCP discovery and runtime integration, including current Hermes Agent 0.19 support.
- Protected release gates for PyPI, GHCR, optional Docker Hub mirroring, provenance, and post-publication verification.

### Fixed
- Made the stable Hermes plugin mirror self-contained so it no longer depends on unpublished Wright component packages.
- Hardened workspace/session separation, concurrent Hermes sessions, prompt queueing and steering, and production path validation.

## [0.1.0] - 2026-06-05

### Added
- Automated GHA workflows for Python (`python-quality.yml`) and Frontend (`frontend-quality.yml`) quality gates.
- Local developer quality tools including a pre-commit config (`.pre-commit-config.yaml`) and EditorConfig workspace rules (`.editorconfig`).
- Comprehensive GitHub Issue templates (`bug_report.yml`, `feature_request.yml`, `config.yml`) and Pull Request template (`PULL_REQUEST_TEMPLATE.md`).
- Automated weekly dependency update configuration via Dependabot (`dependabot.yml`).
- Developer-friendly non-Docker Makefile quality validation targets (`make lint`, `make format`, etc.).
- Repository visual branding assets (logos, visual icons, social previews) and rewritten comprehensive landing page (`README.md`).
- Community repository hygiene files (`CODE_OF_CONDUCT.md`, `SUPPORT.md`, `CONTRIBUTING.md`, `LICENSE`, `SECURITY.md`).
- Complete containerized agent runtime appliance with full agent stack, Hermes LLM profile, and smoke testing suites.
- Enhanced tool registry with 34 deterministic engineering MCP servers, OpenSCAD integration, and WebGL 3D viewport canvas.
- Premium engineering workspace IDE dashboard with session management, custom workspace switchers, and WebSocket bridge.

### Fixed
- Fixed remote host resolution errors and WebSocket communication parameters.
- Resolved workspace switching synchronization bugs.
- Fixed relative file paths and temporary file accesses inside the chat viewport.
