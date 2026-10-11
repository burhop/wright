# UI evidence negative walkthrough

Prepared before the first browser action. The authenticated trace is kept privately; published diagnostics omit credentials. Synthetic authoring and producer responses are fixture scaffolding, not live AI or engineering acceptance.

## 2026-10-03T21:26:22.112Z UTC â€” Saved UI uses the changed accepted default

URL: http://wright.localhost:65439/workspace/06ac6649-2ca2-4b6c-88db-02cc9b69ff4e?processView=view-revision-working-89333f9b1d-prepare-001&processPath=workflows%2Fui-evidence-negative-001.workflow.wflow&processDigest=89333f9b1df725ad192265a0c3d2b8e00814829db4bbd2f09f51dc2496a2ae5e&processUIKind=working&processUI=ui-f1ca33c61df74d2ea8a96a3f284f2692&processUIRevision=revision-619a6260b1e64c51807c7fb2ed823879
Action: Open current saved UI after conditional input-default change
Expected: Same compiled UI; actual current default and no old run/review
Actual: Saved UI renders the changed input default from the current accepted process, without old outputs or review permission.
Status: PASS
Screenshots: screenshots/raw/D01.png; screenshots/annotated/D01.png

## 2026-10-03T21:26:22.945Z UTC â€” Common view agrees on the changed default

URL: http://wright.localhost:65439/workspace/06ac6649-2ca2-4b6c-88db-02cc9b69ff4e?processView=view-revision-working-89333f9b1d-prepare-001&processPath=workflows%2Fui-evidence-negative-001.workflow.wflow&processDigest=89333f9b1df725ad192265a0c3d2b8e00814829db4bbd2f09f51dc2496a2ae5e&processUIKind=working&processUI=ui-f1ca33c61df74d2ea8a96a3f284f2692&processUIRevision=revision-619a6260b1e64c51807c7fb2ed823879
Action: Click Use common working view
Expected: Same current input basis without old review
Actual: Common view shows the same accepted changed default and no historical review. No process is started.
Status: PASS
Screenshots: screenshots/raw/D02.png; screenshots/annotated/D02.png

## 2026-10-03T21:26:31.707Z UTC â€” Restored source still reuses the immutable saved UI

URL: http://wright.localhost:65439/workspace/06ac6649-2ca2-4b6c-88db-02cc9b69ff4e?processView=view-revision-working-93289359a4-prepare-001&processPath=workflows%2Fui-evidence-negative-001.workflow.wflow&processDigest=93289359a42dd8ec077255622aa337b5361686875f77579494eeeb48feec2cb7&processUIKind=working&processUI=ui-f1ca33c61df74d2ea8a96a3f284f2692&processUIRevision=revision-619a6260b1e64c51807c7fb2ed823879
Action: Open original-source saved preparation view
Expected: Original default; no old review automatically attached
Actual: Saved UI returns to the original accepted default after exact CAS restoration while preserving separate run/review identity.
Status: PASS
Screenshots: screenshots/raw/D03.png; screenshots/annotated/D03.png

Manual repeat instructions now describe the three actual default-change checks and controlled source-CAS prerequisite. Original statuses and screenshots are unchanged.
