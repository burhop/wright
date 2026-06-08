# Research: UI Redesign & Theme Architecture

## 1. Design & Typography Alignment

### Problem Analysis
* **Typography**: Inconsistent header and body copy sizes throughout the interface. Overly large fonts reduce the density of cards.
* **Layout Overlaps**: Spacing issues in the cards (such as the "Check for Updates" button overlap next to the version badge in the current UI) are caused by absolute positioning and inadequate grid column bounds.
* **Icon and Button Placement**: Action buttons and info tags are placed at varying coordinates across different cards depending on description length.

### Solutions
* **CSS Grid / Flexbox**: Transition all card components to use robust flexbox-based column structures, ensuring that tags, description content, and actions stack consistently.
* **Min/Max Heights**: Define standard min-height constraints for cards so cards in the same row align identically, while long descriptions wrap gracefully or are capped with a text-overflow clamp.
* **Typography Type Scale**: Enforce strict type hierarchy using design tokens:
  * Headers: `var(--font-size-xl)` (e.g. 24px)
  * Card Titles: `var(--font-size-lg)` (e.g. 18px)
  * Body Copy: `var(--font-size-md)` (e.g. 14px)
  * Badges/Sub-text: `var(--font-size-sm)` (e.g. 12px)

---

## 2. Configuration-Driven Theme System

### Architecture Options
1. **Option A: Pure frontend theme loading (Static Config)**:
   * Build environment variable `VITE_THEME` read at compile-time.
   * *Limitation*: Requires rebuilding the container or application to change themes.
2. **Option B: Backend config API propagation (Recommended)**:
   * Backend reads `UI_THEME` environment variable at runtime (defaults to `dark`).
   * `/api/setup/status` endpoint includes a `theme` field in its response.
   * Frontend fetches `/api/setup/status` on load, retrieves the theme value, and applies it to the document root element:
     ```javascript
     document.documentElement.setAttribute('data-theme', theme);
     ```
   * *Benefits*: Dynamic at runtime, supports hot-swapping in dev or prod compose stack without rebuilds.

### Chosen Decision: Option B
* Rationale: Follows modern full-stack web standards, avoids rebuild overhead, and integrates directly with the existing FastAPI configuration/env flow.

---

## 3. UI Consistency Testing Strategy

### Testing Tier 1: Component Tests (Vitest)
* **Goal**: Validate that components load and apply CSS custom properties.
* **Verification**: Render `App` or layout containers in a test sandbox and verify that the HTML tag receives `data-theme="light"` or `data-theme="dark"` based on mocked API setup responses.

### Testing Tier 2: Integration/E2E Tests (Playwright)
* **Goal**: Guarantee that elements do not overlap, layout structures are aligned, and font scale limits are respected.
* **Verification**:
  * Write a Playwright spec `tests/ui-integration/ui-consistency-theme.spec.ts` that intercepts `/api/setup/status` to return specific themes.
  * Load pages and run bounding-box assertions:
    * Assert that card bounds (e.g., width, height) are equal across rows.
    * Assert that the vertical/horizontal alignment coordinates of action buttons in different cards match.
    * Validate that no text element overflows its card boundary or overlaps adjacent fields.
