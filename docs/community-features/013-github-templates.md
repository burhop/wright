# Feature Brief: GitHub Templates & Issue Automation

Set up GitHub Issue templates, Pull Request templates, and Discussion categories to standardize how the community reports bugs, requests features, and submits code contributions. This ensures maintainers receive structured, actionable information and contributors have clear guidance.

## What to build

### Issue Templates (YAML Forms)

Create structured issue templates using GitHub's YAML form syntax (not markdown templates) for richer, more structured submissions:

1. **Bug Report template** (`.github/ISSUE_TEMPLATE/bug_report.yml`) — A form-based template with fields for:
   - Bug description (textarea, required)
   - Steps to reproduce (textarea, required)
   - Expected behavior (textarea, required)
   - Actual behavior (textarea, required)
   - Environment details (dropdown: Docker deployment / Local development / CI/CD)
   - Wright version or commit SHA (input, required)
   - Docker version if applicable (input, optional)
   - Operating system (input, required)
   - Relevant logs or screenshots (textarea, optional)
   - Labels auto-applied: `bug`, `needs-triage`

2. **Feature Request template** (`.github/ISSUE_TEMPLATE/feature_request.yml`) — A form-based template with fields for:
   - Feature summary (input, required)
   - Use case / problem description (textarea, required) — "What problem does this solve?"
   - Proposed solution (textarea, required)
   - Alternatives considered (textarea, optional)
   - Which Wright component is affected (dropdown: API / Web UI / Agent Adapters / Tool Registry / Docker / MCP Tools / Other)
   - Willingness to contribute (dropdown: Yes, I'd like to implement this / I'd like help implementing / I'm requesting this as a user)
   - Labels auto-applied: `enhancement`, `needs-triage`

3. **Issue Chooser config** (`.github/ISSUE_TEMPLATE/config.yml`) — Configure the issue type selector to:
   - Show Bug Report and Feature Request as options
   - Add a "Question / Help" option that redirects to GitHub Discussions Q&A category (not an issue template)
   - Add a "Security Vulnerability" option that redirects to SECURITY.md (not a public issue)

### Pull Request Template

4. **PR template** (`.github/PULL_REQUEST_TEMPLATE.md`) — A checklist that contributors see when opening a PR:
   - Description of changes (what and why)
   - Related issue number (e.g., "Closes #123")
   - Checklist items:
     - [ ] I have read CONTRIBUTING.md
     - [ ] My changes follow the project's coding standards
     - [ ] I have added/updated tests for my changes (if applicable)
     - [ ] I have updated documentation (if applicable)
     - [ ] My changes do not introduce breaking changes
     - [ ] All existing tests pass (`make test` or equivalent)
     - [ ] My branch is up to date with the target branch
   - For spec-kit features: additional checklist items:
     - [ ] Spec-kit artifacts (spec.md, plan.md, tasks.md) are updated
     - [ ] Changes comply with constitution.md

### GitHub Discussions

5. **Enable and configure GitHub Discussions** with categories:
   - **Announcements** (maintainers only) — Release notes, breaking changes, project updates
   - **Q&A** (threaded, with answered marking) — Technical help and usage questions
   - **Ideas** — Feature brainstorming before formal feature requests
   - **Show & Tell** — Community members sharing what they've built with Wright
   - Document the category setup instructions for the repo owner (Discussions are enabled via GitHub Settings, not files)

### Dependency Management

6. **Dependabot configuration** (`.github/dependabot.yml`) — Automated dependency update PRs for:
   - Python dependencies (pip ecosystem, check weekly)
   - npm dependencies (check weekly)
   - GitHub Actions (check weekly)
   - Docker base images (check weekly)
   - Group minor/patch updates into single PRs to reduce noise
   - Set reasonable limits (max 5 open PRs per ecosystem)

### Labels

7. **Standard label set** — Document a recommended set of GitHub labels for the repo owner to create:
   - Priority: `P0-critical`, `P1-high`, `P2-medium`, `P3-low`
   - Type: `bug`, `enhancement`, `documentation`, `question`, `security`
   - Status: `needs-triage`, `confirmed`, `in-progress`, `blocked`, `wontfix`
   - Component: `api`, `web-ui`, `docker`, `agents`, `tools`, `ci-cd`
   - Contributor: `good first issue`, `help wanted`, `hacktoberfest`
   - Include a script or markdown table documenting each label's name, color, and description

## Constraints

- All templates must use GitHub's YAML form syntax (not markdown) for issue templates
- Do not modify any source code, Docker files, or existing CI/CD workflows
- Do not modify README.md or community health files (those are separate features)
- The PR template should be lightweight enough that it doesn't discourage small contributions
- Dependabot must not create excessive noise — use grouping and limits
