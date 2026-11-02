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

## Development snapshots on TestPyPI

Use the existing trusted publisher in `release.yml` for an explicitly requested
development package. This mode publishes only to TestPyPI; it does not create a
release tag or enter the production PyPI, container, docs, or GitHub Release jobs.
Manual dispatch without `publish_dev` remains a non-publishing rehearsal.

The `testpypi` GitHub environment must allow the `dev` branch in addition to its
existing release-tag policy. Preserve its required reviewer and the TestPyPI
trusted-publisher binding to `release.yml` and the `testpypi` environment. A
temporary feature-branch dispatch requires an exact branch deployment rule and
the same environment review; remove that rule after integration.

```powershell
$devCommit = gh api repos/burhop/wright/git/ref/heads/dev --jq .object.sha
gh workflow run release.yml --repo burhop/wright --ref dev -f publish_dev=true -f dev_source_sha=$devCommit
```

The build checks out `dev` and refuses a different source commit. It stamps only
the disposable build checkout with a unique next-patch development version,
such as `0.1.10.dev<run-id><attempt>`. Packaged `dev-release.json` records the
exact source and workflow run. Existing packaging builds and inspects the full
API/UI wheel and sdist once; Python 3.11–3.14 install checks precede publication.
Public verification retries bounded propagation delays, compares both published
file hashes with the original candidate, installs the downloaded wheel with
runtime dependencies from PyPI, and runs CLI diagnostics outside the source tree.
This is package qualification, not engineering workflow or physical acceptance.

Use the exact version and wheel URL from the successful run to install a snapshot.
Keep TestPyPI package selection separate from runtime dependency resolution on
PyPI; do not combine the indexes with `--extra-index-url`. A Hermes adapter's
Git branch does not itself select this snapshot: the stable adapter still pins
its released runtime, and candidate selection must be configured explicitly.
If publication succeeded but verification failed, rerun verification only; never
rebuild or re-upload that same version.

## Native wheel layout validation

Run `python -m scripts.release.wheel_policy PATH.whl` with the pinned
`check-wheel-contents==0.6.3` tool. It reuses native artifact validation and runs
every generic wheel check. Exact reviewed subjects classify the copied validator
profile, common working-view layout resources, two editor icon assets and
path-addressed setup scripts. These assets keep their existing names and bytes.
An unknown duplicate group, added script, extra package root or other finding
still fails. No global W002/W004 ignore is introduced. The same owner runs in
native PR builds, the complete local merge gate and both release modes.

## Private component packages

`wright-core`, `wright-tool-registry`, `wright-workspace-service`,
`wright-agent-adapters`, `wright-data-vault`, and `hermes-plugin-wright` are
marked `Private :: Do Not Upload`. Never publish `wright-core`; that public name
belongs to another project.
