# Quickstart: Community Release Readiness Review

Use this quickstart to validate the feature after implementation.

## 1. Review User Use Cases

Open the public repository and docs entry points. Confirm a first-time visitor can find install guidance for:

- Curious demo user.
- Windows 11 user.
- Linux workstation or Dell GB10 user.
- Hermes Desktop user.
- Python developer.
- MCP/tool contributor.
- Enterprise evaluator.
- Sponsor or customer.

Pass condition: each use case has a recommended path, prerequisites, verification step, and limitations.

## 2. Validate Container Install Story

Confirm public docs and container listing materials identify:

- Canonical image names: `burhop/wright` and `ghcr.io/burhop/wright`.
- Tag policy.
- Platform support and validation status.
- Required environment variables.
- Local ports and volumes.
- Health check or browser verification.
- BYO-AI and no bundled proprietary tool expectations.

Pass condition: a user can start from the public docs and understand whether to run a published image, build locally, or wait for a future release channel.

## 3. Validate Python Package Story

Confirm package docs identify:

- `wright-engineering` is the single public alpha PyPI package.
- Component packages are deferred for alpha and are not promised as public PyPI installs.
- `wright` is unavailable on PyPI and must not be promised.
- Fallback package naming strategy is documented.
- Links to repository, docs, issues, security, releases, and funding/support.

Pass condition: no page promises `pip install wright`; public Python install references use `wright-engineering` and explain Docker remains the primary end-user path.

## 4. Validate Hermes Desktop Story

Confirm Hermes-facing docs explain:

- Whether Wright runs as a local service, plugin, native desktop integration, or source checkout.
- How Hermes Desktop users connect to or manage Wright.
- What is not provided by a Docker container.

Pass condition: Windows users are not led to expect a full desktop GUI inside a Linux container.

## 5. Validate Visibility Surfaces

Review README, docs landing page, package/container descriptions, and release notes.

Pass condition: each surface states what Wright is, who it is for, current alpha status, how to try it, how to contribute, and how to sponsor or request support.

## 6. Validate Funding Path

Review sponsorship and funding docs.

Pass condition: users can find an active sponsorship path, understand what funds support, and distinguish individual sponsorship, project-level funding, partner support, and commercial support.

## 7. Validate Partner Brief

Review partner outreach material for NVIDIA, Dell, or hardware/cloud ecosystem programs.

Pass condition: the brief explains Wright's local-first engineering AI value, requested support, validation needs, and next action without adding vendor-specific runtime requirements.

## 8. Run Local Gates

Before merging to `dev`, run `scripts/check-dev-merge.sh` or document the exact local host limitation that prevented a gate. Before merging `dev` to `main`, run `scripts/check-prod-merge.sh`.


## Implementation Validation Notes

2026-07-03 implementation validation completed before review pause:

- `scripts/build-python-distributions.sh --dry-run .` passed for `wright-engineering` metadata.
- Focused release-readiness tests passed: `uv run pytest tests/test_publish_python_packages_workflow.py tests/test_python_package_metadata.py tests/test_python_package_distribution_build.py tests/test_release_policy.py tests/test_ci_cd_workflow_docs.py tests/test_docker_smoke_contract.py tests/test_community_feature_docs.py tests/test_alpha_release_readiness.py tests/test_deployment_configuration_docs.py tests/test_readme_branding_and_docker_user_guide.py tests/test_hermes_plugin_mirror_readme.py`.
- `mkdocs build --strict` passed. MkDocs reported existing informational warnings about unnaved pages and old anchors, but did not fail the strict build.
- `scripts/check-dev-merge.sh` passed before merge review. The gate reported existing mypy errors in warning mode, then completed the full backend, Hermes plugin, frontend, docs, and Playwright checks successfully.
