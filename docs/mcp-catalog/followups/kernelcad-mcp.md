# kernelCAD MCP follow-up

Status: closed on 10 September 2026. Reopen only when the publisher ships all
runtime dependencies as immutable registry artifacts.

Reviewed 10 September 2026. Owner: Wright catalog maintainers. Next review:
10 October 2026.

kernelCAD 0.15.0 is a relevant mechanical CAD candidate. Its source-first
workflow, deterministic review tools, and STEP/STL exports match Wright's core
engineering focus.

Fresh review found npm 0.15.0 with integrity
`sha512-ZDdFsCX5ewTrhb8Hs9F+0psNW0QLCdIcTzX04BOLf3XUjDBGd+1630YqVg8Zt2oT0W5E3Rw/7HcNGAtyNV8HmA==`.
It did not initialize in a fresh disposable Intel Linux Wright container. npm
rejected this transitive package fetch:

`replicad-opencascadejs@github:w1ne/replicad-opencascadejs#kcad-v0.24.0`

Wright's clean-container image disables Git package fetches. The preserved
`kernelcad-0.15.0-preflight.json` records npm error `EALLOWGIT`, the immutable
candidate integrity, the exact environment, and clean shutdown. No MCP handshake
or CAD operation ran, so this is failure evidence, not a qualification.

The candidate is excluded from the product list after the same policy conflict
was reproduced in releases 0.11.2 and 0.15.0. If a future release removes the
GitHub runtime fetch, run a parameterized mounting-bracket task through
`GatewayService` and independently inspect the editable source, feature
dimensions, STEP/STL structure and geometry before reconsidering it.

Primary sources:

- https://github.com/w1ne/kernelCAD-web
- https://registry.npmjs.org/kernelcad/-/kernelcad-0.15.0.tgz
