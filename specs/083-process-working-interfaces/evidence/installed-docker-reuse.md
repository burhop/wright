# Clean Docker saved-interface reuse — 2 October 2026

**Scope:** T051 native and clean Docker common/saved/open/reload behavior verified
after the diagnostic-strict fixture 014 rerun. Earlier fixture failures remain
preserved below.
Full engineering parity, editor acceptance, migration and
the complete implementation goal remain incomplete.

- [Docker wheel preparation: ten passing browser checks](../../../artifacts/process-interfaces/083/20261002-installed-docker-wheel-013/workspace-walkthrough/report.html).
- [Docker thermal analysis: ten passing browser checks](../../../artifacts/process-interfaces/083/20261002-installed-docker-heat-013/workspace-walkthrough/report.html).
- [Native checks and production repairs](installed-native-reuse.md).

The same local candidate wheel SHA
`2a4ee17102c8518d818320bc56a0107225e44ee87154709e5cad761f452b674e`
was installed in a dedicated temporary Linux venv using `pip --no-index --no-deps`.
It uses the cached standard Linux/amd64 image
`sha256:512b001cbffd0551969630eaf618d9d4fb72987bdfb6422d9d444d8ad2e8ee73`.
No checkout is mounted. Inputs are the local wheel, copied engineering workspace,
copied SQLite records and controlled host fixture. The root filesystem is read-only;
temporary writable storage is bounded to 1 GiB, with 2 GiB memory, two CPUs and
256 PIDs. No dependencies, compiler, model or provider software were downloaded
or added to the base image.

The installed API/core/storage/agent/workspace/registry/runtime modules are
asserted inside the dedicated installed venv. Compiler discovery is unavailable,
provider autostart is disabled, and the interfaces reuse their original immutable
compiled assets. The native distribution inspector passes on the current wheel;
the exact packaged frontend manifest matches the build record.

Browser access uses a loopback-only published port, bridge networking and the
existing authorized HttpOnly operator session. This proves authenticated Docker
workspace behavior, not a Docker login screen or native loopback cookie bootstrap.
Authentication, origin checks and presentation-derived scope remain enforced.
This browser proof is not `--network none`; the prior isolated static serving
proof and current offline-resource tests retain their narrower offline scope.

Both common and tailored views show the same exact recorded second runs and
pending reviews. Opening and reloading generated interfaces does not start,
resume, approve or cancel engineering work. Browser diagnostics have no uncaught
page errors. Attempt 013's diagnostic audit found MCP catalog/settings 500 responses from the
read-only fixture's unconfigured credential-store directory, plus the expected
503 from the unavailable model service. These prevented clean Docker qualification
until the correctly configured fresh rerun 014; the original interaction checks alone did not
establish an error-free workspace. After both journeys, all UI/revision/
authoring/continuation hashes match the original copied database baseline.
Only workspace activation and managed presentation/bootstrap operations occur.

## Corrected diagnostic-strict fixture 014

Fixture 014 uses the existing `WRIGHT_SECRETS_PATH` setting inside bounded writable
state storage; no provider credentials are added. The walkthrough now rejects
unexpected API responses or uncaught page errors before recording passing steps.
Both jobs pass all ten checks with zero unexpected responses and zero page errors.
Each records three expected `/api/agent/models` 503 responses because no model
service exists in the clean container. Authoring unavailability is explicit,
and saved UI reuse remains usable. Associated model-error console messages are
disclosed, not described as an entirely silent console. After both strict
journeys, UI/revision/authoring/continuation hashes match the original copied
baseline. Current proof host is 014 on port 8033; 013 is stopped.

- [Current wheel report](../../../artifacts/process-interfaces/083/20261002-installed-docker-wheel-014/workspace-walkthrough/report.html).
- [Current thermal report](../../../artifacts/process-interfaces/083/20261002-installed-docker-heat-014/workspace-walkthrough/report.html).
- [Current container identity](../../../artifacts/process-interfaces/083/20261002-installed-docker-reuse-014/docker-identity.json).

The earlier reports' ten interaction steps were not treated as clean qualification
after the diagnostic audit. Their failures remain part of the record.

## Retained fixture failures

Attempt 011 stopped before app startup because the fixture renamed the wheel to
an invalid installer filename. Attempt 012 genuinely installed and served inside
the container, but an internal-only Docker network produced no published host
port (`8033/tcp: []`). Adding the bridge did not create the missing mapping.
Its [failed browser report](../../../artifacts/process-interfaces/083/20261002-installed-docker-wheel-012/workspace-walkthrough/report.html)
remains intact. After confirming that configuration, only the exact owned
container was stopped and auto-removed. A fresh fixture 013 created the intended
loopback mapping on the bridge and passed both browser journeys. An observation
timeout alone never triggered restart or workflow replay.

Walkthrough validators pass for the failed report and both successful reports.
Current controlled presentation/start-association/API-authority regressions pass
52 tests in 43.13 seconds, with two existing dependency deprecation warnings.
These are separate from live engineering or human acceptance claims.

The owned native host remains on 8032; the corrected Docker proof host 014 remains on
8033 for subsequent acceptance checks. Both reviews remain unanswered. No
physical action, supplier operation, push, merge, release or public deployment
was performed.
