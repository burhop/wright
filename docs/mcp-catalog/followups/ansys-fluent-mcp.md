# PyFluent MCP follow-up

Reviewed 9 September 2026. Owner: Wright catalog maintainers. Next review:
9 October 2026.

Ansys' official PyFluent MCP 0.4.0 is a high-value CFD candidate. Its reviewed
universal wheel has SHA-256
`59e0e5d9613e5254830ccf5a919d7ec61affbe19608a11ccf4e296764d0fd72a`.

In a fresh disposable Intel Linux Wright container, the package initialized,
published 25 valid tools, and cleanly validated a small PyFluent launch script
without executing it. The preflight and offline-task attempts are preserved in
`ansys-fluent-0.4.0-preflight.json` and `ansys-fluent-0.4.0-offline.json`.

This result proves a narrow offline code-checking capability. It does not prove
connection to Fluent, a mesh or solve, numerical correctness, result export, or
Wright gateway operation. That narrow feature does not add enough engineering
value to curate the server by itself, so it remains in Follow up.

To resume qualification, connect a licensed Fluent 2024 R1 or newer instance and
run one deterministic CFD case through Wright `GatewayService`. Independently
inspect the mesh, convergence history, selected field values, and exported result;
then exercise an invalid setup, timeout/cancellation, reconnect, and cleanup. Keep
the Ansys license and any proprietary case data outside the repository.

Primary sources:

- https://github.com/ansys/pyfluent-mcp
- https://pypi.org/project/ansys-fluent-mcp/0.4.0/
