# Release Runbook

This runbook describes the prepared release train. Feature 047 authorizes rehearsal only; do not create tags or publish artifacts without explicit release authorization.

## External prerequisites

Repository administrators must configure protected `testpypi`, `pypi`, `release`, and `dockerhub` environments with tag restrictions and required reviewers. PyPI and TestPyPI use separate OIDC Trusted Publisher records for `.github/workflows/publish-python-packages.yml`. Do not store PyPI tokens.

## Rehearsal

1. Start from a clean reviewed commit whose root version and changelog agree.
2. Run `scripts/release-preflight.py --dry-run` with the intended tag and full commit.
3. Build the public wheel and sdist once with `scripts/build-python-distributions.sh`.
4. Run `scripts/release-rehearsal.py --dry-run`; retain the evidence manifest and content manifests.
5. Run the release tests and `scripts/check-dev-merge.sh`.

The rehearsal rejects credentials and performs no TestPyPI, PyPI, registry, documentation, tag, or GitHub Release mutation.

## Protected production order

1. Preflight and required CI.
2. Build one Python candidate set and one `linux/amd64` OCI candidate.
3. Validate exact wheel/sdist installs and exact-digest smoke, scan, SBOM, and provenance.
4. Publish the recorded Python files to TestPyPI and install/smoke that version.
5. Obtain protected approval.
6. Publish the same Python files to PyPI and promote the tested OCI digest in GHCR.
7. If configured, copy the same OCI manifest to Docker Hub and verify digest identity.
8. Perform post-publication package, digest, and attestation verification.
9. Deploy versioned documentation.
10. Publish the GitHub Release last.

Any required failure stops later jobs. An absent optional Docker Hub mirror must be recorded as skipped; a configured mirror that diverges is a failure.

## Consumer verification

```bash
python -m pip install --no-deps wright-engineering==VERSION
wright --version
wright doctor
docker pull ghcr.io/burhop/wright@sha256:DIGEST
gh attestation verify oci://ghcr.io/burhop/wright@sha256:DIGEST -R burhop/wright
```

Never substitute a mutable tag when verifying the released OCI subject.
