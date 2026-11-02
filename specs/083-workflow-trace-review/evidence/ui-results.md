# UI Results

Recorded 2026-09-16 against the production build on port 8094 and managed
workspace `b5514bda-a2be-4926-8888-7e9de42b47a1`.

- The unmocked Playwright acceptance entered through the normal workspace
  Workflows control, selected `printed-replacement-part-01`, expanded Run
  details and the retained completed run, and opened its Trace page.
- Before browser navigation, the test requested all 24 exact indexed run paths
  from the live API and confirmed each original run ID, succeeded state, and a
  nonempty result set.
- Results are the initial Trace tab. Process, Evidence, and Run history remain
  behind explicit tabs; no concerns dashboard or Trace-generated verdict appears.
- The real `mesh-preview.png` campaign artifact rendered inline from a
  digest-checked, workspace-confined endpoint. The retained process graph showed
  four nodes and its selected-node detail opened and closed correctly.
- `source_mesh.stl` opened from the result card in Wright's actual Three.js
  viewer. The selected document tab appeared and a WebGL readback found more
  than 100 nonblack pixels.
- Both export modes were downloaded from this same run. The test extracted and
  relocated them, blocked HTTP and HTTPS, and opened both `index.html` files
  through `file://` with no network requests.
- The standalone HTML uses the recorded title, results summary, inline retained
  imagery, relative artifact links, expandable process occurrences, and embedded
  evidence/manifest sections. Its inspected full-page capture is
  `live-campaign/standalone-report.png`.
- The inspected results-first screenshots are
  `live-campaign/real-campaign-results.png` and
  `live-campaign/real-campaign-mobile.png`. The 390 px live layout stayed within
  its viewport and kept the retained image visible. The exact downloaded packages are `live-campaign/report-only.zip` and
  `live-campaign/report-and-data.zip`; both pass `unzip -t`.
- Earlier responsive fixtures remain beside this file as layout regression
  evidence: `trace-workspace-desktop.png`, `trace-workspace-mobile.png`, and
  `trace-workspace-text-200.png`.
