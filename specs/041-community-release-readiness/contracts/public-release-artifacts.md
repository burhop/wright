# Contract: Public Release Artifacts

This contract defines what public release-readiness artifacts must contain before Wright promotes a public install, visibility, or funding path.

## Install Guide Contract

Each install guide must include:

- Audience and use case.
- Supported status: planned, alpha, stable, deprecated, or unsupported.
- Prerequisites.
- Recommended first path.
- Configuration expectations, including BYO-AI and credential boundaries.
- Verification step.
- Known limitations.
- Troubleshooting or support link.
- Link to security policy.

A guide fails this contract if it asks users to infer platform support, assumes bundled LLMs or proprietary tools, or lacks a verification step.

## Package Listing Contract

Each public Python package listing must include:

- Package purpose and audience.
- Stability status.
- Supported Python versions.
- Canonical repository link.
- Documentation link.
- Issue tracker link.
- Security policy link.
- Release notes link.
- Funding/support link.
- Clear distinction between component package and end-user appliance, when applicable.

A listing fails this contract if it implies `pip install` provides the full Wright appliance when the package only serves developers or runtime components.

## Container Listing Contract

Each public container listing must include:

- Image name and tag policy.
- Supported platforms and validation status.
- Quick start using a published image rather than a local build when available.
- Required environment variables and credential boundaries.
- Port and volume expectations.
- Health checks or verification commands.
- Security and support links.
- Alpha/stability status.

A listing fails this contract if it promises unvalidated architectures, bundles proprietary tools without disclosure, or omits BYO-AI expectations.

## Visibility Surface Contract

Each public discovery surface must answer:

- What Wright is.
- Who Wright is for.
- What works today.
- How to try it.
- How to contribute.
- How to report security issues.
- How to sponsor or request support.

A surface fails this contract if a first-time visitor cannot identify the primary action within five minutes.

## Funding Surface Contract

Each funding surface must include:

- Active funding channels.
- Planned or deferred funding channels, clearly labeled.
- What funds or donated resources support.
- Sponsor/customer/partner contact path.
- Boundaries around unavailable commitments.

A surface fails this contract if it implies project-level fiscal structure, paid support, or partner benefits that are not actually available.

## Partner Brief Contract

Each partner brief must include:

- One-paragraph Wright positioning.
- Partner-specific relevance.
- Requested support.
- Evidence links or screenshots.
- Validation needs.
- Next action.

A brief fails this contract if it adds vendor-specific requirements to core Wright installation or overstates validated hardware support.
