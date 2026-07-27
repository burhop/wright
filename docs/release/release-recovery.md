# Release Recovery

Recovery preserves immutable subjects. Never overwrite PyPI files or move OCI version/SHA references.

## Retry and partial completion

Compare the release identity, Python SHA-256 values, and OCI digest with retained evidence. Identical subjects may resume missing stages. A differing subject under the same version is a conflict: stop and create a corrected patch version.

## Python correction and yank

PyPI files are immutable. Publish a corrected patch. Yank only when the release is broken, incompatible, vulnerable, or contains prohibited material; record the reason and replacement. Do not yank solely because a newer version exists or because an artifact is larger than desired after sensitive-content review passes.

## OCI quarantine and alias restore

Keep immutable version and SHA references for audit. Mark the bad digest quarantined in release evidence, stop mutable aliases from pointing to it, and restore `latest` only to a digest already recorded as verified. Publish a patch candidate for the fix. Do not rebuild an old version.

## Mirror divergence

If Docker Hub resolves to a different manifest, hold the GitHub Release as draft, quarantine the mirror reference, and recopy from the canonical GHCR digest only after credentials/repository ownership are revalidated. Canonical GHCR evidence remains authoritative.

## GitHub Release and documentation

Keep the GitHub Release absent or draft until package, canonical image, configured mirror, attestations, and versioned documentation are verified. If a terminal job fails, resume only after all evidence subjects remain identical.

## Evidence retention

Retain release identity, candidate files/hashes, archive content manifests, OCI digest/platform/labels, vulnerability decision and exceptions, SBOM/provenance subjects, approvals, promotions, verification output, optional skips, and recovery decisions. Redact credentials and secret values.
