# Quick Start: Documentation Site

**Branch**: `016-docs-site` | **Date**: 2026-06-05

This document details how to serve the documentation site locally, build it for deployment validation, and review GitHub Pages integrations.

## 1. Running the Local Docs Server

You can run the MkDocs Material server locally to preview code edits in real time:

```bash
# 1. Install dependencies
pip install mkdocs-material

# 2. Run the local serve process
mkdocs serve
```

The documentation server will start and be available at:
`http://127.0.0.1:8000/`

## 2. Validating the Site Build

To ensure there are no dead links, missing pages, or markdown configuration issues:

```bash
# Run a strict local build
mkdocs build --strict
```

If the build succeeds without errors, the site is ready for release.

## 3. GitHub Pages Autodeploy

- **Workflow File**: `.github/workflows/docs-deploy.yml`
- **Trigger**: Merge or push to the `main` branch.
- **Execution**: Builds static assets and publishes them directly to the `gh-pages` branch.
- **Access**: The site will be reachable at `https://burhop.github.io/wright/`.
