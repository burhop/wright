# Release Recovery

Recovery preserves immutable subjects. Never overwrite PyPI files or move OCI version/SHA references.

Native Hermes and Docker are independent mandatory production paths. Recovering
one never permits the other to be skipped or marked complete.

## Native Hermes channel and runtime recovery

If stable Hermes channel activation cannot be verified, restore its prior
immutable version pointer through the protected channel service and retain both
the failed activation ID and the restored version in recovery evidence. Never
replace an already-published wheel under the same version.

If public native verification fails after activation, stop final documentation
and GitHub Release jobs, restore the previous channel pointer, and use
`/wright rollback` only when the packaged schema bounds permit it. The runtime
keeps its predecessor until health succeeds. A `recovery_required` result is a
real stop condition: use the recorded backup and manifest rather than silently
discarding data. Default uninstall preserves `HERMES_HOME/wright/data`; purge is
separate and requires the exact confirmation code for the disclosed path.

The legacy Git mirror is migration support for Hermes 0.18 and older. Publishing
or repairing it does not repair the native package channel and does not satisfy
native release evidence.

## Retry and partial completion

Compare the release identity, Python SHA-256 values, and OCI digest with retained evidence. Identical subjects may resume missing stages. A differing subject under the same version is a conflict: stop and create a corrected patch version.

## Python correction and yank

PyPI files are immutable. Publish a corrected patch. Yank only when the release is broken, incompatible, vulnerable, or contains prohibited material; record the reason and replacement. Do not yank solely because a newer version exists or because an artifact is larger than desired after sensitive-content review passes.

## OCI quarantine and alias restore

Keep immutable version and SHA references for audit. Mark the bad digest quarantined in release evidence, stop mutable aliases from pointing to it, and restore `latest` only to a digest already recorded as verified. Publish a patch candidate for the fix. Do not rebuild an old version.

## Mirror divergence

If Docker Hub resolves to a different manifest, hold the GitHub Release as draft, quarantine the mirror reference, and recopy from the canonical GHCR digest only after credentials/repository ownership are revalidated. Canonical GHCR evidence remains authoritative.

If PyPI and GHCR already passed but Docker Hub did not, do not rerun Python
publication or rebuild the OCI image. Dispatch
`.github/workflows/recover-dockerhub-release.yml` from `main` with the existing
release tag and the GHCR digest recorded in `release-evidence.json`. The
recovery validates the tag commit and retained evidence, copies that exact
digest to the version tag and stable `latest`, verifies both publicly, and
retains separate recovery evidence as an artifact of the protected workflow
run. Finalized GitHub Releases are immutable, so recovery intentionally does
not modify the existing release; the evidence records the workflow run URL.

## GitHub Release and documentation

Keep the GitHub Release absent or draft until the package, released-Hermes
native lifecycle on every claimed platform, canonical image, required Docker
Hub distribution, attestations, and versioned documentation are verified. If a
terminal job fails, resume only after all evidence subjects remain identical.

## Evidence retention

Retain release identity, candidate files/hashes, archive content manifests,
runtime-extra lock, compatibility hash, released Hermes capability/version,
stable-channel activation, platform lifecycle results, forbidden-executable
audit, OCI digest/platform/labels, vulnerability decision and exceptions,
SBOM/provenance subjects, approvals, promotions, verification output, optional
non-native skips, and recovery decisions. Redact credentials and secret values.
