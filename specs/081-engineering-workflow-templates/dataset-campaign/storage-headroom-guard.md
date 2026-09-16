# Campaign start disk headroom

## September 14 Windows temporary-directory verification

After the user restored D:, verification established that the real Windows
account `WORK17\markb` already had `TEMP` and `TMP` set to `D:\TEMP`. They were
reapplied after an actual write/delete probe, registry readback passed, and an
Environment-change notification was sent to Windows. The initial C: values
came from the different `WORK17\CodexSandboxOffline` account's HKCU environment;
they were not the regular user's persisted settings. The repair receipt's
before-values confirm this distinction.

An unsandboxed read of only TEMP/TMP from 25 running Codex, Hermes, Python and
uv processes found D:\TEMP in every inspected process. No restart is needed
for those processes to receive this path. Other applications can retain old
inherited settings until restarted. No existing temporary files were removed
or moved.

The prior values and verified result are retained in
`.local-run/feature-081-live/user-temp-repair-20260914T153824695Z.json`;
the bounded repair script is alongside it as `repair-user-temp.ps1`.
The machine/system temporary-directory settings were not changed.

This does not relocate the live campaign workspace:
`scripts/windows/start-engineering-workflow-demo.ps1` still configures
`C:\Users\markb\wright-feature-081` through the user-profile path. C: had about
0.24 GiB available during the repair. Workspace/export storage guards must
still pass before new runs. Relocation requires preserving workspace identity,
artifact paths, container mounts and approval/tool authority; changing TEMP
alone cannot perform that migration.

## Existing start guard

**Later September 14 update:** The user reported the disk problem addressed;
inspection found C:\tmp absent and approximately 9.95 GiB free on C:. Before
that change, a preservation copy to `D:\RecoveredTemp\C-tmp-20260914` completed
with Robocopy reporting 217,616 files and 10.104 GiB copied, zero failures and
zero mismatches. The subsequent independent SHA-256 audit was interrupted;
only `verified-files.jsonl.partial` exists under
`.local-run/c-tmp-relocation/`, not a successful full verification receipt.
Do not claim that full independent verification passed. The agent did not run
`finish-relocation.ps1` or delete the source. Keep the D: copy. The source's
absence prevents completing the original source-versus-copy hash audit.

The immediate disk shortage is now addressed. Keep the existing capacity guard
and prioritize other campaign reliability fixes; a larger future run still
needs sufficient measured headroom.

The September 12 live campaign encountered `ENOSPC` while publishing a run
record on the workspace volume. The persistent campaign runner now checks free
space on the actual workspace and export destination volumes immediately before
a **new** workflow start. A missing destination directory is measured using its
nearest existing ancestor, without creating an output directory.

The default minimum is 512 MiB on each volume. Configure another positive
threshold using `--min-free-disk-mib`, or `minimum_free_bytes` for a programmatic
runner. An insufficient or unavailable measurement records `storage_blocked`
with role, free/required bytes and a reason. No HTTP start request, dispatch
intent, workflow output receipt or run-count increment is created. A later
invocation may start once adequate space is available because no mutation was
attempted.

The check follows existing-run discovery and uncertain-mutation recovery. It
does not prevent observing an existing run or continuing its approved checkpoint,
and it never replays an uncertain start. The threshold is a preflight margin,
not a reservation or estimate of a particular solver's future disk consumption.

Validation: 44 focused runner/file-inspection tests passed; one Windows symlink
test was skipped because the host lacks creation privilege. Cases cover both
destination roles, missing-directory ancestry, unavailable usage information,
threshold configuration, recovery, existing completion, approved resume and
unknown-start protection. The file-inspector oversize test now uses a 129-byte
file with a monkeypatched 128-byte limit instead of leaving 256 MiB fixtures.
Actual engineering files and existing grants remain unchanged. No API or Hermes
restart is required; a newly launched runner loads this check.
