# Container Publishing

Wright's canonical alpha appliance identity is:

```text
ghcr.io/burhop/wright@sha256:<digest>
```

GHCR is canonical. Docker Hub is an optional byte-identical manifest mirror
using protected `dockerhub` credentials; it never rebuilds the image.

## Tag Policy

- Release and SHA tags point to the already-tested immutable digest.
- Prerelease tags such as `v0.1.0-alpha.1`, `v0.1.0-beta.1`, and `v0.1.0-rc.1` do not move `latest`.
- Stable tags may move `latest` only after post-promotion verification.

## Platform Policy

`linux/amd64` is the only released target. `linux/arm64`, GPU-enabled workflows,
and NVIDIA Container Toolkit assumptions are deferred until every binary input
is architecture-aware and the exact digest passes a native arm64 smoke test.

## Build-once evidence

The release train pins base/tool inputs, builds one candidate, records its
digest, blocks fixable High/Critical findings unless a reviewed unexpired
exception applies, and binds smoke, inventory, SPDX SBOM, provenance,
promotion, mirror, and verification to that digest. GitHub Release publication
is last. See [Release Runbook](release-runbook.md) and
[Release Recovery](release-recovery.md).

## Public Listing Requirements

Container listings must state that Wright is public-alpha and bring-your-own-AI, and must link to:

- Repository: https://github.com/burhop/wright
- Docs: https://burhop.github.io/wright/
- Issues: https://github.com/burhop/wright/issues
- Security policy: https://github.com/burhop/wright/security/policy
- Releases: https://github.com/burhop/wright/releases
- Support contact: `wright@makerengineer.com`
- Sponsorship: https://github.com/sponsors/burhop
