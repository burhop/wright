# Quickstart Guide: Repo Hygiene & Legal Foundation

This guide explains how to verify and maintain the repository hygiene files added in this feature.

## Verifying Community Health Files Locally

Once implementation is complete, run the following checks to ensure all files are in place and properly populated:

1. **Verify Files Exist**:
   ```bash
   ls -la LICENSE CODE_OF_CONDUCT.md SECURITY.md SUPPORT.md CONTRIBUTING.md .github/CODEOWNERS
   ```

2. **Verify Git Exclusions**:
   Ensure that files like `state.db` or local logs are ignored by Git. Run:
   ```bash
   git status --ignored
   ```
   Verify that any temporary logs (e.g. `phase1.log`, `ps_debug.log`) or database files (`state.db`) are listed under "Ignored files" and not tracked in the active staging area.

3. **Verify Documentation References**:
   Ensure that the screenshots have been relocated to the `docs/images/` folder:
   ```bash
   ls -la docs/images/
   ```

## Verifying on GitHub (Post-Push)

Once the changes are merged to the default branch on GitHub:

1. **Check Community Profile**:
   * Navigate to your repository on GitHub.
   * Click on the **Insights** tab, then select **Community Standards** (or go to `https://github.com/<owner>/<repo>/community`).
   * Verify that all indicators (License, Code of Conduct, Contributing, Security Policy, Support) have a green checkmark.

2. **Check Code Owners**:
   * Open a test Pull Request on GitHub modifying a backend or frontend file.
   * Verify that GitHub automatically adds `@burhop` as a required reviewer on the PR sidebar.

3. **Verify Metadata & Topics**:
   * Follow the steps in `docs/metadata-guide.md` to set up the description and 20 topic tags via the GitHub web interface.
   * Verify that search queries on GitHub for those topics return the repository.
