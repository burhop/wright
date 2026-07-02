# Contract: Frontend Type Generation

## Generated Artifact

```text
apps/web/src/types/generated/wright-contracts.ts
```

## Source Models

- MCP policy decision
- Validation evidence and step evidence
- Agent runtime provider metadata
- Workspace service response/result DTOs

## Rules

- Generation is deterministic and offline.
- Generated files are checked in.
- Frontend-owned display labels, icons, and layout metadata are not generated.
- A freshness check fails if generated contracts differ from the checked-in artifact.
