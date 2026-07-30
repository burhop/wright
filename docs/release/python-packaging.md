# Python Packaging

Wright's sole public Python distribution is `wright-engineering`; the ideal
name `wright` is unavailable on PyPI.

## Application role

The distribution contains the complete manager-neutral application: lifecycle
bootstrap, packaged API/UI, canonical catalog, provider-neutral gateway, manager
profile generation, and a bounded `runtime` extra. It does not contain a Hermes
plugin entry point and does not depend on manager runtimes. Internal module
sources are bundled into the wheel rather than resolved as private packages.

Supported Python versions are 3.11 through 3.14. Useful direct-manager and
diagnostic commands include:

```bash
python -m pip install 'wright-engineering[runtime]==<version>'
wright doctor
wright appliance status --api-url http://127.0.0.1:8000
wright mcp serve --stdio --api-url http://127.0.0.1:8000 --workspace WORKSPACE
```

Hermes users do not run that install manually: its thin Git adapter resolves the
exact compatible wheel. Codex may launch the installed command or
connect to the running HTTP service. Docker remains mandatory for every release.

## Trusted Publishing

PyPI and TestPyPI use GitHub Actions OIDC Trusted Publishing; do not add PyPI
API tokens to GitHub secrets.

| Index | Project | Workflow | Environment |
| --- | --- | --- | --- |
| TestPyPI | `wright-engineering` | `release.yml` | `testpypi` |
| PyPI | `wright-engineering` | `release.yml` | `pypi` |

The publishing action stays in the top-level workflow because Trusted
Publishing does not support a reusable workflow as the publisher identity. The
build-once wheel and sdist are identified by SHA-256, installed from TestPyPI,
and passed unchanged to PyPI.

## Private component packages

`wright-core`, `wright-tool-registry`, `wright-workspace-service`,
`wright-agent-adapters`, `wright-data-vault`, and `hermes-plugin-wright` are
marked `Private :: Do Not Upload`. Never publish `wright-core`; that public name
belongs to another project.
