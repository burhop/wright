# Release Recovery

Recovery preserves immutable subjects. Never overwrite PyPI files or rebuild an
old OCI version. Native manager paths and Docker are independent mandatory
production paths.

## Manager adapter and runtime recovery

If the Hermes adapter clone does not match the recorded Git commit or its
provenance does not name the Wright release commit, stop before starting Wright.
Repair and resync the mirror, then retry only with the same release subjects.
The released-Hermes verification must use `hermes plugins install`, `update`,
and `remove`; a fixture cannot replace it.

If a published Wright update fails, retain the predecessor and use `/wright
rollback` only when packaged schema bounds permit it. `recovery_required` is a
stop condition. Default uninstall preserves `WRIGHT_HOME/data`; purge is
separate and requires the exact confirmation code for the disclosed path.

Codex profile failure does not authorize routing through Hermes.
Repair that manager's profile or evidence while retaining the same Wright
runtime subject.

## Python and OCI recovery

Never overwrite PyPI files. Publish a corrected patch; yank only for a broken,
incompatible, vulnerable, or prohibited release and record the reason.

For OCI recovery, preserve immutable version and digest references. Restore
`latest` only to a digest already recorded as verified. If Docker Hub failed
after GHCR passed, dispatch `recover-dockerhub-release.yml` with the existing tag
and recorded GHCR digest; do not rebuild or republish Python artifacts.

## Completion and evidence

Keep the GitHub Release absent or draft until PyPI, released-Hermes lifecycle,
the Codex profile, GHCR, Docker Hub, attestations, and documentation are
verified. Retain hashes, adapter identities, manager versions, lifecycle/MCP
results, forbidden-executable audits, approvals, promotion output, and recovery
decisions without credentials.
