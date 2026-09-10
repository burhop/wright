# kernelCAD MCP follow-up

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

Recheck the publisher for a release whose runtime dependencies are immutable
registry artifacts. Once it installs without weakening Wright's package policy,
run a parameterized mounting-bracket task through `GatewayService`. Independently
inspect the editable source, feature dimensions, STEP/STL file structure and
geometry, then exercise invalid geometry, timeout/cancellation, workspace path
controls, and cleanup before considering promotion.

Primary sources:

- https://github.com/w1ne/kernelCAD-web
- https://registry.npmjs.org/kernelcad/-/kernelcad-0.15.0.tgz
