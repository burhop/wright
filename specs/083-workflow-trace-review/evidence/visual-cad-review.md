# Visual CAD Review Evidence

Date: 2026-09-17

The campaign renderer now promotes retained engineering visuals only when they add review value. The Raspberry Pi enclosure report presents the supplied design sketch directly and embeds two bounded, retained final enclosure STL variants in offline Three.js viewers. Fluid-domain STL files remain available in the full-data package but are not presented as final product geometry.

The same report projects `cad-export-inspection.json` as engineering verification: 14 expected outputs present, 14 retained SHA-256 identities matched, representation counts, contract-read status, and a collapsed file-level integrity list. Raw byte-count observation tables are suppressed. Campaign event order supplies explicitly labeled `Next recorded activity` connectors; the report states that these do not establish unrecorded artifact lineage.

Verification:

- Focused Python workflow-trace and export API suite: `59 passed`.
- Existing offline export, iteration, progressive-input, and 30-activity Playwright suite: `7 passed`.
- New visual CAD and all-campaign offline Playwright suite: `2 passed`.
- Campaign archive/resource verifier: `30 verified`, `0 failures`.
- The visual test checks one retained input image, two nonblank WebGL canvases, ten recorded-order connections, independent responsibility-row expansion, CAD verification content, mobile containment, zero remote requests, and zero browser errors.

Generated local review:

`/home/burhop/repos/wright/.local-run/feature-083-reports/campaign-081/reports/raspberry-pi-enclosure-01/full_data/index.html`
