# Proposed Report API, UI, and Export Contract

## Application Boundary

Expose thin FastAPI routes under the existing workspace/session scope. Proposed relative resources are `workflow-runs/{run_id}/trace`, its `occurrences`, `traversals`, `artifacts`, and `evidence` children, plus `trace/exports`. Final route names must follow current workspace routing during implementation. All operations delegate to `workspace_service`; files remain behind existing authorized file access.

| Operation                      | Behavior                                                                                                                                                 |
| ------------------------------ | -------------------------------------------------------------------------------------------------------------------------------------------------------- |
| Read report summary            | Returns pinned report revision, run outcome, purpose, primary deliverables/previews, and links for lazy details. Does not load full logs or file bodies. |
| Read graph                     | Returns executed semantic definition projection, saved or deterministic fallback layout, recorded state references, and selectable element IDs.          |
| Read occurrence/traversal list | Cursor-paginated records for one selected block/path, preserving parent scope and attempt order.                                                         |
| Read evidence/artifact detail  | Returns original identity, availability, provenance links, producer-authored claims, representations, and authorized viewer/download references.         |
| Request export                 | Pins report revision and mode (`report_only` or `full_data`), creates a bounded background archive job, and returns its identity.                        |
| Read/cancel/download export    | Exposes archive progress, cancellation, failure, and completed download without affecting workflow execution.                                            |

Use immutable report revisions for detail requests so a concurrently arriving check cannot mix evidence snapshots. Return explicit not-found, incompatible-schema, or unavailable-content states. Keep performance and pagination limits in service configuration and test them. No endpoint runs a validator, model, CAD operation, or workflow.

## Progressive Disclosure

The results surface contains a compact run heading/outcome, concise purpose, final deliverables with actual previews, and export access. A recorded error or blocker is visible when applicable. Do not reserve space for an empty concerns panel, mandatory matrix, or permanently open inspector.

The reviewer can open the process graph and select blocks, connections, groups, and iteration badges. Selection opens one contextual detail panel with progressively expandable inputs, outputs, evidence, prompt, and technical activity. Closing it restores focus and the prior viewport. Keyboard users can reach the same subjects through an equivalent step/connection list. Small screens show one detail view at a time; the graph does not obscure deliverables or controls.

Use existing tokens, icons, viewer surfaces, and download controls. Do not make the results page a new authoring interface. Artifact counts and expandable groups keep large projects scannable. Description summaries must come from recorded titles/purpose or explicitly identified presentation text; do not fabricate decision explanations.

## Engineering Presentation Examples

| Output                    | Default presentation                             | Deeper inspection                                                                                   |
| ------------------------- | ------------------------------------------------ | --------------------------------------------------------------------------------------------------- |
| Design document           | Title and document preview                       | Source inputs, requirement/approval revisions, decisions, exact prompt                              |
| CAD model or assembly     | Recorded render or qualified model preview       | Original STEP/native files, version lineage, linked geometry validation                             |
| Mesh                      | Recorded image or qualified 3D representation    | Mesh file, recorded counts/density/units, generating settings, existing quality/convergence reports |
| Simulation                | Produced plots or images and named result report | Model and mesh revisions, material/BC/settings documents, field data, recorded check results        |
| PCB/harness               | Board/schematic preview and final package        | BOM, connections, native project, external ERC/DRC reports                                          |
| Printed/manufactured part | Part preview and output package                  | Source image/model, repaired mesh, orientation/slice/manufacturing settings and external checks     |
| Numerical/controls study  | Supplied plots and summary document              | Raw tables, configuration, units, parameter/assumption records, verification evidence               |
| Unsupported native format | Available image and original-file access         | Producer identity and linked neutral exports; no claim of browser-native support                    |

These are rendering choices for recorded evidence, not a requirement to create new checks or complete absent engineering outputs.

## ZIP Layout

```text
index.html
manifest.json
report/                 # embedded/paged report data and navigation assets
assets/                 # local CSS, scripts, images, optional viewer bundles
inputs/                 # retained original input versions (full-data mode)
outputs/final/          # principal deliverables (full-data mode)
outputs/iterations/     # occurrence-specific intermediate versions
evidence/               # requirements, decisions, approvals, external validation
execution/              # definition, recorded prompts, tool activity, diagnostics
licenses/               # notices for bundled viewer resources
```

Logical grouping can map multiple provenance references to one stored blob. Preserve useful project-directory structure for multi-file artifacts and disambiguate repeated names. The manifest records original subject ID, package path, digest, size, media type, role, and availability. Preserve originals byte-for-byte; a converted or rewritten portable document is a separately identified representation with its own digest.

`report_only` includes the navigable report, its evidence descriptions, and display assets. File bodies omitted by that mode have a deliberate omission state. `full_data` includes all retained referenced data within the authorized scope, including available failed-attempt and input files, and lists unavailable/session-only/external resources. It is not an arbitrary recursive archive of the host or workspace.

Archive construction snapshots its membership and checks each retained file's byte identity before publishing the final archive. Stream large entries to a temporary archive on disk; do not hold whole simulation directories in RAM. Abort publication on an integrity mismatch rather than substituting current bytes. Report unavailability separately from an actual mismatched retained version.

## Offline Browser Behavior

After extraction, `index.html` must work under `file://` without Wright, authentication, a local web server, or a network connection. Embed the bounded report model safely in the HTML or use local classic-script chunks rather than relying on fetch of adjacent JSON or server-only module loading. File links are relative and remain valid after moving the folder. Passive HTML still provides results and file navigation if optional interactive assets fail.

Qualify a self-contained Three.js-based STL viewer first using the already installed library and parser. Where file-origin restrictions prevent automatic model loading, a bounded embedded display representation may be used; large originals stay separate. Add 3MF or STEP viewers only through proven available libraries/routes with acceptable packaging, not handwritten parsers. Direct STEP viewing in Wright and STEP viewing in exported HTML are separate capabilities.

Fallbacks retain an actual recorded preview where available, an original-file link, and a short unavailable-viewer state. An image absence is not filled with unrelated imagery. No viewer checks the engineering validity of its subject.

Link rewriting applies to generated navigation and separately identified portable document representations. Preserve original reports; unresolved external or host-specific references are recorded in the manifest and exposed locally instead of pretending they work offline.

## Acceptance

Test a moved export under a browser's actual file origin with all networking disabled. Exercise results, graph selection, iterations, evidence navigation, repeated filenames, a multi-file deliverable, missing resources, and both export modes. Check every generated internal link and advertised viewer, including canvas pixels and interaction for 3D. A working HTTP preview is not evidence of offline export completion.
