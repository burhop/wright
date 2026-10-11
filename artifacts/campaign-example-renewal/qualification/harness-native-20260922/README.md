# Actual native harness correspondence checkpoint

Captured 22 September 2026. These are isolated engineering-tool qualification
results, **not complete campaign packages or full-scope engineering approval**.

| Case | Actual result | Native ERC | Original receipt SHA-256 |
| --- | --- | --- | --- |
| 01 | Pin/net/splice correspondence passed, including B1 | 0 errors, 4 library warnings | `e1d1d7f295ed6615c9e330de7e501f6717bdc618dd6b2a59451e2bd6708ce5c9` |
| 02 | Pin/net/splice correspondence passed, including B0 | 0 errors, 5 library warnings | `80bd88647b27d45e880ebd03f659b8fcaf128438cdca38e756a8123862b0a762` |
| 03 | Native component creation rejected `S_ZX`; stopped before export | Not reached | `61909afb09ca1b6b476c03264b217a408f604f4579189ee81e55169e87cb12ac` |

Each numbered directory preserves the actual tool responses and unchanged
receipt. Cases 01/02 also contain the saved KiCad schematic and native
`check/netlist.xml`, `erc.json` and hash-bound `inspection.json`. `source-inputs`
contains byte-identical copies of the real upstream WireViz pin schedule and
independently extracted netlist. Original absolute locations in the receipts
describe the execution host; these copies make the relevant evidence portable.
The old missing-B1 schematic was not overwritten.

Execution used the real Wright StdioRunner/GatewayService, selected KiCad MCP,
and image `sha256:5203521497814b23db6eab50ebd2a5cef208ee0bf164bbdf4164eb3268f72cd9`.
Each container had no network, 2 CPUs, 3 GiB memory, a read-only source mount,
and a fresh writable output mount. Containers were removed when their probes
ended. No Solid Edge operation or host engineering-software installation occurred.

The planner in `scripts/qualify-harness-kicad-runtime.py` now consumes the real
released pin schedule and fixed profile map instead of a three-connector sample
that omitted splices. Its offline tests cover all three schedules and malformed
maps. Those tests do not establish native compatibility for case 03: its actual
MCP rejects the underscore reference. A prospective explicit splice alias needs
coherent planner/profile/reader changes and new native proof; that repair was
not implemented or dispatched before the user's stop request.

All native ERC warnings remain in the receipts. They report the missing global
Connector_Generic library configuration; embedded symbol pin definitions were
present and independently compared. These warnings are not silently erased.
Total voltage drop, proposed contact/splice resistances and required human
reviews remain outside this proof. No campaign counter receives credit.
