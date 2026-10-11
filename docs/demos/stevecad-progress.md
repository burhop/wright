# SteveCAD integration and engineering demonstrations

## Current scope

The user requested a new SteveCAD MCP integration in Wright and three substantial
engineering demonstrations, followed by unpublished social assets. The user
confirmed the proposed structural mount, heat-spreader comparison, and PCB
enclosure portfolio. On 11 October they clarified that adding the new MCP is the
immediate priority. Demonstration execution and social content follow actual
connection and output verification.

## Isolation and baseline

- Branch: `codex/stevecad-engineering-demos`.
- Worktree: `D:/repos/wright/.local-run/stevecad-engineering-demos`.
- Fetched `origin/dev`: `ba2fad68c181165b96b9c15c40b1a1f63c88acb3` (PR 140 merge).
- Git checkout requires per-command `-c core.longpaths=true` on this Windows host.
- Existing checkout, untracked evidence, profiles and protected runs preserved.
- GitHub baseline checks include failures and unfinished jobs. This baseline is
  identified, not certified globally green. Local relevant checks are recorded
  separately. No production release or social publication is authorized.
- GB10 Codex adapter work remains separate. This change adds provider metadata;
  it does not modify model adapters or instruction/execution owners.

## Integration

Official documentation and live public resource discovery establish
`https://stevecad.studio/mcp`, streamable HTTP and account-scoped OAuth. New catalog
metadata reuses existing onboarding, remote transport, secret storage and gateway.
No vendor implementation, local CAD host, new executor or new UI is added.
Native Windows connected using Wright OAuth: STEVE CAD 4.0.10, MCP 2025-11-25,
26 tools, successful `list_skills` and `api_reference` calls. The existing Wright
gateway discovered 26 prefixed tools and proxied `api_reference(Model.box)`.
Catalog checks: **17 passed**. The first stale 81-entry count failure was corrected
to 82; no existing catalog entry or requirement was changed.

An isolated normal Wright API/workspace runs on port 8891 using separate SQLite,
secret storage, workspace directories and source from this branch. SteveCAD is
installed and active there. The existing runtime on port 8884 remains unchanged.
Native read-only evidence is recorded; container and CAD geometry remain untested.

## Portfolio after connection

1. **Structural equipment mount:** reuse the existing lightweight-equipment-bracket
   assignment and structural profile. SteveCAD produces editable CAD and exact STEP
   revisions. A qualified existing structural/meshing provider consumes that
   geometry for loads, mesh refinement and stress/displacement evidence. Required
   checks cannot be substituted with a render or a provider success message.
2. **Heat-spreader comparison:** reuse the existing conduction sizing process and
   its analytical, heat-balance and mesh-stability checks. SteveCAD produces measured
   candidate geometry; the existing OASiS path consumes exact dimensions linked to
   exported geometry. Dimensional idealization is disclosed; arbitrary STEP
   topology import is not claimed without proof.
3. **PCB enclosure fit:** build on the existing sensor-interface PCB and enclosure
   examples. KiCad supplies an actual constrained board/mechanical envelope;
   SteveCAD builds the housing around it. Required electrical checks and mechanical
   clearances are verified independently. The catalog records a limited KiCad DRC
   path; do not claim full board readiness until a qualified path exists.

Each process retains exact source/input/output identities, digest-bound handoffs,
082 validation and genuine review authority. Missing capabilities block the
affected stage. Geometry, loads or requirements changes invalidate dependent
assessment/drawing/render outputs. Common working views and the refined editor
remain the fallback; new process interfaces are optional and version-bound.

## Outstanding

Verify a small CAD operation and the container boundary; finalize numerical requirements using existing
assignments; save/run processes through the normal workspace; retain attempts and
revisions; verify outputs; then create images, captions, posts and storyboard from
actual results. None of those downstream outcomes is claimed completed here.
