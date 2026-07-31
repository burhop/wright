# Container Publishing

Wright's canonical alpha appliance identity is:

```text
ghcr.io/burhop/wright@sha256:<digest>
```

GHCR is canonical. Docker Hub is a required byte-identical distribution target
using protected `dockerhub` credentials; it never rebuilds the image. A
production release is incomplete if either registry tag is missing or resolves
to a different digest.

The engineering-tools image family is published as additive tags on the same
repositories after each exact image passes smoke validation:

```text
ghcr.io/burhop/wright:<tag>-engineering-tools-linux-amd64
ghcr.io/burhop/wright:<tag>-engineering-tools-linux-arm64
docker.io/burhop/wright:<tag>-engineering-tools-linux-amd64
docker.io/burhop/wright:<tag>-engineering-tools-linux-arm64
```

`dev` and `main` branch pushes publish moving branch-prefixed engineering-tools
tags for testing. Version tags publish immutable release-prefixed
engineering-tools tags. The Windows engineering-tools image remains a managed
profile, but publication requires a Windows runner configured for Windows
container mode.

## Tag Policy

- Release and SHA tags point to the already-tested immutable digest.
- Prerelease tags such as `v0.1.0-alpha.1`, `v0.1.0-beta.1`, and `v0.1.0-rc.1` do not move `latest`.
- Stable tags may move `latest` only after post-promotion verification.
- Stable releases update and verify `latest` in both GHCR and Docker Hub.

## Platform Policy

The standard appliance release target is `linux/amd64`. Engineering-tools
Linux variants are built and smoked on native `linux/amd64` and `linux/arm64`
runners. GPU-enabled workflows and NVIDIA Container Toolkit assumptions remain
deferred.

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
