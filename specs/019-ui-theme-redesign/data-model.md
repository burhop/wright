# Data Model & Schema Design: UI Themes

## 1. Setup Status API Response Schema
The `/api/setup/status` backend route returns system details. We will expand this schema to include the active theme configuration.

### Entity: `SetupStatusResponse` (FastAPI / Pydantic Model)
* **Fields**:
  * `is_configured` (boolean): `true` if backend LLM API URL is configured.
  * `llm_api_url` (string, optional): Base URL for LLM API requests.
  * `active_agent` (string): Active agent identifier (e.g., `"hermes"`).
  * `theme` (string): Current application theme (must be `"dark"` or `"light"`).

---

## 2. CSS Design Tokens Schema
The design system properties are defined in `design-tokens.css` using custom properties.

### Entity: `ThemeVariables`
Every theme must define the following CSS custom properties:
* **Backgrounds & Surfaces**:
  * `--color-neutral`: Primary application background color.
  * `--color-surface`: Card, dashboard panels, and modal surface color.
  * `--color-surface-subtle`: Secondary/inset surface color.
  * `--color-surface-hover`: Hover state highlights for clickable cards/list items.
* **Text & Typography**:
  * `--color-primary`: Main body copy and header text color.
  * `--color-secondary`: Accents, active indicators, and secondary icons.
  * `--color-accent`: Link hover highlights and system tags.
* **Borders & Shadows**:
  * `--color-border`: Container boundary outline color.
  * `--color-border-hover`: Hover boundary outline.
  * `--color-border-glow`: Box shadow/glow effects color.
