# UI evidence negative walkthrough

Prepared before the first browser action. The authenticated trace is kept privately; published diagnostics omit credentials. Synthetic authoring and producer responses are fixture scaffolding, not live AI or engineering acceptance.

## 2026-10-03T20:05:47.911Z UTC — common restored exact baseline

URL: http://wright.localhost:61434/workspace/06ac6649-2ca2-4b6c-88db-02cc9b69ff4e?processView=view-negative-common-001&processPath=workflows%2Fui-evidence-negative-001.workflow.wflow&processDigest=93289359a42dd8ec077255622aa337b5361686875f77579494eeeb48feec2cb7&processRun=1ed6c2e1302a4eb18ff7575a3fbe5be0
Action: Open retained common run link
Expected: Same exact saved review available; no execution or decision
Actual: Exact original evidence enables Approve. Earlier saved-preview and two-view changed-evidence proofs are retained; no preview, producer or authoring is repeated.
Status: PASS
Screenshots: screenshots/raw/C01.png; screenshots/annotated/C01.png

## 2026-10-03T20:05:55.341Z UTC — working restored exact baseline

URL: http://wright.localhost:61434/workspace/06ac6649-2ca2-4b6c-88db-02cc9b69ff4e?processView=view-negative-working-001&processPath=workflows%2Fui-evidence-negative-001.workflow.wflow&processDigest=93289359a42dd8ec077255622aa337b5361686875f77579494eeeb48feec2cb7&processRun=1ed6c2e1302a4eb18ff7575a3fbe5be0&processUIKind=working&processUI=ui-f1ca33c61df74d2ea8a96a3f284f2692&processUIRevision=revision-619a6260b1e64c51807c7fb2ed823879
Action: Open retained working run link
Expected: Same exact saved review available; no execution or decision
Actual: Exact original evidence enables Approve. Earlier saved-preview and two-view changed-evidence proofs are retained; no preview, producer or authoring is repeated.
Status: PASS
Screenshots: screenshots/raw/C02.png; screenshots/annotated/C02.png

## 2026-10-03T20:05:57.010Z UTC — Incompatible saved binding contained

URL: http://wright.localhost:61434/workspace/06ac6649-2ca2-4b6c-88db-02cc9b69ff4e?processView=view-negative-working-001&processPath=workflows%2Fui-evidence-negative-001.workflow.wflow&processDigest=93289359a42dd8ec077255622aa337b5361686875f77579494eeeb48feec2cb7&processRun=1ed6c2e1302a4eb18ff7575a3fbe5be0&processUIKind=working&processUI=ui-f1ca33c61df74d2ea8a96a3f284f2692&processUIRevision=revision-619a6260b1e64c51807c7fb2ed823879
Action: Open saved interface for changed process revision
Expected: No generated frame/action authority; common fallback offered
Actual: Changed accepted output binding prevents launching the saved interface and offers the common view.
Status: PASS
Screenshots: screenshots/raw/S15.png; screenshots/annotated/S15.png

## 2026-10-03T20:05:58.703Z UTC — Common fallback preserves historical identity

URL: http://wright.localhost:61434/workspace/06ac6649-2ca2-4b6c-88db-02cc9b69ff4e?processView=view-negative-working-001&processPath=workflows%2Fui-evidence-negative-001.workflow.wflow&processDigest=93289359a42dd8ec077255622aa337b5361686875f77579494eeeb48feec2cb7&processRun=1ed6c2e1302a4eb18ff7575a3fbe5be0&processUIKind=working&processUI=ui-f1ca33c61df74d2ea8a96a3f284f2692&processUIRevision=revision-619a6260b1e64c51807c7fb2ed823879
Action: Click Use common working view
Expected: Historical run inspectable without new permission
Actual: Common fallback opens the exact historical run while review stays unavailable for changed source.
Status: PASS
Screenshots: screenshots/raw/S16.png; screenshots/annotated/S16.png
