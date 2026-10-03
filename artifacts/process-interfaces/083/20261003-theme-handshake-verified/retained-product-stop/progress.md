# Latest saved Heat output and navigation continuation

Prepared before navigation. Browser trace remains in the private proof root because authentication headers are sensitive.

## 2026-10-03T03:44:47.473Z UTC â€” heat saved working interface

URL: http://127.0.0.1:5243/workspace/083-heat-live-005?workflow=canonical&workflowPath=workflows%2Fheat-spreader-sizing-live-default-model-002.workflow.wflow&processView=87dd3848-6197-4c21-92ad-474afec1dc2c&processPath=workflows%2Fheat-spreader-sizing-live-default-model-002.workflow.wflow&processDigest=e1ddaf65a1890060ad546ccc9604ea6f2a3ebfcdb9f0de7d1183bdeaadf20bf9&processRun=67abaa021ee44972a94e3c9cbaa3dbbe&processUIKind=working&processUI=ui-8858f2ec2bc24bc588ce5042626503ab&processUIRevision=revision-9c8c8b164ea34a9ba65910567b41b170
Action: Open the saved working-interface link.
Controls: Back to Dashboard, Run inputs, Open assessment
Expected: Exact saved revision and current results.
Actual: 18 exact results in the current working context.
Status: pass
Screenshots: screenshots/raw/S01.png; screenshots/annotated/S01.png

## 2026-10-03T03:45:24.018Z UTC â€” Theme/handshake check stopped

URL: http://127.0.0.1:5243/workspace/083-heat-live-005?workflow=canonical&workflowPath=workflows%2Fheat-spreader-sizing-live-default-model-002.workflow.wflow&processView=87dd3848-6197-4c21-92ad-474afec1dc2c&processPath=workflows%2Fheat-spreader-sizing-live-default-model-002.workflow.wflow&processDigest=e1ddaf65a1890060ad546ccc9604ea6f2a3ebfcdb9f0de7d1183bdeaadf20bf9&processRun=67abaa021ee44972a94e3c9cbaa3dbbe&processUIKind=working&processUI=ui-8858f2ec2bc24bc588ce5042626503ab&processUIRevision=revision-9c8c8b164ea34a9ba65910567b41b170
Action: Stop at the current saved interface.
Controls: Use common working view, Reopen interface view
Expected: Parent and saved interface have the same selected theme and exact run context.
Actual: expect(received).toEqual(expected) // deep equality

- Expected  - 1
+ Received  + 1

  Object {
    "neutral": "#e8edf5",
    "primary": "#0f172a",
-   "scheme": "light",
+   "scheme": "dark",
  }

Call Log:
- Timeout 30000ms exceeded while waiting on the predicate
Status: blocked
Screenshots: screenshots/raw/STOP.png; screenshots/annotated/STOP.png
