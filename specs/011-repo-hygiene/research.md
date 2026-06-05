# Research and Technical Decisions: Repo Hygiene & Legal Foundation

This document details the research, options, and rationale behind the community health configuration choices for the Wright repository.

## Decisions & Rationale

### 1. License Selection
* **Decision**: MIT License
* **Rationale**: The MIT License is the industry standard for permissive open-source software, utilized by other leading agentic frameworks such as OpenHands, CrewAI, and OpenClaw. It maximizes adoption and collaboration by allowing individuals, developers, and commercial entities to use, modify, and distribute the codebase with minimal friction, requiring only that the original copyright and license notice are preserved.
* **Alternatives Considered**: 
  * **Apache License 2.0**: Rejected due to additional complexity (explicit grant of patent rights and requirements to document modifications). MIT is simpler and cleaner for early-stage community adoption.
  * **GPLv3**: Rejected because copyleft constraints deter enterprise and commercial contributors from integrating the project into their proprietary tooling.

### 2. Code of Conduct Standard
* **Decision**: Contributor Covenant v2.1
* **Rationale**: The Contributor Covenant is the de-facto industry standard for open-source communities, used by projects like Kubernetes, Rails, and Swift. Using a well-known standard builds instant trust with external contributors and provides clear, fair guidelines for community behavior and enforcement.
* **Alternatives Considered**: 
  * **Custom Code of Conduct**: Rejected because drafting custom legal/behavioral guidelines is highly error-prone, time-consuming, and lacks the immediate recognition and authority of the Contributor Covenant.

### 3. Security Policy Disclosure Channel
* **Decision**: Direct private reporting via email (`burhop@gmail.com` or project security contact) with a 48-hour response acknowledgment.
* **Rationale**: Providing a clear, private contact method prevents security vulnerabilities from being disclosed publicly as zero-days. A standard email reporting flow is universally understood and accessible to security researchers without requiring complex ticketing integrations.
* **Alternatives Considered**: 
  * **Public GitHub Issues**: Rejected. Reporting security flaws publicly exposes users to immediate exploitation before patches can be designed and released.

### 4. Contributing Guidelines & Spec-Kit Integration
* **Decision**: CONTRIBUTING.md specifying the `spec-kit` workflow (specify → plan → tasks → implement), branch naming (`011-repo-hygiene`), and code formatting tools (`ruff`, `eslint`, `prettier`).
* **Rationale**: Wright relies on a structured, spec-first methodology. Documenting the specific slash commands (`/speckit-specify`, `/speckit-plan`, `/speckit-tasks`, `/speckit-implement`) and branch naming conventions is critical for ensuring that external contributions conform to the project's development workflow.
* **Alternatives Considered**: 
  * **Standard PR Contributing Guide**: Rejected because standard guides do not emphasize spec-kit design-first principles, which would result in pull requests that bypass the required spec and plan validation gates.

### 5. Repository Root Cleanup & Screenshot Relocation
* **Decision**: Move the existing screenshots (`screenshot_*.png`) from the root directory to `docs/images/`, and update the git exclusion list (`.gitignore`) to ignore debug, log, test output, and local database files.
* **Rationale**: A clean repository root increases credibility and signals high code quality and professional maintenance. Relocating screenshots to `docs/images/` keeps documentation assets organized, while updating `.gitignore` prevents developers from accidentally committing local database files (`state.db`) or runtime log/test output files.
* **Alternatives Considered**: 
  * **Deleting Screenshots**: Rejected because screenshots are highly valuable visual guides for users.
  * **Leaving Screenshots in Root**: Rejected because it clutters the root directory and does not follow repository best practices.
