# Data Model

| Entity | Durable location | Key fields |
|---|---|---|
| WorkflowProject | `workflows/<slug>/workflow.rivet-project` | workflow_id, format_version, title, revision, content digest |
| DatasetSidecar | `workflows/<slug>/datasets/<name>.json` | dataset_id, name, revision, digest |
| WorkflowIndexRecord | additive SQLite index | workspace_id, workflow_id, slug, title, revision, lifecycle state, timestamps |
| RecoveryRecord | `workflows/.deleted/<id>/<revision>/` plus index | deletion time, actor, original slug, revision |

The project and sidecars are authoritative. The index is rebuildable cache/metadata. No secrets, user session, runner state, or approval state is persisted here.
