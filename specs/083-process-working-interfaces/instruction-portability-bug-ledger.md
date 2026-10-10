# Instruction portability — find and fix ledger

This goal's evidence is separate from earlier Feature 083 acceptance. Setup and
harness faults are retained as such; they do not establish product defects.

| ID | Reproduction / cause | Correction | Evidence / remaining qualification |
|---|---|---|---|
| IP-B01 | Fresh saved-workflow URL opens a blank canvas. Development StrictMode repeats the tab reset while the passive-link attachment guard retains its key. | Reset that guard whenever the owning viewer is reset. No workflow is created by opening a link. | `20261007-input-wait-01` failed; `20261007-input-wait-02` passes diagram wait, exact-run working tab and browser reload. Full-panel StrictMode regressions pass 2/2. Final production build remains pending. |
| IP-B02 | Isolated provider installation discovers tools, then fails synchronizing an unrelated host Hermes config. Explicit config selection still included host fallback write targets. | Explicit `HERMES_CONFIG_PATH` selects only that config. Optional unreadable host binding probes are handled without failing workspace load. | 14 gateway/config regressions pass. Fresh provider installs subsequently return 200; original user configuration was preserved. |
| IP-B03 | UI imports a portable workflow, then refuses the response because its source envelope lacks workspace identity and metadata authority. | Bundle router uses the scoped source envelope matching ordinary source routes. | Original UI failure retained in `instruction-authoring-transfer/20261007-07`; -08 passes the original reproduction and -09 passes all 11 steps including bundle transfer and exact imported positions. |
| IP-B04 | Newly added model readiness cannot confirm the gateway even though the normal model picker returns 200. Native Hermes exposes provider/model; Wright's facade exposes current_provider/current_model. | Reader accepts both explicit contracts and rejects incomplete or conflicting pairs. | Fresh frozen first-input run d2381e55fb9946b39bfca8df47275774 now passes preparation and waits. Actual submitted model lock still requires IP-B05 closure. |
| IP-B05 | Frozen model request fails before submission: lock endpoint requires an existing session but the adapter only generated a UUID header. | Create and verify the fresh private session through the existing Hermes API before confirming its exact model lock. Never change global model defaults. | Failed pre-dispatch logs retained. Served conditional ask c996ca8b361d4e2b8ceab30a3ba05ce9 and skip 79aeae6e30eb4b7bbbb36aa57b759be0 executed the actual model. Modern frozen first wait d2381e55fb9946b39bfca8df47275774 and conditional ask both completed the same run after restart, with invalid/stale/duplicate response checks. |
| IP-B06 | A raw tool returns useful solver diagnostics, then missing expected files prevent the returned response reaching completed-step evidence. Runtime output failure was labelled readiness failure. | Persist bounded redacted tool-response evidence and exact response hash before interpreting it or verifying outputs. Classify failed expected output as WORKFLOW_OUTPUT_INVALID. | 79 focused checks pass. Actual existing-provider negative runs b7e7b3c7727f45748093539b4ec12322 and 2eb73fce79464521b745f9bd9c8bc775 retain returned evidence and fail output verification, without result or replay. Ordinary UI failure visibility remains under qualification. |
| IP-B07 | Switching recorded-run evidence could briefly display a previous run's text or accept a late result under the new run. | Key evidence viewer by authenticated session and exact run-log locator. | RunInstructionsEvidence regression passes 5/5. |
| IP-B08 | Applying instruction settings remounted the modal, hiding acknowledgement and resetting expanded resources. | Preserve the mounted editor until close; reopening still reads fresh state. | Original served reproduction instruction-revisions/20261008-01 retained; -02 passes 11 revision, migration, copy and concurrent-edit steps. |
| IP-B09 | Native image preparation qualified the SDK, then typed input preparation recompiled the plan and discarded its image resolution. Frozen routing rejected the unqualified image step. | Retain the qualified resolution by exact accepted step identity when binding prepared inputs. | 51 focused checks pass, including fresh and frozen-input native image plans. Served fix loaded; actual CAD/image rerun remains in progress. |

| IP-B10 | Actual bridge response enriched the same nested capture object retained as the submitted request, changing historical phase/content. | Deep-copy adapter observer publications and recorder events/results/notifications. Do not reconstruct old events. | 21 focused checks; actual completed run e333f6183c704380bac48be20b402ccb readback verifies five ordered immutable submission/response pairs plus the native image SDK request. |
| IP-B11 | Tampered bundle validation included a Pydantic ValueError in response context, producing a 500 instead of a safe structured error. | Reuse bounded redacted JSON validation serializer for bundle routes, without echoing source/base64/credentials. | 39 automated checks; eight actual authenticated bundle cases reject missing/tampered dependencies with safe JSON before publishing files. |
| IP-B12 | Agent model badge was red because the workspace registry had no local model entry, although the configured gateway exposed the actual model. | Qualify the configured gateway separately; show unknown/configured yellow until probe, with no false green. | 14 API and three frontend checks; served UI shows Agent model configured/unprobed. Workflow readiness remains separate. |
| IP-B13 | Production saved interface failed401 SURFACE_PREVIEW_UNAUTHORIZED: proxy eligibility depended on DEV and middleware existed only on the dev server. | Permit verified loopback control origin in production and use the same authenticated surface middleware for preview. | 46 tests; failed saved-ui-reuse/20261008-02-production retained. Original production reproduction -03-production passes4/4, three served asset hashes match build02, thirteen original files and four UI tables unchanged. |
| IP-B14 | Strict CAD run6eb599a8d9af48eaa0bbfb6e07860f26 created geometry using unspecified choices before terminal assumption rejection. | Versioned portable action-intent envelope checked before gateway dispatch; strict legacy changing tools require explicit reviewed upgrade; save resource/schema/proposal identities and choices. | 84 focused runtime/schema/operation checks, 66 resource/settings/API checks, 24 parser checks; independent review and modern live positive/negative qualification remain active. Typed declarations do not semantically prove arbitrary prose or engineering correctness. |

## Retained setup and harness corrections

- IP-B15: Modern strict CAD run `a3b297f819724fb4b4b7be162319b834`
  stopped before AI geometry creation because the fixed action-intent envelope
  raised a valid provider schema from depth15/16 to17/18. A shared qualifier
  retains the original provider depth16 limit and allows the two additional
  levels only for the exact supported envelope. A marker alone cannot expand
  the limit; forged envelopes remain rejected. Runtime readiness uses the same
  qualifier before CAD setup.119 focused helper/depth checks pass. Corrected
  live strict run9ccec0d193204bb193aeeb6e6cc2de11 rejected the geometry proposal
  before gateway dispatch; only read-only server observation occurred.
- IP-B16: The final instruction audit found design-check, design-revision,
  expected-file and task-workspace guidance still embedded in implementation.
  Profile1.2 moves all four into frozen, inspectable versioned resources. Missing
  modern helpers fail readiness; existing saved sources require an explicit
  reviewed compatibility update. Custom bodies and policies remain preserved.
  Custom-resource and same-run recreation checks pass;34 wheel instruction
  resources and six authenticated exact-transfer cases pass. Final UI journeys
  remain pending.
- IP-B17: Genuine enrolled schema3 approval checkpoints were routed as legacy
  unenrolled decisions; optional omitted reason was forwarded as None to a
  string-only owner. The existing canonical approval owner now accepts schema2
  and schema3 approval checkpoints, rejects schema3 input/missing/unknown kinds
  before authority, and normalizes the optional empty reason.27 API checks pass,
  including real stdio exactly-once interruption/restart cases and six negative
  checkpoint-type cases. No review grant or enrollment requirement was weakened.
- IP-B18: Private workflow-source subroute validation could serialize exception
  objects from Pydantic context, returning500 instead of a useful422. Slash-bounded
  source subroutes now reuse the existing private bounded JSON-safe serializer,
  retaining no-store headers and omitting input/exception contexts.18 focused
  privacy/bundle and22 existing source API checks pass. An unrelated historical
  bundle traceback is not attributed to the later storage-exhaustion attempt.
- IP-B19: A plain AI prompt displayed Automation not configured from an unrelated
  MCP binding state despite a configured prompt/connection. Its card now labels
  the configured AI prompt without asserting model readiness. Focused UI checks
  and type checking pass; production06 includes the correction.
- IP-B20: Open representation initially left the document below the page. An
  immediate scroll also raced asynchronous text loading, reproduced in final
  production09. The shared passive viewer now reports committed preview readiness;
  only a deliberate exact-generation selection focuses/scrolls once after content
  or fallback is ready. Polling does not re-scroll, stale requests do not steal
  focus, and assessment navigation retains its target.106 common/UI-kit checks
  include delayed text and bitmap readiness; final live reproduction is pending.

- Installed browser could not launch inside the process sandbox; approved browser
  launch was used, with failed setup evidence retained.
- New isolated UI omitted its Workflows feature flag, and local gateway settings
  omitted the existing gateway credential. Corrected only task-owned configuration.
- Browser locators first matched instruction resource text and hidden kept-alive
  tabs. Exact visible controls are now used; these were harness faults.
- A test import filename used uppercase `A`; the safe-path validator correctly
  refused it. A lowercase destination passed without relaxing that validator.
- Gateway test workspaces located inside the application checkout were correctly
  rejected by the protected-root gate. Rerunning in the dedicated writable proof
  root passed without bypassing the gate.

## Observed successful live evidence so far

### Final exploratory CAD export handoff finding

**IP-B21:** Actual multi-provider run5a9d356cc77e488996a2dd7845a1b9ad completed
native CAD and verified its STL export, then the declared Blender file dependency
incorrectly reported that the connected file was not produced. CAD file ports
published a path string to response bindings; this consumer requires a verified
typed artifact/reference. The shared runner now publishes the existing
`file_result` with exact provenance and includes declared file dependencies in
the required connected-output check. Four new regressions cover valid handoff,
changed bytes, deleted file and never-produced export. The combined owning suite
passes92 checks with1 host symlink skip; Ruff passes. No artifact verification,
provider safe mode, output identity or engineering constraint was weakened.
  Owned API8065 PID41316 loads the correction. Actual final chain71811e15501344d084c5fd261c3060be
  verifies native CAD -> Blender -> offline slicer with six hashed outputs and
  exact file dependencies. Post-fix cross-workspace UI14/16 pass7/7 each; native
  image read-only UI18 passes3/3. The full owning workspace rerun passes2399 with
  24 host-specific skips. Earlier failed runs are retained. Intervening safe-mode
  export-directory and run-path limitations were handled in new explicit source
  definitions, without provider security changes or production-code relaxation.

- Existing local gateway model picker: 200, configured model retained unchanged.
- Material comparison produced through the real model: 3000 mm³, steel 23.55 g,
  aluminum 8.10 g, with scope limitations; declared downstream input then waited.
- Initial declared input waited without a fabricated upstream producer.
- First-question and after-real-comparison runs resumed and completed the same run
  through the configured model after service recreation. Invalid/stale answers
  remained pending, and duplicate answers before/after completion returned the
  same response. Synthetic answers retain integration_test=true and exact IDs.
- Existing numerical-analysis provider produced actual 697-node/1280-element
  fields for 40/60 mm conduction straps. Peaks 50/41.6667 °C and both 4 W balances
  match independent all-node readback of the idealized one-dimensional solution.
  This proves numerical analysis only, not hardware or manufacturing acceptance.
- Exact source A exported/imported while isolated global defaults B were active.
  Defaults were restored via compare-and-swap; existing waiting source digest did
  not change. This proof started no imported run.

Live provider qualification and final model routing, conditional waits, reviews,
portable working UI reuse and exploratory acceptance are still being completed.
