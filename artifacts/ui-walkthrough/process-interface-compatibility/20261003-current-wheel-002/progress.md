# UI evidence negative walkthrough

Prepared before the first browser action. The authenticated trace is kept privately; published diagnostics omit credentials. Synthetic authoring and producer responses are fixture scaffolding, not live AI or engineering acceptance.

## 2026-10-03T21:15:49.197Z UTC â€” Required binding mismatch remains contained

URL: http://wright.localhost:65191/workspace/06ac6649-2ca2-4b6c-88db-02cc9b69ff4e?processView=view-revision-working-a51fc954d5-prepare-001&processPath=workflows%2Fui-evidence-negative-001.workflow.wflow&processDigest=a51fc954d54cd7bede392f3210f6b0d80551cc7d26602a80ea994f04896f098a&processUIKind=working&processUI=ui-f1ca33c61df74d2ea8a96a3f284f2692&processUIRevision=revision-619a6260b1e64c51807c7fb2ed823879
Action: Open current saved UI link after controlled source CAS
Expected: No frame; exact binding reason and fallback
Actual: The same immutable saved UI is contained for this incompatible accepted revision.
Status: PASS
Screenshots: screenshots/raw/C01.png; screenshots/annotated/C01.png

## 2026-10-03T21:15:51.114Z UTC â€” Unavailable authoring remains disabled with complete request

URL: http://wright.localhost:65191/workspace/06ac6649-2ca2-4b6c-88db-02cc9b69ff4e?processView=view-revision-working-a51fc954d5-prepare-001&processPath=workflows%2Fui-evidence-negative-001.workflow.wflow&processDigest=a51fc954d54cd7bede392f3210f6b0d80551cc7d26602a80ea994f04896f098a&processUIKind=working&processUI=ui-f1ca33c61df74d2ea8a96a3f284f2692&processUIRevision=revision-619a6260b1e64c51807c7fb2ed823879
Action: Select existing revision and fill title/instructions
Expected: Resource limitation keeps creation/update disabled
Actual: The old saved revision is selected and title/instructions supplied; explicit compiler/model unavailability still blocks creation/update. No authoring request is sent.
Status: PASS
Screenshots: screenshots/raw/C02.png; screenshots/annotated/C02.png

## 2026-10-03T21:15:52.652Z UTC â€” Common fallback form is fully inspectable

URL: http://wright.localhost:65191/workspace/06ac6649-2ca2-4b6c-88db-02cc9b69ff4e?processView=view-revision-working-a51fc954d5-prepare-001&processPath=workflows%2Fui-evidence-negative-001.workflow.wflow&processDigest=a51fc954d54cd7bede392f3210f6b0d80551cc7d26602a80ea994f04896f098a&processUIKind=working&processUI=ui-f1ca33c61df74d2ea8a96a3f284f2692&processUIRevision=revision-619a6260b1e64c51807c7fb2ed823879
Action: Hide interface controls then Use common working view
Expected: Current required input visible without old review authority
Actual: The common form displays the accepted input and its actual default. No old run/review or generated frame is attached.
Status: PASS
Screenshots: screenshots/raw/C03.png; screenshots/annotated/C03.png

Manual repeat instructions now describe the three actual supplemental controls and the controlled source-CAS prerequisite. Original statuses and screenshots are unchanged.
