# Release Train Contract

## Entry conditions

The release train accepts one reviewed source commit and product version. It rejects a dirty tree, non-release ref, mismatched root metadata/tag/changelog/labels, unsupported version, or an existing evidence identity with different subjects.

## Build-once guarantees

1. The Python build job is the only producer of the primary wheel and sdist.
2. The OCI candidate job is the only producer of the release image manifest.
3. Every downstream job downloads or resolves subjects by recorded SHA-256/digest.
4. No publish, promote, mirror, verify, docs, or GitHub Release job invokes a package or image build.

## Required stage graph

```text
preflight + required CI
  -> python-build -> python-content/install-matrix -> TestPyPI verify
  -> OCI-build -> digest smoke/scan/SBOM/provenance verify
  -> protected approval
  -> PyPI exact-file promotion + OCI digest promotion
  -> optional byte-identical mirror
  -> post-publication verification
  -> versioned documentation
  -> GitHub Release (last)
```

All incoming required dependencies must succeed. Optional mirror absence is an explicit skip; configured mirror failure blocks completion.

## Permission contract

- Default: `contents: read` only.
- Python publication: `id-token: write`, no contents/packages write.
- OCI candidate/promotion: `packages: write` only where pushing/copying is required.
- Attestation: `id-token: write`, `attestations: write`, and subject-specific package permission.
- Documentation: only its deployment permission.
- GitHub Release: `contents: write` only in the terminal job.

Protected environments: `testpypi`, `pypi`, `release`, and `dockerhub` where configured.

## Rehearsal contract

Dry-run mode may build local artifacts and images and must validate every transition/evidence field. It must reject credentials and disable registry upload, tag creation, docs deployment, and GitHub Release mutation. Its terminal result states `rehearsal`, never `published`.

## Retry contract

An identical version/commit/hash/digest set may resume incomplete stages. Any differing primary subject under the same version produces a conflict. Artifacts are rebuilt only under a new release identity.
