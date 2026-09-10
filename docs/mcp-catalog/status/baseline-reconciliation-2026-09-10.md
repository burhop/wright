# Combined integration baseline reconciliation

The reviewed baseline contains 78 canonical records. Each canonical ID occurs
once. Aliases, launch configurations, and tool counts do not add integrations.

| Protocol family | Tracked |
| --- | ---: |
| MCP | 73 |
| WebMCP | 3 |
| Hardware MCP | 2 |
| **Total** | **78** |

| Status | Count | Legacy source |
| --- | ---: | --- |
| Works | 10 | Current scoped qualifications |
| Preview | 4 | Useful passed execution evidence without full qualification |
| Requires login | 10 | Observed authentication boundaries |
| In progress | 36 | 26 environment-dependent records plus 10 repairable failures |
| Abandoned | 18 | Reviewed excluded archive |
| Blocked by vendor | 0 | No attributable vendor restriction is recorded |

The 24 green records are 10 Works, 4 Preview, and 10 Requires login. This is a
technical-assessment measure. Repeat customer adoption is unknown.

Four legacy examples received an explicit migration review:

- `web3d-mcp` remains Preview. Protocol and representative tool operations
  passed on Node 22, while 33 dependency advisories, the observed Node-version
  mismatch, and the full Wright gateway scope remain unresolved.
- `kernelcad-mcp` is In progress rather than Abandoned. Its clean-container
  package failure happened before protocol execution and has a concrete repair
  and retest path.
- `autocad-mcp-u-c4n` is Works only for the qualified headless DXF fallback;
  live Windows AutoCAD COM behavior is outside that claim.
- `rhino-mcp-easehee` is Works only for the qualified headless solid 3DM scope;
  live Rhino/Grasshopper and mesh/STL behavior remain outside that claim.

No historical evidence supported a backdated growth curve. The first status
publication therefore contains one real observation and states that history
collection has started.
