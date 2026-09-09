# kernelCAD MCP follow-up

Reviewed 9 September 2026. Owner: Wright catalog maintainers. Next review:
9 October 2026.

kernelCAD 0.11.2 is a relevant new mechanical CAD candidate. Its source-first
workflow, deterministic review tools, and STEP/STL exports match Wright's core
engineering focus. The reviewed npm tarball has SHA-256
`faf3b230d45c1d0095a8555312719cc64b969e37d88b43c30108ad857bf1488a`.

The package did not initialize in a fresh disposable Intel Linux Wright
container. npm rejected this transitive package fetch:

`replicad-opencascadejs@github:w1ne/replicad-opencascadejs#kcad-v0.23.1`

Wright's clean-container image disables Git package fetches. The preserved
`kernelcad-0.11.2-preflight.json` records npm error `EALLOWGIT`, the immutable
candidate digest, the exact environment, an 18.282-second duration, and clean
shutdown. No MCP handshake or CAD operation ran, so this is failure evidence,
not a qualification.

Recheck the publisher for a release whose runtime dependencies are immutable
registry artifacts. Once it installs without weakening Wright's package policy,
run a parameterized mounting-bracket task through `GatewayService`. Independently
inspect the editable source, feature dimensions, STEP/STL file structure and
geometry, then exercise invalid geometry, timeout/cancellation, workspace path
controls, and cleanup before considering promotion.

Primary sources:

- https://github.com/w1ne/kernelCAD-web
- https://registry.npmjs.org/kernelcad/-/kernelcad-0.11.2.tgz
