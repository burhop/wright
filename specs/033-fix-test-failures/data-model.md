# Data Model: Fix Test Validation Failures

This bugfix introduces no new persisted domain entities.

## Existing Preference Values

- **wright-split-active**: Existing AppShell UI preference. Stored as the string `"true"` when split view is active.
- **wright-split-percent**: Existing AppShell UI preference. Stored as a numeric string representing the split pane width percentage.

## Validation Rules

- If preference storage is unavailable, unreadable, or unwritable, AppShell must fall back to default values.
- `wright-split-percent` must default to `30` when absent or unparsable.
- Split percentage clamping remains between 5 and 95 during drag updates.
