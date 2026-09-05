# WebKit focus fixture correction

Reviewed correction: `114fba07a1912a28c0251f1d24ece76c71447406`, based on candidate `40ebc645ddb641503706dcb3a7d9c84a2b685359`. Only `tests/ui-integration/workspace-surfaces/presentation-fixture.ts` and `focus-layout.spec.ts` changed. Product source, browser configuration, retries, timeouts and existing focus assertions are unchanged. Prettier also wrapped existing long lines within the edited test file.

## Cause

The shared shell fixture listed ready live application surfaces but did not mock the runtime inspection endpoint requested by `LiveAppControls` during mount. The dev server returned HTTP 200 HTML to `/api/workspace/surfaces/{surfaceId}/live-app`. Its JSON parse error inserted an alert above the focus button. In the original failed trace the two response completions at 275314.640/275314.776 ms fall within the click interval 275298.040–275350.922 ms. The input snapshot lacks the alert; the following snapshot contains it. No focus reducer or persistence overwrite was evidenced.

Original trace is retained unchanged at `original-40/trace.zip`, SHA-256 `f0918cfd9c27ac9a198fc2245cf2cd720f856d046d90c53ab9e2b9a7b253b3a5`. The independent reviewer also inspected this chronology and the controlled pointer proof.

## Controlled reproduction and correction

`controlled-race-probe.spec.ts` holds the runtime response, presses the pointer on the focus button, releases the malformed HTML response, and releases the pointer after the resulting alert appears. The button moves from Y 222.34375 to 244.734375. Recorded event targets are mouse-down BUTTON `surface-enter-focus`, mouse-up P, click DIV `live-app-surface`; the button does not receive a click and layout remains normal. This bounded WebKit reproduction passed once in 3.9 seconds. Its source and raw trace are retained separately and are not added to the product test population.

The correction adds exact routes only for fixture-declared live instances. Runtime DTOs preserve each descriptor's surface ID, instance ID, generation, lifecycle and sharing. Unknown surface endpoints remain unmocked, and later test-specific overrides retain normal Playwright precedence. The focus test now requires both runtime responses to be JSON with matching identities and verifies that runtime controls contain no unexpected alerts. Its original mouse click, focus, chat, resize, tab switching, restoration and sidebar assertions remain.

## Bounded validation

- Original focused WebKit test, once before edits: 1 passed in 17.4 seconds. This passing rerun was diagnostic, not closure.
- Controlled malformed-response pointer reproduction: 1 passed in 3.9 seconds, demonstrating the failure cause.
- Strengthened focus test before fixture correction: failed deterministically because `text/html; charset=utf-8` is not the required `application/json`.
- Same strengthened WebKit test after fixture correction: 1 passed in 4.9 seconds.
- Both focus-layout tests across Chromium, Firefox, WebKit and the existing desktop-host project: 8 passed in 20.7 seconds.
- Existing WebKit live-app lifecycle journey: 1 passed, preserving its later runtime override and crash/retry/panel/browser/transport/navigation/restart/stop assertions.
- Prettier on the two edited files and `git diff --check`: passed.

Commands are retained in `run-focused.py`, `run-race-probe.py`, `run-layout-projects.py` and `run-live-app-override.py`. They invoke the installed Playwright CLI with explicit Node 24.19.0, a minimal synthetic environment, retries zero, one worker, task-owned Vite port 15317 and trace recording. No full gate or product suite was repeated. All task servers terminate with the runner.

## Fixture consumers

Ready live-instance consumers affected by the new runtime route: focus-layout, focus-accessibility, frame-fallback, hostile-surface and presentation-choice. The live-app spec supplies a later overriding runtime route, verified above. Presentation-restore passes stopped/no-instance or empty fixtures; rivet-ai and rivet2-canvas pass empty lists, so these consumers receive no new route. The parent owns wider gate selection and final integration.

Raw reports are local evidence; this document does not claim an additional real backend, Docker, human-study or production acceptance run.
