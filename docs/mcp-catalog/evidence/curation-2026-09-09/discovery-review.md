# Engineering MCP discovery review — 9 September 2026

The official MCP Registry was searched separately for `cad`, `ecad`,
`simulation`, and `metrology`. The raw bounded result sets are preserved in the
four `discovery-*` directories beside this report. The source-health research
attempt is preserved under `research/research.attempt.json`; it was partial
because 14 publisher sources were unavailable during this run.

The CAD query contained many substring and general-purpose false positives.
Desk review produced these decisions:

| Lead | Identity decision | Portfolio decision | Reason |
|---|---|---|---|
| `w1ne/kernelCAD-web` / `kernelcad` | New integration | Follow up as `kernelcad-mcp` | Strong source-first CAD fit, but npm 0.11.2 fails clean-container installation because it fetches a GitHub dependency. |
| `blwfish/freecad-mcp` | Existing family | No new entry | Already represented by Wright's FreeCAD identities; registry spelling must not inflate the catalog count. |
| `getfacade/mcp` | New lead | Leave in discovery evidence | Building-envelope design service needs a paid API and has lower value than Wright's current CAD/CAE qualification queue. |

The ECAD query returned FreeCAD substring matches rather than a new electrical
CAD server. The simulation and metrology queries returned no records. These zero
results are retained so a rerun can show newly published integrations rather
than relying on memory.

No source outage caused an automatic demotion. Source availability is one review
signal; catalog disposition still depends on identity, engineering value,
qualification evidence, and an explicit maintainer decision.
