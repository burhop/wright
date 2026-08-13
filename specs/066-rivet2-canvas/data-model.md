# Data Model: Modern Rivet Canvas Editor

No new durable database entity is introduced. The feature replaces an editor artifact and defines ephemeral bridge/session state around existing workspace workflows.

## Editor Artifact Manifest

| Field | Meaning | Validation |
|---|---|---|
| `source_repository` | Approved Rivet 2 repository | Exact HTTPS repository URL |
| `source_revision` | Reviewed source commit | Full 40-character commit SHA |
| `rivet_app_version` | Upstream editor package version | Major version 2 |
| `entrypoint` | Hosted build entry document | Confined relative path below editor root |
| `sha256` | Deterministic artifact-tree digest | Lowercase SHA-256 |
| `patches` | Ordered Wright patch identities and digests | Every applied patch must be listed and verified |
| `license` | Upstream license identity | MIT for the selected source |

## Canvas Session

| Field | Meaning |
|---|---|
| `workspace_id` | Server-derived workspace boundary |
| `workflow_slug` | Active Wright workflow identity |
| `workflow_revision` | Revision used for the next Wright save |
| `target_origin` | Exact isolated frame origin accepted by the bridge |
| `phase` | `starting`, `ready`, `opening`, `editing`, `saving`, `error`, or `stopped` |
| `latest_project` | Ephemeral current Rivet project snapshot inside the frame |
| `pending_requests` | Bounded request IDs awaiting acknowledgement |

### State Transitions

```text
starting -> ready -> opening -> editing -> saving -> editing
    |          |         |          |         |
    +----------+---------+----------+---------+-> error
editing -> opening (replace active workflow)
any live phase -> stopped
```

The workspace project remains authoritative. `latest_project` is never restored as durable truth without a successful revision-aware Wright save.

## Editor Bridge Message

| Field | Meaning | Validation |
|---|---|---|
| `type` | Versioned command or event discriminator | Allowlisted values only |
| `requestId` | Correlates a command and one terminal response | Non-empty unique string; bounded pending map |
| `project` | Serialized Rivet project for set/get operations | String with size bound; parsed and normalized before activation |
| `error` | Structured safe failure detail | Code plus user-safe message; no path or secret disclosure |

Messages from any origin other than the exact isolated editor/parent origin are ignored. Unknown discriminators never mutate session state.
