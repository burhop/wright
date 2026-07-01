# Feature Specification: Port Nous Fixes

**Feature Branch**: `codex/port-nous-good-fixes`

**Created**: 2026-07-01

**Status**: Draft

**Input**: User description: "Use Spec Kit to pull the good changes from the `nous_hackathon` prototype branch into the current branch while leaving behind nemoclaw, Stripe, hackathon Docker/scripts, generated outputs, paid-demo, and other prototype expansions."

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Review Good Candidate Changes (Priority: P1)

A maintainer can inspect a curated set of changes from the prototype branch without having those changes applied to production source files.

**Why this priority**: The prototype branch contains mixed experimental and reusable work. Review must begin from a clean, bounded candidate set so unwanted expansions are not accidentally carried forward.

**Independent Test**: A maintainer can open the review folder, see preserved source paths, and confirm that explicitly excluded prototype/payment/demo artifacts are absent.

**Acceptance Scenarios**:

1. **Given** the current extraction branch, **When** the maintainer opens the candidate review folder, **Then** selected files from `nous_hackathon` are available under their original repository-relative paths.
2. **Given** the excluded prototype areas, **When** the maintainer searches the candidate review folder, **Then** Stripe billing, hackathon Docker/scripts, generated outputs, paid-demo MCP, and nemoclaw-specific expansion code are not present as port-ready files.

---

### User Story 2 - Port Verified Fixes Safely (Priority: P2)

A maintainer can move reviewed fixes into the live codebase in small, traceable groups while leaving unrelated prototype behavior behind.

**Why this priority**: The branch should gain the useful bug fixes and updates without becoming a merge of the entire hackathon prototype.

**Independent Test**: Each accepted group can be reviewed with a focused diff showing only the intended fix area and no unrelated payment/demo/prototype files.

**Acceptance Scenarios**:

1. **Given** a candidate file with only reusable changes, **When** the maintainer accepts it, **Then** the live code receives the intended change and the diff remains scoped to that file or feature area.
2. **Given** a mixed-risk candidate file, **When** the maintainer reviews it by hunk, **Then** only bug-fix or stability hunks are applied and prototype expansion hunks remain excluded.

---

### User Story 3 - Validate The Extracted Work (Priority: P3)

A maintainer can run targeted validation to prove the extracted changes still fit the existing product behavior and engineering MCP catalog constraints.

**Why this priority**: Extracted code must be tested in the current branch context, not assumed correct because it worked in the prototype branch.

**Independent Test**: Targeted backend and frontend tests pass for the areas touched by accepted fixes, and skipped prototype areas remain absent from the final diff.

**Acceptance Scenarios**:

1. **Given** accepted backend changes, **When** targeted backend tests run, **Then** the relevant API, adapter, catalog, and workspace tests pass or any failures are documented with next actions.
2. **Given** accepted frontend changes, **When** targeted frontend tests run, **Then** the relevant component and service tests pass or any failures are documented with next actions.

---

### Edge Cases

- A candidate file may include both a real bug fix and Stripe/demo/hackathon wiring; those files must be treated as hunk-review only.
- A candidate change may depend on a purposely excluded expansion; the change must be skipped or rewritten so it stands alone.
- Generated binary assets and temporary Office lock files must not become part of the extraction work.
- MCP catalog validation changes must respect the clean-container process and must not add MCP-specific host software to the base Docker image just to pass validation.
- Existing user or unrelated repository changes must not be reverted during the port.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: The extraction branch MUST remain based on `dev` and MUST NOT merge the full `nous_hackathon` branch.
- **FR-002**: The system MUST provide a review folder containing selected candidate files copied from `nous_hackathon` with repository-relative paths preserved.
- **FR-003**: The review set MUST exclude known prototype/payment/demo artifacts, including Stripe billing, hackathon Docker/scripts, generated outputs, paid-demo MCP code, and nemoclaw-specific expansion code.
- **FR-004**: Mixed-risk files MUST be identified so reviewers know to apply only selected hunks rather than whole files.
- **FR-005**: Accepted changes MUST be ported in small logical groups that can be reviewed independently.
- **FR-006**: Accepted backend changes MUST preserve existing API boundaries and avoid introducing new payment/demo/product-expansion behavior.
- **FR-007**: Accepted frontend changes MUST preserve existing UI behavior while incorporating only reusable stability, layout, session, registry, or viewer fixes.
- **FR-008**: MCP catalog or validation changes MUST continue to follow the clean-container validation process and must not add MCP-specific host software to the base Docker image.
- **FR-009**: The final diff MUST omit intentionally excluded prototype artifacts.
- **FR-010**: Targeted validation MUST be run for touched areas, or any inability to run validation MUST be documented.

### Key Entities *(include if feature involves data)*

- **Candidate Review Folder**: A workspace folder containing copied files from `nous_hackathon`, organized by original repository-relative path, used only for review and comparison.
- **Candidate File**: A copied source, test, config, or documentation file that may contain reusable fixes.
- **Excluded Artifact**: A file or hunk that belongs to prototype/payment/demo expansion and must not be applied to the live branch.
- **Accepted Change Group**: A small set of related changes applied to the live codebase and validated together.
- **Validation Result**: Evidence that targeted tests or manual checks passed, failed, or could not be run.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: 100% of explicitly excluded prototype/payment/demo artifact paths are absent from the final applied source diff.
- **SC-002**: Each accepted change group can be reviewed in under 10 minutes because its diff is scoped to a single fix area.
- **SC-003**: At least one targeted validation command is run for every accepted backend or frontend area, unless a blocker is documented.
- **SC-004**: Maintainers can trace every accepted change back to a candidate file or hunk in the review folder.
- **SC-005**: No branch merge from `nous_hackathon` is used to complete the extraction.

## Assumptions

- The current branch `codex/port-nous-good-fixes` is the intended extraction branch.
- The existing review folder under `scratch/nous_hackathon_candidates/` is allowed to remain as working review material during implementation.
- Prototype payment, demo, hackathon stack, generated presentation/video output, and nemoclaw expansion work are out of scope unless the user later approves a specific item.
- Validation should favor targeted tests for changed areas before broad test suites.
- The extraction may leave some candidate files unapplied if they are too entangled with excluded prototype behavior.
