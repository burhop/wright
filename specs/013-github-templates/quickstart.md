# Quick Start: GitHub Templates & Issue Automation

**Branch**: `013-github-templates` | **Date**: 2026-06-05

This document details how to test the issue templates, PR template, and Dependabot configuration locally or on GitHub.

## 1. Syntax Validation

Ensure all YAML configurations follow correct schemas using basic syntax parsing tools (e.g. `yamllint` or Python's `pyyaml`):

```bash
# Verify dependabot and issue templates are valid YAML
python -c "import yaml, glob; [yaml.safe_load(open(f)) for f in glob.glob('.github/**/*.yml', recursive=True)]"
```

## 2. GitHub Local Template Preview (Optional)

Since GitHub YAML forms cannot be completely previewed offline, they can be tested by committing them to a personal sandbox repository on GitHub and opening the "New Issue" page.

## 3. Standard Label Creation

A set of standard labels needs to be created on the GitHub repository. To automate this, you can run a curl script using the GitHub CLI (`gh`):

```bash
# Example script to create type and status labels
gh label create bug --color "d73a4a" --description "Something isn't working"
gh label create enhancement --color "a2eeef" --description "New feature or request"
gh label create needs-triage --color "fbca04" --description "New issues requiring triage"
```
