# Blender MCP compatibility fixture

This test-only fixture vendors `safe_mode.py` from Blender MCP commit
`5f8ddaf6e987c4aa0c3467fcc548838b28f64477`. The committed LF-normalized
`safe_mode.py` SHA-256 is
`d3bc1f43f4707476e595efed111d514b3f81bf4358993b8accb18962c5c4bf35`.

The minimal `server.py` exposes only the import needed to discover Wright's wrapper
tool without starting Blender. Native lifecycle tests use the real qualified server.

Upstream license: MIT; see `LICENSE`.
