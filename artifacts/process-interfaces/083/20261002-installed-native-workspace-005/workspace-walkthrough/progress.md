# Installed native process workspace walkthrough

Prepared before navigation. Authenticated browser trace remains private.

## 2026-10-02T20:09:53.977Z UTC — Installed journey stopped
URL: http://127.0.0.1:8032/workspace/083-heat-live-005
Action: Stop at first unexpected state.
Controls: Current workspace control
Expected: Installed common/saved journey remains usable.
Actual: expect(locator).toBeVisible() failed

Locator: getByRole('button', { name: 'Workflows', exact: true })
Expected: visible
Timeout: 120000ms
Error: element(s) not found

Call log:
  - Expect "to.be.visible" with timeout 120000ms
  - waiting for getByRole('button', { name: 'Workflows', exact: true })

Status: blocked
Screenshots: screenshots/raw/STOP.png; screenshots/annotated/STOP.png
