# Workflow Composer Checkpoint D invalid-edit recovery

Commit: `e0354dd7346c7573f1aa6a36e1c29ed854a3bbe9`
Base URL: `http://127.0.0.1:8000`
Persona: local engineer
Authority: provisional draft only; no execution, release, MCP, model, benchmark, or publication action is present.

## 8/31/2026, 5:28:30 PM EDT — PASS

- Current URL: `http://127.0.0.1:8000/workflow-composer?draft=draft.6c916fe0302f4e72be2f8ce8de3df8b1`
- Action: Clicked Create working draft.
- Exact control: Draft title, Purpose, Create working draft
- Value: Product definition draft
- Expected: An empty revision 1 opens with no released or executable authority.
- Actual: Revision 1 opened with Working draft and Not released · Not executable labels.
- Diagnostics:
  - No console errors, page errors, or failed responses recorded.
- Screenshots:
  - Raw: `screenshots/raw/01-create.png`
  - Annotated: `screenshots/annotated/01-create.png`
- Status: **PASS**
## 8/31/2026, 5:28:31 PM EDT — PASS

- Current URL: `http://127.0.0.1:8000/workflow-composer?draft=draft.6c916fe0302f4e72be2f8ce8de3df8b1`
- Action: Clicked Capture input.
- Exact control: Capture input
- Value: No value entered.
- Expected: The next complete valid candidate replaces the working copy.
- Actual: The block and its reciprocal declarations appeared without browser diagnostics.
- Diagnostics:
  - No console errors, page errors, or failed responses recorded.
- Screenshots:
  - Raw: `screenshots/raw/02-add-input.png`
  - Annotated: `screenshots/annotated/02-add-input.png`
- Status: **PASS**
## 8/31/2026, 5:28:31 PM EDT — PASS

- Current URL: `http://127.0.0.1:8000/workflow-composer?draft=draft.6c916fe0302f4e72be2f8ce8de3df8b1`
- Action: Clicked Engineering work.
- Exact control: Engineering work
- Value: No value entered.
- Expected: The next complete valid candidate replaces the working copy.
- Actual: The block and its reciprocal declarations appeared without browser diagnostics.
- Diagnostics:
  - No console errors, page errors, or failed responses recorded.
- Screenshots:
  - Raw: `screenshots/raw/03-add-work.png`
  - Annotated: `screenshots/annotated/03-add-work.png`
- Status: **PASS**
## 8/31/2026, 5:28:31 PM EDT — PASS

- Current URL: `http://127.0.0.1:8000/workflow-composer?draft=draft.6c916fe0302f4e72be2f8ce8de3df8b1`
- Action: Clicked Review.
- Exact control: Review
- Value: No value entered.
- Expected: The next complete valid candidate replaces the working copy.
- Actual: The block and its reciprocal declarations appeared without browser diagnostics.
- Diagnostics:
  - No console errors, page errors, or failed responses recorded.
- Screenshots:
  - Raw: `screenshots/raw/04-add-review.png`
  - Annotated: `screenshots/annotated/04-add-review.png`
- Status: **PASS**
## 8/31/2026, 5:28:32 PM EDT — PASS

- Current URL: `http://127.0.0.1:8000/workflow-composer?draft=draft.6c916fe0302f4e72be2f8ce8de3df8b1`
- Action: Clicked Release boundary.
- Exact control: Release boundary
- Value: No value entered.
- Expected: The next complete valid candidate replaces the working copy.
- Actual: The block and its reciprocal declarations appeared without browser diagnostics.
- Diagnostics:
  - No console errors, page errors, or failed responses recorded.
- Screenshots:
  - Raw: `screenshots/raw/05-add-release.png`
  - Annotated: `screenshots/annotated/05-add-release.png`
- Status: **PASS**
## 8/31/2026, 5:28:32 PM EDT — PASS

- Current URL: `http://127.0.0.1:8000/workflow-composer?draft=draft.6c916fe0302f4e72be2f8ce8de3df8b1`
- Action: Changed the selected block title, purpose, X, and Y, then applied both edits.
- Exact control: Title, Purpose, Apply definition, X, Y, Apply position
- Value: Review the product definition; 720,96
- Expected: Canvas, text, and inspector agree on the same stable block identity and new values.
- Actual: All three surfaces show the edited block at layout 720,96; revision remains 1.
- Diagnostics:
  - No console errors, page errors, or failed responses recorded.
- Screenshots:
  - Raw: `screenshots/raw/06-edit-review.png`
  - Annotated: `screenshots/annotated/06-edit-review.png`
- Status: **PASS**
## 8/31/2026, 5:28:33 PM EDT — PASS

- Current URL: `http://127.0.0.1:8000/workflow-composer?draft=draft.6c916fe0302f4e72be2f8ce8de3df8b1`
- Action: Clicked Delete connection for connection.definition-to-review.
- Exact control: Delete connection
- Value: No value entered.
- Expected: Only that connection disappears; ports and saved revision remain unchanged.
- Actual: The relationship count fell from three to two and revision remained 1.
- Diagnostics:
  - No console errors, page errors, or failed responses recorded.
- Screenshots:
  - Raw: `screenshots/raw/07-delete-connection.png`
  - Annotated: `screenshots/annotated/07-delete-connection.png`
- Status: **PASS**
## 8/31/2026, 5:28:33 PM EDT — PASS

- Current URL: `http://127.0.0.1:8000/workflow-composer?draft=draft.6c916fe0302f4e72be2f8ce8de3df8b1`
- Action: Selected Product definition output as source, Accepted definition output as target, and clicked Create connection.
- Exact control: Source port, Target port, Create connection
- Value: port.product-definition-out → port.accepted-definition-out
- Expected: The invalid connection is rejected, affected identities are marked, and a bounded correction is shown.
- Actual: CONNECTION_TARGET_INVALID identified the output target, stated it is not an input, and directed the engineer to choose an existing input; no candidate connection appeared.
- Diagnostics:
  - No console errors, page errors, or failed responses recorded.
- Screenshots:
  - Raw: `screenshots/raw/09-invalid-contained.png`
  - Annotated: `screenshots/annotated/09-invalid-contained.png`
- Status: **PASS**
## 8/31/2026, 5:28:34 PM EDT — PASS

- Current URL: `http://127.0.0.1:8000/workflow-composer?draft=draft.6c916fe0302f4e72be2f8ce8de3df8b1`
- Action: Changed only the target to Product definition input and clicked Create connection.
- Exact control: Target port, Create connection
- Value: port.product-definition-out → port.product-definition-in
- Expected: The correction clears the diagnostic and appears in both diagram and text.
- Actual: The diagnostic cleared; the corrected connection appears in diagram and text while the review edit and position remain.
- Diagnostics:
  - No console errors, page errors, or failed responses recorded.
- Screenshots:
  - Raw: `screenshots/raw/10-corrected.png`
  - Annotated: `screenshots/annotated/10-corrected.png`
- Status: **PASS**
## 8/31/2026, 5:28:34 PM EDT — PASS

- Current URL: `http://127.0.0.1:8000/workflow-composer?draft=draft.6c916fe0302f4e72be2f8ce8de3df8b1`
- Action: Clicked Validate.
- Exact control: Validate
- Value: No value entered.
- Expected: Validation passes with no contradictory local or server diagnostic.
- Actual: The status and inspector both report validation passed.
- Diagnostics:
  - No console errors, page errors, or failed responses recorded.
- Screenshots:
  - Raw: `screenshots/raw/11-validated.png`
  - Annotated: `screenshots/annotated/11-validated.png`
- Status: **PASS**
## 8/31/2026, 5:28:34 PM EDT — PASS

- Current URL: `http://127.0.0.1:8000/workflow-composer?draft=draft.6c916fe0302f4e72be2f8ce8de3df8b1`
- Action: Clicked Save draft after validation passed.
- Exact control: Save draft
- Value: No value entered.
- Expected: Only the corrected candidate advances to revision 2.
- Actual: Revision 2 saved with the edited review block and compatible connection; the rejected output-to-output relationship is absent.
- Diagnostics:
  - No console errors, page errors, or failed responses recorded.
- Screenshots:
  - Raw: `screenshots/raw/12-saved.png`
  - Annotated: `screenshots/annotated/12-saved.png`
- Status: **PASS**
