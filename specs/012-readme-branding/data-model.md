# Data Model: README Overhaul & Branding

This feature defines the structural elements of the visual assets and the layout hierarchy for the restructured landing page.

## Visual Asset Models

| Asset Name | Target Path | File Format | Layout / Dimensions | Key Content / Requirements |
|---|---|---|---|---|
| Vector Logo | `docs/images/wright-logo.svg` | SVG (XML) | Square / Scalable | Scalable vector graphic combining gear & neural paths. |
| Raster Logo | `docs/images/wright-logo.png` | PNG | 512×512px | High-resolution exported raster logo. |
| Social Preview | `docs/images/social-preview.png` | PNG | 1280×640px | Logo, tagline, and icons showcasing key local features. |

## README Section Layout Hierarchy

The `README.md` file will be refactored to conform to the following schema structure:

| Section Level | Header Name | Content / Components | Verification Rules |
|---|---|---|---|
| `H1` | Centered Hero | Logo, Tagline, Shields.io Badge row | Centered layout, valid links for all 6 badges. |
| `H2` | Why Wright? | Problem (IP/Cloud APIs), Solution (Local LLMs) | Compelling narrative, mentions offline-first focus. |
| `H2` | Key Features | Emojified cards (CAD, FEA, Mfg, LLMs, Local) | Scannable format, emojis properly rendered. |
| `H2` | User Interface | Screenshots: Chat, Tool Registry, File Vault | Relocated image embeds with descriptive captions. |
| `H2` | Quick Start | copy-pasteable Docker commands | Under 4 commands, no setup wizard bloat. |
| `H2` | Architecture | Component Flow Mermaid diagram, existing text | Valid Mermaid markup, top-down execution flow. |
| `H2` | Contributing | Link to `CONTRIBUTING.md`, Good First Issues | Active relative link to CONTRIBUTING.md. |
| `H2` | License & Star History | MIT License note, Star History chart link | Functional external star-history.com graph. |
