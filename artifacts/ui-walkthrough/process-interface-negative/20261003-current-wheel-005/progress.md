# UI evidence negative walkthrough

Prepared before the first browser action. The authenticated trace is kept privately; published diagnostics omit credentials. Synthetic authoring and producer responses are fixture scaffolding, not live AI or engineering acceptance.

## 2026-10-03T19:36:16.845Z UTC — common restored exact baseline

URL: http://wright.localhost:54345/workspace/06ac6649-2ca2-4b6c-88db-02cc9b69ff4e?processView=view-negative-common-001&processPath=workflows%2Fui-evidence-negative-001.workflow.wflow&processDigest=93289359a42dd8ec077255622aa337b5361686875f77579494eeeb48feec2cb7&processRun=1ed6c2e1302a4eb18ff7575a3fbe5be0
Action: Open retained common run link
Expected: Same exact saved review available; no execution or decision
Actual: Exact original evidence enables Approve. Earlier saved-preview and two-view changed-evidence proofs are retained; no preview, producer or authoring is repeated.
Status: PASS
Screenshots: screenshots/raw/C01.png; screenshots/annotated/C01.png

## 2026-10-03T19:36:25.298Z UTC — working restored exact baseline

URL: http://wright.localhost:54345/workspace/06ac6649-2ca2-4b6c-88db-02cc9b69ff4e?processView=view-negative-working-001&processPath=workflows%2Fui-evidence-negative-001.workflow.wflow&processDigest=93289359a42dd8ec077255622aa337b5361686875f77579494eeeb48feec2cb7&processRun=1ed6c2e1302a4eb18ff7575a3fbe5be0&processUIKind=working&processUI=ui-f1ca33c61df74d2ea8a96a3f284f2692&processUIRevision=revision-619a6260b1e64c51807c7fb2ed823879
Action: Open retained working run link
Expected: Same exact saved review available; no execution or decision
Actual: Exact original evidence enables Approve. Earlier saved-preview and two-view changed-evidence proofs are retained; no preview, producer or authoring is repeated.
Status: PASS
Screenshots: screenshots/raw/C02.png; screenshots/annotated/C02.png

## 2026-10-03T19:36:28.650Z UTC — common missing evidence blocked

URL: http://wright.localhost:54345/workspace/06ac6649-2ca2-4b6c-88db-02cc9b69ff4e?processView=view-negative-common-001&processPath=workflows%2Fui-evidence-negative-001.workflow.wflow&processDigest=93289359a42dd8ec077255622aa337b5361686875f77579494eeeb48feec2cb7&processRun=1ed6c2e1302a4eb18ff7575a3fbe5be0
Action: Reload common view after controlled required document removal
Expected: Missing required evidence blocks review with reason
Actual: Missing actual file cannot authorize Approve in this view.
Status: PASS
Screenshots: screenshots/raw/S13.png; screenshots/annotated/S13.png

## 2026-10-03T19:36:38.203Z UTC — working missing evidence blocked

URL: http://wright.localhost:54345/workspace/06ac6649-2ca2-4b6c-88db-02cc9b69ff4e?processView=view-negative-working-001&processPath=workflows%2Fui-evidence-negative-001.workflow.wflow&processDigest=93289359a42dd8ec077255622aa337b5361686875f77579494eeeb48feec2cb7&processRun=1ed6c2e1302a4eb18ff7575a3fbe5be0&processUIKind=working&processUI=ui-f1ca33c61df74d2ea8a96a3f284f2692&processUIRevision=revision-619a6260b1e64c51807c7fb2ed823879
Action: Reload working view after controlled required document removal
Expected: Missing required evidence blocks review with reason
Actual: Missing actual file cannot authorize Approve in this view.
Status: PASS
Screenshots: screenshots/raw/S14.png; screenshots/annotated/S14.png

## 2026-10-03T19:36:40.020Z UTC — Incompatible saved binding contained

URL: http://wright.localhost:54345/workspace/06ac6649-2ca2-4b6c-88db-02cc9b69ff4e?processView=view-negative-working-001&processPath=workflows%2Fui-evidence-negative-001.workflow.wflow&processDigest=a51fc954d54cd7bede392f3210f6b0d80551cc7d26602a80ea994f04896f098a&processRun=1ed6c2e1302a4eb18ff7575a3fbe5be0&processUIKind=working&processUI=ui-f1ca33c61df74d2ea8a96a3f284f2692&processUIRevision=revision-619a6260b1e64c51807c7fb2ed823879
Action: Open saved interface for changed process revision
Expected: No generated frame/action authority; common fallback offered
Actual: Changed accepted output binding prevents launching the saved interface and offers the common view.
Status: PASS
Screenshots: screenshots/raw/S15.png; screenshots/annotated/S15.png

STOPPED: Error: expect(locator).toBeDisabled() failed

Locator: locator('[data-testid="common-process-view"]:visible').getByRole('button', { name: 'Approve', exact: true })
Expected: disabled
Timeout: 5000ms
Error: element(s) not found

Call log:
  - Expect "to.be.disabled" with timeout 5000ms
  - waiting for locator('[data-testid="common-process-view"]:visible').getByRole('button', { name: 'Approve', exact: true })

    at captureRawStack (D:\repos\wright\node_modules\playwright-core\lib\coreBundle.js:9681:17)
    at callMatcherAsStep (D:\repos\wright\node_modules\playwright\lib\matchers\expect.js:13310:57)
    at Object.toBeDisabled (D:\repos\wright\node_modules\playwright\lib\matchers\expect.js:13300:23)
    at D:\repos\wright\.local-run\process-interfaces-083\t056-negative-ui-browser-005.mjs:46:208
