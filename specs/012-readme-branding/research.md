# Research and Technical Decisions: README Overhaul & Branding

This document covers research and design selections made for the Wright visual identity and landing page restructuring.

## Decisions & Rationale

### 1. Logo Visual Theme
* **Decision**: A hybrid gear and neural node network design in deep blue (`#0f172a`), teal (`#0d9488`), and cyan (`#06b6d4`) hues.
* **Rationale**: This design represents the union of mechanical engineering (the gear) and agentic artificial intelligence (the neural paths). Using modern, high-contrast HSL-tailored colors fits standard dark modes and presents a premium, tech-forward aesthetic.
* **Alternatives Considered**: 
  * **Text-only logo**: Rejected because it fails to establish a strong, memorable visual brand.
  * **Robot mascot**: Rejected as it is too generic and doesn't represent the precise engineering focus of the project.

### 2. Badge Architecture
* **Decision**: Dynamic shields.io badges mapped to repository indicators (GitHub Actions, MIT License, GHCR release image, Python, Node, Stars).
* **Rationale**: Dynamic badges build trust by proving the codebase is actively building, licensed, and deployed. Using shields.io maintains visual styling consistency.
* **Alternatives Considered**: 
  * **No badges**: Rejected. Badges are table-stakes for open-source frameworks and indicate project health at first glance.

### 3. Core Narrative & Value Proposition Focus
* **Decision**: Focus the landing page narrative on the "design and engineering agent orchestrator" value proposition, highlighting developer-level AI productivity gains for traditional engineering.
* **Rationale**: Moving the tone to a hybrid orchestrator positions Wright as a powerful utility that can utilize any agentic tool (commercial, startup, university, open source) to bring massive productivity leaps to traditional engineering, while maintaining flexible local/hybrid deployment options as secondary options rather than strict constraints.
* **Alternatives Considered**: 
  * **Feature-first description**: Rejected. Starting with features without explaining the local-first "why" fails to establish Wright's key differentiator.

### 4. Simplified Quick Start
* **Decision**: Minimum-viable copy-pasteable Docker Compose command block in the README, with advanced configuration details linked.
* **Rationale**: Keeping the README onboarding to a 4-line terminal block maximizes the conversion rate of visitors trying the software. Detailed setup options are reserved for `CONTRIBUTING.md` and the docs site.
* **Alternatives Considered**: 
  * **Multistep local setup guides**: Rejected because they clutter the main page and lead to higher drop-off rates due to environment-specific errors.
