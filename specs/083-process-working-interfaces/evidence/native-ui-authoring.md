# Native interface authoring checkpoint

Date: 2026-10-01. Branch: `codex/083-process-working-interfaces`.
Parent: `e7aca677c74de55391e6af3bc7d6f3428ae33e0a`.

## Implemented scope

T038 adds authenticated native capability, generation/update, bounded observer,
explicit cancellation, status, preview, save, compatibility, revision listing,
activation/rollback, saved-presentation and close routes under the existing
`/api/workspace/process-interfaces` mount. They use the existing authoring,
immutable revision and process owners. Request identities are retained before
model/build work; a dropped observer never cancels or replays generation. Status
exposes a server-recorded preview observation so the next workspace controls can
explain when saving becomes available. Native workspace collaborators can inspect
their authorized workspace's jobs; an issued presentation remains principal-bound.

The native presentation owner verifies the exact immutable bundle, accepted
bindings, saved revision and optional durable run before installing a fixed
Wright declaration. Existing SurfaceService, LiveAppControlService,
PresentationService and CapabilityGrantService own declaration, runtime,
bootstrap and grants. Model code selects no launch command, origin, principal or
permission. Preview grants are read-only; working views require a saved revision.
Reusing a presentation request cannot change its mode/run binding. Revoked grants
are not silently renewed. Native close disposes the exact presentation, revokes
its grants and stops only its UI runtime after the final presentation closes.
It never calls the process cancellation owner.

Trusted compiler discovery checks a local checkout or an administrator-configured
root. Missing resources report an unavailable authoring capability without
installing anything. Directory presence alone is not qualification: the fixed
toolchain verifies actual installed package identities/versions. Packed installed
client/kit resources and their distribution proof remain T032/T050/T051 work.
Saved-view opening does not invoke the model or compiler.

## Verification

The [checkpoint manifest](../../../artifacts/process-interfaces/083/20261001-native-ui-authoring/checked-scope.json)
records exact owned hashes, commands, logs and protected-file checks.

- Qualified group: **150 passed**, zero skips, 102.38 seconds. Includes native
  authoring routes; actual immutable revision, grant, presentation and process
  repositories; controlled model/compiler/runtime manager; existing authoring,
  real fixed local build, migrations, preview bridge, surface lifecycle and
  process API/package-boundary regressions.
- A controlled active source run remains running after its saved view closes.
  Two actual durable source-run records reuse one saved UI/revision with one
  controlled authoring invocation. Both execute the existing source runner with
  controlled text output, not engineering MCPs. No additional executor exists.
- Save-before-preview, wrong source/build/job identity, stale active revision,
  update/rollback, unavailable model/compiler, viewer-role denial, foreign
  presentation principal, revoked grants, policy rejection, corrupt declaration,
  observer expiry and explicit cancellation are checked.
- Ruff and whitespace checks are recorded with the checkpoint capture.

The earlier API attempt had three passes and three assertion failures: the
save-before-preview owner correctly returned forbidden; authorized workspace
collaborators can read job status; and the qualified-adapter guidance is in the
correction field. The initial owner attempt caught an incorrect ownership enum
spelling, which was fixed to the existing enum. Later owner attempts corrected
fixture grant-list selectors, a private supervisor-field assumption and a missing
saved fixture source file before using the public run projection. The final group
checks the corrected paths. The intermediate qualified group passed 143 checks;
counts overlap and must not be summed.

Preview observations in these tests are explicitly synthetic. No actual managed
browser, native workspace authoring journey, new live model/MCP demonstration,
engineering acceptance, physical/supplier operation or installed distribution
proof is claimed. T034/T037/T039–T042, T021, remaining T032 and M4–M5 stay pending.
Native frontend authoring work has begun separately and is excluded from this
backend checkpoint until its checks and workspace integration are complete.
