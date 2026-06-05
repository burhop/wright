# Quick Start: Release Engineering & Versioning

**Branch**: `015-release-engineering` | **Date**: 2026-06-05

This document details how to trigger new version releases, configure repository secrets, and test the release workflow.

## 1. Preparing and Tagging a Release

To trigger a release, you must push an annotated Git tag matching the SemVer pattern to GitHub.

```bash
# 1. Ensure your branch is up to date and clean
git checkout main
git pull origin main

# 2. Verify the version field in pyproject.toml is bumped (e.g. to "0.1.0")

# 3. Create an annotated git tag (which triggers the release workflow)
git tag -a v0.1.0 -m "Initial release: Wright AI mechanical engineering platform"

# 4. Push the tag to the remote repository
git push origin v0.1.0
```

## 2. Configuring Repository Secrets

For the release workflow to successfully push built Docker images to Docker Hub, you must add your credentials to GitHub:

1. Navigate to your repository page on GitHub.
2. Go to **Settings** -> **Secrets and variables** -> **Actions**.
3. Click **New repository secret** and add:
   - Name: `DOCKER_USERNAME`
   - Value: `[Your Docker Hub Username]`
4. Click **New repository secret** again and add:
   - Name: `DOCKER_PASSWORD`
   - Value: `[Your Docker Hub Personal Access Token (PAT)]`

## 3. Local Verification

To check if the workflows are syntactically valid locally before tagging:

```bash
# Parse all YAML files locally using Python safe loader
python -c "import yaml, glob; [yaml.safe_load(open(f)) for f in glob.glob('.github/**/*.yml', recursive=True)]"
```
