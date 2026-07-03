# Python Packaging

Wright's public-alpha PyPI package is:

```text
wright-engineering
```

The ideal package name `wright` is unavailable on PyPI. Existing component names such as `wright-core` also collide or need a more careful dependency plan, so component package publication is deferred for alpha.

## What `wright-engineering` Is

`wright-engineering` is a small public helper and discovery package. It can expose CLI checks such as:

```bash
pip install wright-engineering
wright doctor
```

Docker remains the primary end-user install path for running the Wright appliance.

## Trusted Publishing

PyPI and TestPyPI use Trusted Publishing through GitHub Actions OIDC. Do not add PyPI API tokens to GitHub secrets.

Configured pending publishers:

| Index | Project | GitHub owner/repo | Workflow | Environment |
| --- | --- | --- | --- | --- |
| TestPyPI | `wright-engineering` | `burhop/wright` | `publish-python-packages.yml` | `testpypi` |
| PyPI | `wright-engineering` | `burhop/wright` | `publish-python-packages.yml` | `pypi` |

The `pypi` GitHub environment should require manual approval before a real PyPI upload.

## Deferred Component Packages

These packages stay workspace-local for alpha and are not promised as PyPI installs:

- `wright-core`
- `wright-tool-registry`
- `wright-workspace-service`
- `wright-agent-adapters`
- `wright-data-vault`
- `hermes-plugin-wright`

Publish them later only after naming, dependency bounds, mirror behavior, and collision handling are designed together.
