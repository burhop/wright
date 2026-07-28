# Release Runbook

This runbook describes the prepared release train. Feature 047 authorizes rehearsal only; do not create tags or publish artifacts without explicit release authorization.

## External prerequisites

Repository administrators must configure protected `testpypi`, `pypi`,
`release`, and `dockerhub` environments with tag restrictions and required
reviewers. PyPI and TestPyPI use separate OIDC Trusted Publisher records for the
top-level `.github/workflows/release.yml`, with environments `pypi` and
`testpypi` respectively. Keep the PyPI publishing action in that top-level
workflow because PyPI does not support reusable workflows as Trusted Publisher
identities. Do not store PyPI tokens. The `release` environment also holds the
protected Hermes package-channel credential. Record
`HERMES_PACKAGE_PLUGIN_VERSION` only after the released CLI passes
`python-distribution-v1`; the Git-only Hermes 0.18 interface is not eligible.

## Rehearsal

1. Start from a clean reviewed commit whose root version and changelog agree.
2. Run `scripts/release-preflight.py --dry-run` with the intended tag and full commit.
3. Build the complete public wheel and sdist once with
   `scripts/build-python-distributions.sh`; retain native build evidence, the UI
   manifest, compatibility hash, and runtime-extra lock.
4. Run `scripts/test-native-hermes-install.py` in the local candidate fixture on
   every claimed platform. The harness must report source isolation and zero
   forbidden executables.
5. Run `scripts/release-rehearsal.py --dry-run`; retain the evidence manifest and
   content manifests.
6. Run the release tests and `scripts/check-dev-merge.sh`.

The rehearsal rejects credentials and performs no TestPyPI, PyPI, registry, documentation, tag, or GitHub Release mutation.

## Protected production order

1. Preflight and required CI.
2. Build one Python candidate set and one `linux/amd64` OCI candidate.
3. Validate exact wheel/sdist installs and exact-digest smoke, scan, SBOM, and provenance.
4. Publish the recorded Python files to TestPyPI and install/smoke that version.
5. Obtain protected approval.
6. Publish the same Python files to PyPI.
7. Verify the configured released Hermes package-plugin capability, then activate
   that immutable Wright version on the protected stable Hermes channel.
8. Promote the tested OCI digest in GHCR and copy the same OCI manifest to Docker
   Hub. Verify the version tag and, for
   stable releases, `latest` resolve to the tested digest.
9. From clean Windows, Linux, and macOS profiles, install through released Hermes
   and exercise install/start/status/doctor/stop/update/rollback/uninstall/purge
   against the public files. A fixture result cannot satisfy this stage.
10. Perform post-publication package, native, digest, and attestation verification.
11. Deploy versioned documentation.
12. Publish the GitHub Release last.

Any failure stops later jobs. Missing released Hermes capability or native
platform evidence, missing Docker Hub credentials, authentication failure, an
absent tag, or digest divergence makes the production release incomplete.

## Consumer verification

```bash
python -m pip install --no-deps wright-engineering==VERSION
wright --version
wright doctor
hermes plugins install-package wright-engineering==VERSION --enable
docker pull ghcr.io/burhop/wright@sha256:DIGEST
docker pull burhop/wright:TAG
gh attestation verify oci://ghcr.io/burhop/wright@sha256:DIGEST -R burhop/wright
```

Never substitute a mutable tag when verifying the released OCI subject.
