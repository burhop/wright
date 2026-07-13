# Python Packaging

Wright's public-alpha PyPI package is:

```text
wright-engineering
```

The ideal package name `wright` is unavailable on PyPI. Existing component names such as `wright-core` also collide or need a more careful dependency plan, so component package publication is deferred for alpha.

## What `wright-engineering` Is

`wright-engineering` is the sole public Wright Python distribution. It is a
lightweight CLI, diagnostics/configuration client, appliance status client, and
direct MCP STDIO bridge. It does not contain the full appliance or depend on
workspace-private packages. Supported Python versions are 3.11 through 3.14,
and both the wheel and source archive must clean-install independently.

It exposes commands such as:

```bash
pip install wright-engineering
wright doctor
wright appliance status --api-url http://127.0.0.1:8000
wright config --dry-run
wright mcp serve --stdio --api-url http://127.0.0.1:8000 --workspace WORKSPACE_ID
```

Docker remains the primary end-user install path for running the Wright appliance.

## Trusted Publishing

PyPI and TestPyPI use Trusted Publishing through GitHub Actions OIDC. Do not add PyPI API tokens to GitHub secrets.

Configured pending publishers:

| Index | Project | GitHub owner/repo | Workflow | Environment |
| --- | --- | --- | --- | --- |
| TestPyPI | `wright-engineering` | `burhop/wright` | `publish-python-packages.yml` | `testpypi` |
| PyPI | `wright-engineering` | `burhop/wright` | `publish-python-packages.yml` | `pypi` |

The `testpypi`, `pypi`, and `release` environments require protected review.
The build-once wheel and source archive are identified by SHA-256, installed
from TestPyPI first, and then passed unchanged to PyPI. Identical retries may
resume; different hashes require a new patch version.

## Deferred Component Packages

These packages stay workspace-local for alpha and are not promised as PyPI installs:

- `wright-core`
- `wright-tool-registry`
- `wright-workspace-service`
- `wright-agent-adapters`
- `wright-data-vault`
- `hermes-plugin-wright`

They are marked `Private :: Do Not Upload`. Publish them later only after
naming, dependency bounds, mirror behavior, and collision handling are designed
together. Never publish `wright-core`; that public name belongs to another project.
