# Data model

`RivetNodeInvocation`: run ID, node ID, workspace/session IDs, declared tool,
bounded JSON input, trace ID. `RivetNodeResult`: typed output, approval/policy
state, artifact references, redacted diagnostic. No secrets are persisted.
