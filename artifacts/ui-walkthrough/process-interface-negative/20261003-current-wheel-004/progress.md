# UI evidence negative walkthrough

Prepared before the first browser action. The authenticated trace is kept privately; published diagnostics omit credentials. Synthetic authoring and producer responses are fixture scaffolding, not live AI or engineering acceptance.

## 2026-10-03T19:34:04.674Z UTC — common restored exact baseline

URL: http://wright.localhost:54345/workspace/06ac6649-2ca2-4b6c-88db-02cc9b69ff4e?processView=view-negative-common-001&processPath=workflows%2Fui-evidence-negative-001.workflow.wflow&processDigest=93289359a42dd8ec077255622aa337b5361686875f77579494eeeb48feec2cb7&processRun=1ed6c2e1302a4eb18ff7575a3fbe5be0
Action: Open retained common run link
Expected: Same exact saved review available; no execution or decision
Actual: Exact original evidence enables Approve. Earlier ten-step saved-preview proof is retained; no preview, producer or authoring is repeated.
Status: PASS
Screenshots: screenshots/raw/C01.png; screenshots/annotated/C01.png

## 2026-10-03T19:34:12.061Z UTC — working restored exact baseline

URL: http://wright.localhost:54345/workspace/06ac6649-2ca2-4b6c-88db-02cc9b69ff4e?processView=view-negative-working-001&processPath=workflows%2Fui-evidence-negative-001.workflow.wflow&processDigest=93289359a42dd8ec077255622aa337b5361686875f77579494eeeb48feec2cb7&processRun=1ed6c2e1302a4eb18ff7575a3fbe5be0&processUIKind=working&processUI=ui-f1ca33c61df74d2ea8a96a3f284f2692&processUIRevision=revision-619a6260b1e64c51807c7fb2ed823879
Action: Open retained working run link
Expected: Same exact saved review available; no execution or decision
Actual: Exact original evidence enables Approve. Earlier ten-step saved-preview proof is retained; no preview, producer or authoring is repeated.
Status: PASS
Screenshots: screenshots/raw/C02.png; screenshots/annotated/C02.png

## 2026-10-03T19:34:14.930Z UTC — common changed evidence blocked

URL: http://wright.localhost:54345/workspace/06ac6649-2ca2-4b6c-88db-02cc9b69ff4e?processView=view-negative-common-001&processPath=workflows%2Fui-evidence-negative-001.workflow.wflow&processDigest=93289359a42dd8ec077255622aa337b5361686875f77579494eeeb48feec2cb7&processRun=1ed6c2e1302a4eb18ff7575a3fbe5be0
Action: Reload common view after controlled evidence change
Expected: Approve unavailable with exact stale evidence reason
Actual: Changed document blocks the review and explains refreshing its exact evidence.
Status: PASS
Screenshots: screenshots/raw/S11.png; screenshots/annotated/S11.png

## 2026-10-03T19:34:23.975Z UTC — working changed evidence blocked

URL: http://wright.localhost:54345/workspace/06ac6649-2ca2-4b6c-88db-02cc9b69ff4e?processView=view-negative-working-001&processPath=workflows%2Fui-evidence-negative-001.workflow.wflow&processDigest=93289359a42dd8ec077255622aa337b5361686875f77579494eeeb48feec2cb7&processRun=1ed6c2e1302a4eb18ff7575a3fbe5be0&processUIKind=working&processUI=ui-f1ca33c61df74d2ea8a96a3f284f2692&processUIRevision=revision-619a6260b1e64c51807c7fb2ed823879
Action: Reload working view after controlled evidence change
Expected: Approve unavailable with exact stale evidence reason
Actual: Changed document blocks the review and explains refreshing its exact evidence.
Status: PASS
Screenshots: screenshots/raw/S12.png; screenshots/annotated/S12.png

STOPPED: Error: EXDEV: cross-device link not permitted, rename 'C:\Users\markb\.codex\visualizations\2026\09\24\01a0d4b8-b5fa-79d0-8e8b-fc78c3dfd056\t056-negative-native-home-003\data\workspaces\proof\first.txt' -> 'D:\repos\wright\.local-run\process-interfaces-083\t056-negative-native-003\missing-reviewed-document.txt'
    at renameSync (node:fs:1014:11)
    at file:///D:/repos/wright/.local-run/process-interfaces-083/t056-negative-ui-browser-004.mjs:42:168
