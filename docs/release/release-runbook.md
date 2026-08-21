# Release Runbook

This is the production release order. A rehearsal must not publish artifacts;
rehearsals do not create tags. Production publication requires explicit
authorization.

## External prerequisites

Protect the `testpypi`, `pypi`, `release`, and `dockerhub` GitHub environments.
PyPI and TestPyPI use separate OIDC Trusted Publisher records for
`.github/workflows/release.yml`; do not store PyPI tokens. Docker Hub requires
its protected username and token. The Hermes mirror sync requires its scoped
deploy key.

The compatibility contract names the supported manager protocols. Release
verification must use Hermes' real Git interface and released manager profiles,
not a synthetic Python plugin capability.

## Rehearsal

1. Start from a clean reviewed commit whose root version and changelog agree.
2. Run `scripts/release-preflight.py --dry-run`.
3. Build the complete `wright-engineering` wheel/sdist and OCI candidate once.
4. Run local Hermes Git-adapter and direct Codex contract evidence.
5. Run `scripts/release-rehearsal.py --dry-run` and retain its manifests.
6. Run release tests and `scripts/check-dev-merge.sh`.

The rehearsal performs no TestPyPI, PyPI, registry, tag, documentation, or
GitHub Release mutation.

For engineering-program rehearsal, also validate the exact compatibility-
evidence schema and record artifact digest, platform, architecture, manager and
storage profiles, source isolation, forbidden-executable audit, complete
lifecycle/persistence/offline checks, and whether the result is supporting.
Unavailable hosts are recorded as skipped/non-supporting. Do not substitute
fixture, contract, another architecture, or an installed source checkout for
candidate-bound evidence. Support-diagnostic exports used during rehearsal
remain local and must pass the proprietary-data/reusable-authority scan.

## Protected production order

1. Preflight and required CI.
2. Build one Python candidate set and one OCI candidate.
3. Validate wheel/sdist installs and OCI smoke, scan, SBOM, and provenance.
4. Publish the recorded Python files to TestPyPI and install/smoke that version.
5. Obtain protected approval and publish the same files to PyPI.
6. Verify the released Hermes Git interface, installed adapter commit, mirror
   provenance, and the direct Codex MCP profile identity.
7. Promote the tested OCI digest to GHCR and copy the same manifest to Docker
   Hub; verify version and stable `latest` aliases.
8. On clean Windows, Linux, and macOS runners, exercise the published Hermes
   install/start/status/doctor/stop/update/rollback/uninstall/purge lifecycle and
   direct-manager MCP probes.
9. Assemble exact release evidence and verify public packages, digests, and
   attestations.
10. Deploy versioned documentation.
11. Publish the GitHub Release last.

Any missing manager evidence, adapter identity mismatch, Docker Hub failure, or
digest divergence leaves the release incomplete.

## Integration lessons and failure handling

- Treat the merge, the `main` push checks, and the production release as three
  separate gates. Do not report the integration complete until all three pass.
- Exercise the full native lifecycle on Linux, macOS, and Windows before the
  production tag, then repeat it against the publicly installed package.
- Build Python and OCI candidates once. Promote the recorded files and digest;
  do not rebuild between validation and publication.
- PyPI, TestPyPI, and container registries are eventually consistent. Public
  verification should use bounded retry and backoff. If publication succeeded
  but lookup has not propagated, wait for the expected files or digest and
  rerun only verification and its downstream jobs. Never republish an existing
  version to work around propagation.
- Require the complete production-readiness check set in GitHub branch
  protection for `dev` to `main`. If GitHub reports no required checks, treat
  that as a repository-control gap rather than assuming the checks are
  enforced.
- Keep the GitHub Release last so its presence means PyPI, GHCR, Docker Hub,
  native lifecycle verification, release evidence, and documentation all
  succeeded.
- When confirming that `dev` and `main` are synchronized after a PR merge,
  compare Git tree hashes. Their commit hashes normally differ because `main`
  retains merge commits.

## Consumer verification

```bash
python -m pip install --no-deps wright-engineering==VERSION
wright --version
wright doctor
hermes plugins install https://github.com/burhop/hermes-plugin-wright --enable
docker pull ghcr.io/burhop/wright@sha256:DIGEST
docker pull burhop/wright:TAG
gh attestation verify oci://ghcr.io/burhop/wright@sha256:DIGEST -R burhop/wright
```

Never substitute a mutable identity for the recorded released subject.
