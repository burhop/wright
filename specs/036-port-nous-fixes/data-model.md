# Data Model: Port Nous Fixes

## Candidate Review Folder

Represents the copied review material from the prototype branch.

**Fields**

- `path`: Workspace path, currently `scratch/nous_hackathon_candidates/`
- `source_branch`: `nous_hackathon`
- `base_branch`: `dev`
- `extraction_branch`: `codex/port-nous-good-fixes`
- `manifest`: Review notes and exclusion list

**Validation Rules**

- Must preserve repository-relative paths for copied candidate files.
- Must not be treated as production source code.
- Must document intentionally excluded prototype artifacts.

## Candidate File

Represents one copied source, test, config, or documentation file under the review folder.

**Fields**

- `original_path`: Repository-relative path of the live file.
- `candidate_path`: Path under the review folder.
- `risk`: `safe`, `mixed`, or `excluded`.
- `decision`: `accept`, `partial`, `reject`, or `pending`.
- `notes`: Reason for the decision.

**Validation Rules**

- Files marked `mixed` require hunk-level review.
- Files marked `excluded` must not be applied.
- New dependencies from candidate files must be accepted only if they are required by non-prototype fixes.

## Excluded Artifact

Represents prototype work that must remain out of the extraction.

**Fields**

- `path_or_pattern`: File path, directory path, or keyword-based hunk marker.
- `reason`: Payment, demo, generated output, hackathon stack, nemoclaw expansion, or paid-demo expansion.

**Validation Rules**

- Excluded artifacts must not appear in the final applied source diff.
- Mixed files containing excluded hunks may still be partially accepted if the final applied hunks are independent.

## Accepted Change Group

Represents a small logical set of live-code changes ported from reviewed candidates.

**Fields**

- `scope`: Backend, frontend, package, docs, or tests.
- `source_candidates`: One or more candidate paths.
- `live_paths`: One or more live repository paths changed.
- `validation`: Associated validation result.

**Validation Rules**

- Must be independently reviewable.
- Must not depend on excluded prototype artifacts.
- Must have targeted validation or a documented validation blocker.

## Validation Result

Represents verification evidence for an accepted change group.

**Fields**

- `command`: Validation command or manual check.
- `status`: `passed`, `failed`, or `blocked`.
- `notes`: Relevant output summary or blocker.

**Validation Rules**

- Backend/package changes require targeted Python tests when practical.
- Frontend changes require targeted workspace tests when practical.
- MCP validation changes must follow the clean-container process.
