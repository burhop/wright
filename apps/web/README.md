# Wright — Frontend UI

> Placeholder for the frontend web application.

The UI will follow atomic design principles (Tokens → Primitives → Components → Patterns)
with all styling flowing strictly through design tokens.

All interactive UI elements will include `data-testid` attributes for testing.

## Testing Tiers

- **Tier 1**: Component tests (Storybook play functions or equivalent)
- **Tier 2**: UI integration tests (mocked Playwright) in `tests/ui-integration/`
- **Tier 3**: System E2E smoke tests in `tests/e2e/`
