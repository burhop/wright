# Container Publishing

Wright's alpha appliance image names are:

```text
burhop/wright:<tag>
ghcr.io/burhop/wright:<tag>
```

Docker Hub is enabled for alpha through the repository secrets `DOCKERHUB_USERNAME` and `DOCKERHUB_TOKEN`. GHCR remains the GitHub-native registry path and must continue to work without Docker Hub credentials.

## Tag Policy

- Release tags publish immutable matching image tags.
- Prerelease tags such as `v0.1.0-alpha.1`, `v0.1.0-beta.1`, and `v0.1.0-rc.1` do not move `latest`.
- Stable tags may move `latest` after release review.

## Platform Policy

`linux/amd64` is the smoked alpha target. `linux/arm64`, GPU-enabled workflows, and NVIDIA Container Toolkit assumptions are deferred until the release workflow builds and validates those variants.

## Public Listing Requirements

Container listings must state that Wright is public-alpha and bring-your-own-AI, and must link to:

- Repository: https://github.com/burhop/wright
- Docs: https://burhop.github.io/wright/
- Issues: https://github.com/burhop/wright/issues
- Security policy: https://github.com/burhop/wright/security/policy
- Releases: https://github.com/burhop/wright/releases
- Support contact: `wright@makerengineer.com`
- Sponsorship: https://github.com/sponsors/burhop
