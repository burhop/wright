# Changelog

All notable changes to the Wright project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/), and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

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
