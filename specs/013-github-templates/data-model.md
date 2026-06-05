# Data Model: GitHub Templates & Issue Automation

**Branch**: `013-github-templates` | **Date**: 2026-06-05

This document defines the schema structure, fields, validation states, and config parameters for the GitHub templates and Dependabot integration.

## 1. Issue Form schemas (YAML)

### Bug Report Form (`bug_report.yml`)
* **Inputs**:
  - `description`: Textarea (Required)
  - `reproduction_steps`: Textarea (Required)
  - `expected_behavior`: Textarea (Required)
  - `actual_behavior`: Textarea (Required)
  - `environment`: Dropdown (Required, options: `Docker deployment`, `Local development`, `CI/CD`)
  - `version`: Input text (Required)
  - `docker_version`: Input text (Optional)
  - `operating_system`: Input text (Required)
  - `logs`: Textarea (Optional)
* **Metadata**:
  - Name: "Bug Report"
  - Description: "Report a bug or unexpected behavior in the Wright toolbox"
  - Labels: `bug`, `needs-triage`

### Feature Request Form (`feature_request.yml`)
* **Inputs**:
  - `summary`: Input text (Required)
  - `problem_description`: Textarea (Required)
  - `proposed_solution`: Textarea (Required)
  - `alternatives`: Textarea (Optional)
  - `component`: Dropdown (Required, options: `API`, `Web UI`, `Agent Adapters`, `Tool Registry`, `Docker`, `MCP Tools`, `Other`)
  - `willingness`: Dropdown (Required, options: `Yes, I'd like to implement this`, `I'd like help implementing`, `I'm requesting this as a user`)
* **Metadata**:
  - Name: "Feature Request"
  - Description: "Suggest an idea or enhancement for the Wright toolbox"
  - Labels: `enhancement`, `needs-triage`

## 2. Dependabot Configuration Schema (`dependabot.yml`)

* **Ecosystems**:
  - `pip` (Python dependencies)
    - Path: `/` (checked weekly, grouped, max 5 PRs)
  - `npm` (Node dependencies)
    - Path: `/apps/web/` (checked weekly, grouped, max 5 PRs)
  - `github-actions` (CI actions)
    - Path: `/` (checked weekly, grouped, max 5 PRs)
  - `docker` (Docker files)
    - Path: `/` (checked weekly, grouped, max 5 PRs)
