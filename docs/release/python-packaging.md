# Python Packaging

Wright's public-alpha PyPI package is:

```text
wright-engineering
```

The ideal package name `wright` is unavailable on PyPI. Existing component names such as `wright-core` also collide or need a more careful dependency plan, so component package publication is deferred for alpha.

## What `wright-engineering` Is

`wright-engineering` is the sole public Wright Python distribution and contains
the complete native application: dependency-light Hermes entry point, lifecycle
bootstrap, packaged API/UI, canonical catalog, provider-neutral gateway, and a
bounded `runtime` extra. Internal module sources are bundled into this wheel; it
does not resolve workspace-private distributions from public indexes. Supported
Python versions are 3.11 through 3.14, and both the wheel and source archive must
produce equivalent policy-controlled application contents.

It exposes commands such as:

```bash
python -m pip install wright-engineering==<version>  # release diagnosis only
wright doctor
wright appliance status --api-url http://127.0.0.1:8000
wright config --dry-run
wright mcp serve --stdio --api-url http://127.0.0.1:8000 --workspace WORKSPACE_ID
```

The normal user install is performed by a released Hermes
`python-distribution-v1` interface, not by a manual pip command. Docker remains
the mandatory turnkey appliance path for every release.

The base dependency set stays small enough for Hermes plugin import. Runtime
dependencies are declared only in `wright-engineering[runtime]` and locked in
the packaged `runtime-extra-lock.json`. The release build records that lock, UI
manifest, compatibility contract, wheel/sdist content manifests, and hashes.

## Trusted Publishing

PyPI and TestPyPI use Trusted Publishing through GitHub Actions OIDC. Do not add PyPI API tokens to GitHub secrets.

Configured project publishers:

| Index | Project | GitHub owner/repo | Workflow | Environment |
| --- | --- | --- | --- | --- |
| TestPyPI | `wright-engineering` | `burhop/wright` | `release.yml` | `testpypi` |
| PyPI | `wright-engineering` | `burhop/wright` | `release.yml` | `pypi` |

The `testpypi`, `pypi`, and `release` environments require protected review.
The PyPI publishing action must remain directly in the top-level `release.yml`;
PyPI Trusted Publishing does not support using a reusable workflow as the
publisher identity. The reusable OCI build is unaffected by this restriction.
The build-once wheel and source archive are identified by SHA-256, installed
from TestPyPI first, and then passed unchanged to PyPI. Identical retries may
resume; different hashes require a new patch version.

## Deferred Component Packages

These packages stay private and are never native runtime dependencies from a
public index:

- `wright-core`
- `wright-tool-registry`
- `wright-workspace-service`
- `wright-agent-adapters`
- `wright-data-vault`
- `hermes-plugin-wright`

They are marked `Private :: Do Not Upload`. Publish them later only after
naming, dependency bounds, mirror behavior, and collision handling are designed
together. Never publish `wright-core`; that public name belongs to another project.
