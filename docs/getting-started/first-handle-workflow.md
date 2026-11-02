# Your first engineering workflow: a replacement handle

Wright coordinates an engineering job: agree on the intent, hand outputs between
tools, inspect their evidence, and make deliberate decisions. This example starts
with a dimensioned drawer handle, then prepares geometry and compares two print
orientations. Inspect its supplied sketch before configuring tools or paying for
model work.

**Development guide — 23 October 2026.** This guide describes setup recipe
`printed-handle-orca` version 2. [Installed version 2 setup](https://github.com/burhop/wright/blob/dev/artifacts/first-contact/084/native-handle-ordinary-setup-013/README.md),
readiness and reopen checks pass in the isolated development build. The
[source8 digital run](https://github.com/burhop/wright/blob/dev/artifacts/first-contact/084/native-handle-final-019/final-validation/README.md)
completed with the user's final review and 43 passing checks. The
[side-orientation correction](https://github.com/burhop/wright/blob/dev/artifacts/first-contact/084/native-handle-correction-020/final-validation/README.md)
also completed with its own user review and43 passing checks. Physical
validation is not assessed; this is not a fit-tested handle or a published-release
availability claim.

## Explore first

Follow [Native Wright for Hermes](hermes-plugin.md), then open the URL returned by
`/wright start`. Use `/wright status` or `/wright doctor` for startup problems.
No source checkout is required.

1. Create or open a workspace. Choose **Workflows → Explore an example**.
2. Select **Replace a broken drawer handle**. Inspect its sketch, original
   requirements, tool contributions and recorded result. The left panel is the
   supplied sketch; the right panel is an unaltered image of the actual repaired
   geometry. Inspect the recorded provenance for its run/source/package identities.
   This is a recorded digital example. Your own run's tools still require setup.
3. Choose **Set up this job** to read the requirements. Give the example a name
   and choose **Create editable workflow** when it suits your task.

Browsing and creating a copy make no model or engineering-tool calls. The supplied
assignment already has dimensions; an unmeasured photograph is insufficient to
establish an arbitrary replacement part's requirements.

The recorded presentation is template1.0.1. Existing accepted processes keep
their saved source and runs. An untouched1.0.0 starter can show **Check unavailable**
because the current catalog no longer supplies that version; preserve it and
create an updated starter separately. A revised accepted process uses its own
current-source readiness checks. The recorded example supplies neither tool
qualification nor approval for that process.

## Prepare the prerequisites

Exploration needs none of the following. This setup recipe needs:

- A working model connection in Wright, with your provider access configured.
  Confirm that the selected model is available for your account; signing in does
  not establish that. The checked development route selects `gpt-6.1-sol`
  through Hermes; the original profile settings are preserved.
  The optional **Hermes Agent** chat indicator checks a separate HTTP connection;
  a red indicator alone does not diagnose the workflow's Hermes SDK connection.
  Use the process readiness result and its actual model evidence for that route.
- Enabled [FreeCAD MCP](../mcp-catalog/usage-guides/freecad-mcp.md) construction,
  [Blender MCP](../mcp-catalog/usage-guides/blender-mcp.md) repair and preview,
  [Orca through MCP shell](../mcp-catalog/usage-guides/mcp-shell-server.md), and
  [OASiS](../mcp-catalog/usage-guides/oasis-mcp.md) inspection capabilities.
  Follow their guides and the exact native versions shown in setup.
- The workspace mounted at the same absolute path in every selected provider.
  Setup shows the required path. This recipe supports POSIX paths without spaces.
- Four exported JSON profiles: P1S 0.4 mm machine, original process,
  Orca-compatible process, and PETG filament. Retain 0.20 mm layers, five walls
  and 40% infill. The compatible process preserves every original setting except
  the documented automatic support-wall mapping from string `-1` to string `0`.
  Keep both files; Wright does not supply these profiles.

Copy the profiles into the workspace folder shown by setup. Enable missing
capabilities in **MCP Tools**, then **Refresh choices**. Discovery alone does not
prove native operation, permissions or shared-mount compatibility.

## Prepare and inspect the process

In a newly created, unchanged starter's editor, choose **Set up this job**. This
setup form does not reconfigure an already edited or accepted prepared process:
it rejects a source that differs from its original starter. Preserve edited work;
use the advanced correction route below for the same process, or create a fresh
starter as a separate process. Check that the displayed recipe is version 2.
Select the four tools,
four files and final package orientation. Both orientations are compared; this
choice identifies the final package.

Choose **Prepare setup proposal**. Inspect its summary, saved/proposed source,
tool identities and file manifest. Confirm your review, then choose **Accept
prepared revision**. The exact selected files are pinned, and the same editor
opens the saved revision. Acceptance does not run or approve the engineering.
Resolving unsaved edits alone does not make an already revised process eligible
for this initial setup form.

Choose **Open working view**, review the inputs, then **Prepare and check inputs**.
Resolve the reported missing requirements. **Ready to start** describes execution
readiness; dimensions, strength and printability still need checks and reviews.

## Check time, cost and limits

Before starting, open `run-disclosure.md` in Workspace Files under this proposal's
`process-proofs/printed-replacement-part/setup-…/inputs/` folder. It describes the
stages and configured limits. It is also attached to the design-basis review
before geometry work.

Fresh-run time and cost estimates are **unknown** without a measured basis.
Timeouts and call-count limits are not price estimates or a total spending cap.
Provider billing and work continuing outside Wright after a timeout may remain
outside those limits. Read the disclosure before choosing **Start process**;
startup can itself use the configured model.

New proposals declare validation capacity of 32 MiB and 1,000,000 structured entities,
a shared cooperative timeout of 120 seconds and a memory setting of 512 MiB.
The memory setting derives allocation caps; it does not enforce an OS/RSS ceiling. These configure resources; all 43
engineering checks still apply. Existing saved sources retain their accepted
settings. The completed source8 assessment read 17 exact subjects totalling
24,136,179 raw bytes. Its 32 MiB limit is cumulative raw subject size; the entity
limit is each reader-supplied checkpoint count, not a sum across all checks.
[Observed resource scope](https://github.com/burhop/wright/blob/dev/artifacts/first-contact/084/native-handle-final-019/final-validation/resource-observation/README.md)
does not establish a validator-only RSS peak. Each new run still needs its own
complete packet validation.

## Review, return and recover

The process declares a design-basis review before construction and a geometry
review before slicing. Inspect attachments with **Open file**; **Open interaction
step** returns to the owning block. Respond to the exact review shown. The final
handoff is a manually reviewed local simulation, with no printer connection or
print start.

Closing the working tab leaves the run with Wright. Return through **Run details →
Previous runs → Open run in working view**, then **Refresh view** if needed.
Reopening does not start another run. After a failure or uncertain response,
inspect the saved outcome before retrying. See
[working interfaces](../workflows/process-working-interfaces.md) for recovery.
This handle recipe's orientation correction requires a new accepted revision
and a full fresh run, as described below; it does not reuse retained geometry to
promise cheap local recomputation.

For support, expand **Diagnose this run → Preview support file**. Review the
privacy-filtered contents, confirm the current preview, then **Export reviewed
support file**. It downloads locally; sharing is a separate choice. Expired or
changed previews need a fresh review.

## Change the preparation on the same process

Changing an existing prepared handle from pads-down to side is currently an
advanced source-authoring operation. There is no one-click reconfiguration
control. The initial setup form's orientation choice applies to a new starter;
creating another starter with Side selected is a separate workflow, not a
same-process correction.

For an existing process, prepare a versioned recipe/source proposal retaining its
workflow identity, original requirements, accepted instructions and exact profile
inputs. Bind the selected orientation, comparison, validation profile and fresh
output locations consistently. Inspect the complete proposal and its change
impact in the existing **Source** view before accepting the new revision. An
orientation change still requires both actual slices and fresh downstream checks.
This is advanced authoring; the retained qualification scripts contain local
identities and mounts and are not portable setup commands.

In the [recorded correction](https://github.com/burhop/wright/blob/dev/artifacts/first-contact/084/native-handle-correction-020/README.md),
revision 9 was accepted through the existing public
`PUT /api/workspace/workflow-sources` boundary, supplying the prior storage
revision and digest to reject concurrent changes. It retains the same workflow
path and identity as revision 8. A separate
[ordinary editor capture](https://github.com/burhop/wright/blob/dev/artifacts/first-contact/084/native-handle-correction-020/accepted-source/README.md)
verified the exact saved revision, Side profile and clean source, then closed
normally. The evidence proves API acceptance followed by installed UI display;
it does not claim acceptance by an observed editor Apply/Save click.

The recorded correction used a **full new run**: basis, construction, repair, both
preparations/slices/inspections, comparison, summary, simulated handoff, final
review and validation. Byte-identical geometry after fresh calls is not
incremental reuse. The old run and assessment stay readable as historical
evidence; their approval does not authorize the new package. A pending review
may be reopened and resumed within its own run; accepting a changed source is
a different operation: it saves a new revision. Starting that revision creates
a separate run.

Revision9/run `de60e23084294148a3a8129bf2bcb1b8` completed after its own human
review. Its selected side package is `30338284…ff54c`; the pads-down comparison
is `9bd5ea30…58f03`. The final assessment passes all43 checks over17 subjects,
with six human-review applications. The installed support view reopened the
same pending subject before approval; no work was replayed. [Exact completion
evidence](https://github.com/burhop/wright/blob/dev/artifacts/first-contact/084/native-handle-correction-020/final-validation/README.md)
retains full digests, decisions and the simulated receipt.

## What the completed development evidence establishes

Source8/run `f45755b659114ec6a746ceaa4f23b773` handed actual FreeCAD geometry to
Blender for repair/measurement/rendering, then used Orca for both preparations.
OASiS supplied standard-format preparation and passive inspection; no handle FEM
solve was performed. The final assessment has 43 passes over 17 subjects,
including six applications of the user's exact final digital review. Earlier
basis, geometry and test-transfer decisions retain synthetic integration-test
attribution. The normal setup route instead declares manual local simulation;
the recorded test enrollment is not customer authority or a required customer
setup procedure.

The source8 selected package is pads-down. Its receipt simulates an integration
handoff with no network dispatch. Digital profile eligibility does not establish
physical contact quality, support removability, hardware fit, strength, fatigue,
printing, certification, customer acceptance or comparative superiority.

The [version 2 setup capture](https://github.com/burhop/wright/blob/dev/artifacts/first-contact/084/native-handle-ordinary-setup-013/README.md)
separately records ordinary proposal acceptance, readiness, reopening and
missing-tool guidance. Watch the [137-second local development walkthrough](https://github.com/burhop/wright/blob/dev/artifacts/first-contact/084/native-handle-walkthrough-021/wright-walkthrough.mp4)
or read its [transcript](https://github.com/burhop/wright/blob/dev/artifacts/first-contact/084/native-handle-walkthrough-021/transcript.md).
It connects the actual job, accepted revision9 and new results. Cuts and held
frames are labelled; it is silent with captions and is not elapsed execution
time. API acceptance, UI display, synthetic intermediate decisions and the user's
actual final review remain distinct. The video retains development-draft labels
and is not a published release demo.
