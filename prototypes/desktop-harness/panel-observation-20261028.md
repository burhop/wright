# Bounded observations from the Wright panel

The desktop delivered `wright.native-navigation/1` context while the user clicked
between the workflow editor and working view on 28 October. That establishes a
working frontend-to-conversation path, not a screenshot or Windows acceptance.
Use that path to carry compact diagnostics instead of depending on discovery of
the experimental frontend inspection tool.

The existing navigation context now includes `ui_observation`: a per-panel
instance ID, timestamp, bundle identity, document visibility, viewport, bounded
control geometry/state counts, image loading/failure counts and recent error
counts. Navigation still carries the exact workspace, accepted source and, when
selected, run ID. A remembered workflow on Home is not the active workflow view;
`active_surface` and the instance ID disambiguate independently open panels.

Reuse `captureUiReview`, `App.updateModelContext` and the existing navigation
owner. Coalesce observations after paint; send only changed observations. This
does not invoke the model, poll, capture the desktop, upload reports, alter
workflows, grant actions or create another execution/state authority. No DOM
text, form contents, image URLs, raw errors or credentials are included.
Measurements can identify clipping or failed images, but cannot establish visual
quality, native tab restoration, downloaded Windows files or engineering acceptance.

## Qualification

- 16 focused observation/navigation tests pass, including private-content
  exclusion, bounded sampling and visible versus offscreen clipping.
- TypeScript and changed-source ESLint pass. The bundled resource has zero
  external assets.
- The actual retained run `91c3fe3f4e0c477e9d9ea0d0dde477b2` passes the
  read-only compiled-resource journey in a simulated Linux native-file host.
  The emitted context contains its exact run and build, and the loaded image.
  An injected clipped control and broken image appear in diagnostics; removing
  them clears the findings. Twenty unchanged resize events produce no additional
  context messages. Private fixture text is absent from the context.
- Original image/report hashes, producing-step availability, absence of a false
  source mismatch, exact same-run return, narrow-panel preview and source/history
  preservation pass. No engineering workflow is started, resumed or retried.
- The initial test correctly rejected candidate HTML against the old client's
  pinned hash. A separate candidate client freezes the new resource while
  retaining the backend binding and tool configuration. Installed metadata was
  not weakened or edited to pass the test.

Evidence: `.local-run/engineering-run-journey-20261028/panel-observation/`,
especially `results-observation-r2/report.json`, `actual-context-image.json`,
`diagnostic-fault-context.json` and the retained qualification script. These are
simulated-host results; delivery of the additional diagnostics by the actual
Windows desktop remains unverified until observed in this conversation.

The earlier Robot Tracking Diagnosis shared-editor regressions remain valid;
this change introduces no workflow-specific dispatch, instructions or runtime
behavior. Historical CAD documents, runs, outputs and reviews remain untouched.
