# Pull Request Submission Checklist

When opening a Pull Request (PR) to merge code changes, follow these guidelines.

---

## 1. Branch Naming Conventions
Ensure feature branches are named correctly:
*   `016-docs-site` (feature specific)
*   `feat/your-feature-name` (general features)
*   `fix/bug-fix-name` (bug fixes)

---

## 2. Pre-Submission Checklist

Before submitting the PR, execute the following validation steps:

- [ ] Run `make check` to ensure all tests, linting, and typechecks pass successfully.
- [ ] Before merging a feature branch to `dev`, run `make check-dev-merge`.
- [ ] Before merging `dev` to `main`, run `make check-prod-merge`.
- [ ] Verify that no credentials, passwords, or API secrets have been hardcoded or committed to git.
- [ ] For user interface modifications, ensure screenshots or video recordings demonstrate the visual change.
- [ ] Verify that your modifications have not changed core app configurations unless explicitly requested.

`make check` is the fast local development gate and is appropriate while a
branch is still moving. The merge gates are intentionally heavier because they
mirror CI and release checks. If CI finds a class of failure that the local
merge gate missed, update the relevant script and this checklist before merging
the fix.

---

## 3. Pull Request Template

We use the standard GitHub PR template located at `.github/PULL_REQUEST_TEMPLATE.md`. Make sure to fill out all sections:
*   **Description**: High-level overview of the problem and your solution.
*   **Testing**: Details on how the changes were verified.
*   **Checklist**: Standard formatting and verification confirmations.
