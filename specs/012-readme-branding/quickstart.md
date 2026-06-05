# Quickstart Guide: README Overhaul & Branding

This guide describes how to verify and validate the README changes and visual assets created in this feature.

## 1. Local Verification

Verify that all assets exist in their respective directories:
```bash
ls -la docs/images/wright-logo.svg docs/images/wright-logo.png docs/images/social-preview.png
```

Verify that the root directory does not contain loose test-runs screenshots:
```bash
ls -la screenshot_*.png 2>/dev/null || echo "Clean root (no loose screenshots)"
```

## 2. Visual and Layout Check

Open the project `README.md` in a Markdown viewer or locally in your browser. Ensure the following layout checklist passes:

* **Logo**: The logo is centered at the top of the file.
* **Badges**: All 6 shields.io badges render correctly:
  * CI Build
  * MIT License
  * Docker Pulls
  * Python version
  * Node.js version
  * GitHub stars
* **Why Wright?**: The problem and local solution are clearly laid out.
* **UI Showcase**: The screenshots load from the `docs/images/` path with descriptive captions.
* **Mermaid Flowchart**: The diagram renders correctly, showing top-down request pathways.

## 3. GitHub Preview Validation (Pre-Merge)

1. Push your branch `012-readme-branding` to GitHub.
2. Navigate to `https://github.com/burhop/wright/tree/012-readme-branding`.
3. Check the rendered README page. Ensure that:
   * No badge returns an error.
   * The Mermaid diagram renders successfully (no syntax warnings).
   * All images (`wright-logo.svg`, `screenshot_*.png`) load correctly from the relative paths.
