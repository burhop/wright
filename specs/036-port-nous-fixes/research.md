# Research: Port Nous Fixes

## Decision: Use a review folder plus path/hunk extraction

**Rationale**: The prototype branch contains a large mixed delta with reusable fixes adjacent to payment, demo, hackathon, and generated assets. A direct merge or broad cherry-pick would make it too easy to import unwanted behavior.

**Alternatives considered**:

- Merge `nous_hackathon`: rejected because it would import prototype expansions.
- Cherry-pick all prototype commits: rejected because the commits are not guaranteed to be cleanly separated by concern.
- Patch only from live diff: rejected as the only workflow because maintainers asked for copied files to review one by one.

## Decision: Keep exclusions path-based and keyword-aware

**Rationale**: Some unwanted work is isolated by path, while some may appear as hunks inside otherwise useful files. The extraction must check both file paths and suspicious terms such as billing, Stripe, hackathon, paid-demo, and nemoclaw.

**Alternatives considered**:

- Trust the initial copied candidate set: rejected because mixed-risk files can still contain excluded hunks.
- Delete all mixed-risk files from review: rejected because useful fixes may be present in those files.

## Decision: Validate by touched area

**Rationale**: The branch should get fast feedback from targeted tests for accepted backend, package, and frontend changes. Full-suite validation can happen later, but each accepted group needs local evidence.

**Alternatives considered**:

- Run only broad test suites at the end: rejected because failures would be harder to attribute.
- Skip tests until all files are ported: rejected because the extraction is intentionally incremental.

## Decision: Preserve the clean-container MCP validation boundary

**Rationale**: The repository instructions require engineering MCP server validation to avoid adding MCP-specific host software to the base Docker image. Any catalog validation updates must remain compatible with that process.

**Alternatives considered**:

- Port prototype Docker/hackathon stack changes: rejected as out of scope and explicitly excluded.
