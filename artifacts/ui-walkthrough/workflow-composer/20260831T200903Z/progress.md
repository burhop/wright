# Workflow Composer Checkpoint C and save/reopen walkthrough

Commit: `8282b9918143ead7860222940e4000f9fa86a7cd`
Base URL: `http://127.0.0.1:8000`
Persona: local engineer
Authority: provisional draft only; no execution, release, MCP, model, or publication action is present.

## 8/31/2026, 4:18:38 PM EDT — PASS

- Current URL: `http://127.0.0.1:8000/workflow-composer?draft=draft.75ada92358d647cfbf7711d04d8cba01`
- Action: Kept the visible title and purpose values and clicked Create working draft.
- Exact control: Draft title, Purpose, Create working draft
- Value: Product definition draft; Capture, define, review, and release one product definition.
- Expected: A feature-bounded working draft opens at revision 1 with no released or executable authority.
- Actual: Revision 1 opened with the Working draft and Not released · Not executable labels.
- Diagnostics:
  - No console errors, page errors, or failed responses recorded.
- Screenshots:
  - Raw: `screenshots/raw/01-create-empty-draft.png`
  - Annotated: `screenshots/annotated/01-create-empty-draft.png`
- Status: **PASS**
## 8/31/2026, 4:18:39 PM EDT — PASS

- Current URL: `http://127.0.0.1:8000/workflow-composer?draft=draft.75ada92358d647cfbf7711d04d8cba01`
- Action: Clicked Capture input.
- Exact control: Capture input
- Value: No value entered.
- Expected: Capture requirements appears in the diagram and text projection with its stable host-owned identities.
- Actual: Capture requirements appeared and the next bounded palette action became available.
- Diagnostics:
  - No console errors, page errors, or failed responses recorded.
- Screenshots:
  - Raw: `screenshots/raw/02-add-input.png`
  - Annotated: `screenshots/annotated/02-add-input.png`
- Status: **PASS**
## 8/31/2026, 4:18:39 PM EDT — PASS

- Current URL: `http://127.0.0.1:8000/workflow-composer?draft=draft.75ada92358d647cfbf7711d04d8cba01`
- Action: Clicked Engineering work.
- Exact control: Engineering work
- Value: No value entered.
- Expected: Define product appears in the diagram and text projection with its stable host-owned identities.
- Actual: Define product appeared and the next bounded palette action became available.
- Diagnostics:
  - No console errors, page errors, or failed responses recorded.
- Screenshots:
  - Raw: `screenshots/raw/03-add-work.png`
  - Annotated: `screenshots/annotated/03-add-work.png`
- Status: **PASS**
## 8/31/2026, 4:18:39 PM EDT — PASS

- Current URL: `http://127.0.0.1:8000/workflow-composer?draft=draft.75ada92358d647cfbf7711d04d8cba01`
- Action: Clicked Review.
- Exact control: Review
- Value: No value entered.
- Expected: Review product definition appears in the diagram and text projection with its stable host-owned identities.
- Actual: Review product definition appeared and the next bounded palette action became available.
- Diagnostics:
  - No console errors, page errors, or failed responses recorded.
- Screenshots:
  - Raw: `screenshots/raw/04-add-review.png`
  - Annotated: `screenshots/annotated/04-add-review.png`
- Status: **PASS**
## 8/31/2026, 4:18:40 PM EDT — PASS

- Current URL: `http://127.0.0.1:8000/workflow-composer?draft=draft.75ada92358d647cfbf7711d04d8cba01`
- Action: Clicked Release boundary.
- Exact control: Release boundary
- Value: No value entered.
- Expected: Release product definition appears in the diagram and text projection with its stable host-owned identities.
- Actual: Release product definition appeared and the next bounded palette action became available.
- Diagnostics:
  - No console errors, page errors, or failed responses recorded.
- Screenshots:
  - Raw: `screenshots/raw/05-add-release.png`
  - Annotated: `screenshots/annotated/05-add-release.png`
- Status: **PASS**
## 8/31/2026, 4:18:40 PM EDT — PASS

- Current URL: `http://127.0.0.1:8000/workflow-composer?draft=draft.75ada92358d647cfbf7711d04d8cba01`
- Action: Compared the complete diagram and text semantic identity sets.
- Exact control: First-party diagram, Canonical text projection, Draft inspector
- Value: No value entered.
- Expected: Both projections contain exactly the same 23 unique semantic identities.
- Actual: Both identity sets matched exactly at 23, including phases, blocks, ports, connections, gate, feedback, and intended artifacts.
- Diagnostics:
  - No console errors, page errors, or failed responses recorded.
- Screenshots:
  - Raw: `screenshots/raw/06-four-block-composition.png`
  - Annotated: `screenshots/annotated/06-four-block-composition.png`
- Status: **PASS**
## 8/31/2026, 4:18:41 PM EDT — PASS

- Current URL: `http://127.0.0.1:8000/workflow-composer?draft=draft.75ada92358d647cfbf7711d04d8cba01`
- Action: Clicked Define product in the diagram.
- Exact control: Define product
- Value: No value entered.
- Expected: The block exposes a non-color selected state and the inspector shows block.define-product.
- Actual: The button exposed aria-pressed=true, visible Selected text, and the inspector showed the same stable ID.
- Diagnostics:
  - No console errors, page errors, or failed responses recorded.
- Screenshots:
  - Raw: `screenshots/raw/07-selected-inspector.png`
  - Annotated: `screenshots/annotated/07-selected-inspector.png`
- Status: **PASS**
## 8/31/2026, 4:18:41 PM EDT — PASS

- Current URL: `http://127.0.0.1:8000/workflow-composer?draft=draft.75ada92358d647cfbf7711d04d8cba01`
- Action: Clicked Validate.
- Exact control: Validate
- Value: No value entered.
- Expected: Validation passes and the inspector does not show contradictory diagnostics.
- Actual: The status and inspector consistently reported validation passed.
- Diagnostics:
  - No console errors, page errors, or failed responses recorded.
- Screenshots:
  - Raw: `screenshots/raw/08-validation-passed.png`
  - Annotated: `screenshots/annotated/08-validation-passed.png`
- Status: **PASS**
## 8/31/2026, 4:18:42 PM EDT — PASS

- Current URL: `http://127.0.0.1:8000/workflow-composer?draft=draft.75ada92358d647cfbf7711d04d8cba01`
- Action: Clicked Save draft.
- Exact control: Save draft
- Value: No value entered.
- Expected: The server advances to revision 2 and reports both identity digests.
- Actual: Revision 2 appeared and both semantic and layout digests remained visible.
- Diagnostics:
  - No console errors, page errors, or failed responses recorded.
- Screenshots:
  - Raw: `screenshots/raw/09-saved-revision.png`
  - Annotated: `screenshots/annotated/09-saved-revision.png`
- Status: **PASS**
## 8/31/2026, 4:18:42 PM EDT — PASS

- Current URL: `http://127.0.0.1:8000/workflow-composer?draft=draft.75ada92358d647cfbf7711d04d8cba01`
- Action: Clicked Close.
- Exact control: Close
- Value: No value entered.
- Expected: The graphical editor closes and saved revision 2 remains available to reopen.
- Actual: The closed state showed revision 2, draft ID, semantic digest, layout digest, and Reopen saved draft.
- Diagnostics:
  - No console errors, page errors, or failed responses recorded.
- Screenshots:
  - Raw: `screenshots/raw/10-closed-draft.png`
  - Annotated: `screenshots/annotated/10-closed-draft.png`
- Status: **PASS**
## 8/31/2026, 4:18:42 PM EDT — PASS

- Current URL: `http://127.0.0.1:8000/workflow-composer?draft=draft.75ada92358d647cfbf7711d04d8cba01`
- Action: Clicked Reopen saved draft and compared saved identities and positions.
- Exact control: Reopen saved draft
- Value: No value entered.
- Expected: Revision, semantic digest, layout digest, 23 identities, and four positions match the saved state.
- Actual: Revision 2 reopened with identical digests, 23 identities, and four saved position records.
- Diagnostics:
  - No console errors, page errors, or failed responses recorded.
- Screenshots:
  - Raw: `screenshots/raw/11-reopened-identical.png`
  - Annotated: `screenshots/annotated/11-reopened-identical.png`
- Status: **PASS**
