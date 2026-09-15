# Contracts and evidence

`mcp-modelica` keeps historical calls frozen and adds capabilities through explicit successor
contracts. A caller never has to infer a response generation from optional fields.

## Contract generations

| Frozen 1.0          | Recorded 2.0 successor       | Role                                                                 |
| ------------------- | ---------------------------- | -------------------------------------------------------------------- |
| `modelica_kit_list` | `modelica_kit_list_recorded` | Read qualified kits, scenarios, bounds, units, and produced metrics. |
| `modelica_simulate` | `modelica_simulate_recorded` | Execute one approved kit/scenario with bounded parameters.           |
| `modelica_run_list` | `modelica_run_list_recorded` | Read a deterministic bounded run index.                              |
| `modelica_run_get`  | `modelica_run_get_recorded`  | Reopen one immutable run ledger.                                     |

The frozen names return only envelope `1.0`. Their recorded successors return only envelope `2.0`.
Recorded results add required timestamps, separate native source/projection hashes, optional
compiler-schema identity, resolved parameters, richer artifacts, and declared observations.

Both simulation names persist the same canonical 2.0 ledger. The frozen projection recalculates its
own historical fingerprint, exposes `model.sha256` as the model-source hash and `scenario.sha256` as
the public-scenario projection hash, and returns only its seven historical artifact kinds. It never
reuses the richer recorded fingerprint or invents a native-scenario hash.

The frozen catalogue omits `produced_metrics[].required`; only the recorded catalogue declares
whether each metric is required or optional. A missing optional metric remains absent rather than
being manufactured.

## Resumable 2.1 flow

| Operation                                  | Responsibility                                                        |
| ------------------------------------------ | --------------------------------------------------------------------- |
| `modelica_simulation_manifest_get`         | Reopen the exact qualified inputs and return their manifest identity. |
| `modelica_simulation_request_template_get` | Prepare a complete reviewed submit payload without executing.         |
| `modelica_simulation_submit`               | Claim and execute one explicit manifest-bound request durably.        |
| `modelica_simulation_request_get`          | Read or reconcile request state without starting OpenModelica.        |
| `modelica_simulation_series_get`           | Summarize one sealed successful CSV with bounded samples.             |

The manifest covers source, native scenario, public projection, optional compiler schema, parameter
bindings/conversions, normalizer, lowering identity, and OMC/MSL engine. A template is valid only
for the exact manifest most recently issued by that server process. Submission still requires every
qualified parameter value, unit, and timeout explicitly.

The request id is caller-owned. Canonically identical request bytes under the same id resolve to the
same run or rejection; changed bytes are a collision. The server commits the claim before probing or
running OMC. A post-claim manifest mismatch becomes immutable `rejected / manifest_mismatch` and
does not start the solver.

Readback never reruns a disappeared owner. It can return a sealed run, reconcile a committed
`run.json`, report an active lock as `running`, retain an unstarted claim as retryable `pending`,
preserve a rejection, or return `recovery_required`.

## Generated selection schemas

Simulation and resumable selection schemas are generated from the loaded qualified kit registry.
Their closed `oneOf` branches enumerate only known model/version/scenario tuples. Parameter maps are
closed and include numeric type, reviewed bounds, exact unit, and `x-modelica-default` planning
metadata. That metadata never supplies a caller value.

## Stable business errors

Expected validation failures are MCP `isError: true` results whose text is canonical
`modelica-mcp-error/1.0` JSON. Every record contains `code`, `field`, bounded `context`, and
`recovery`; it contains no source text, path, or raw solver diagnostic. Unexpected execution faults
remain protocol errors.

`manifest.reissue_required` means the process-local manifest issuance is missing and directs the
caller to obtain a fresh manifest from that same process.

`runtime_incompatible` means the live OpenModelica/MSL probe does not match the exact shipped kit
policy. `compatibility-policy-unavailable` means the selected kit id/version has no server-owned
policy and is not implicitly qualified.

## Run identity

- Artifact `sha256` identifies exact bytes.
- Run `fingerprint` identifies the normalized execution contract: selected kit/scenario, resolved
  parameters, engine, and normalizer. It is an input identity and does not bind raw solver output.
- Recorded 2.0 separates native scenario bytes from the public scenario projection.
- Resumable 2.1 additionally seals engine, conversions, lowering, and normalizer identities in the
  manifest before submission.
- `evidence.json` may include optional `execution-attestation/1.0`. That binding records the input
  fingerprint or 2.1 request identity, engine, generated-script digest, terminal status, and SHA-256
  of the raw CSV and compiler stdout/stderr bytes captured before decode or trim. Raw CSV status is
  `captured`, `rejected`, or `absent`: it attests the runner capture, not the presence of persisted
  `result.csv`. A 2.1 normalization failure keeps the captured digest on the failed terminal record
  without inventing that artifact. Invalid UTF-8 is `rejected` with the raw digest. Historical
  evidence without the field stays readable; a present attestation is replayed strictly and a
  malformed or mismatched attestation fails closed. The recorded fingerprint remains an input
  identity and does not bind solver output.
- Neither a digest, a successful OMC exit, nor a completed run is a requirement verdict.

Completed replay treats the sealed OMC/MSL identity as historical evidence. It verifies the
manifest, copied source artifacts, regenerated `run.mos`, resolved parameters, normalized CSV,
evidence payload, and `run.json`; it does not compare against or probe the current image. An
unavailable or ambiguous normalizer implementation fails closed without rewriting the claim.

## Evidence resources

MCP `resources/list` and `resources/read` expose evidence, not another execution surface:

- `casys://modelica/kits/<model-id>/<version>/model.mo`
- `casys://modelica/kits/<model-id>/<version>/scenarios/<scenario-id>.json`
- `casys://modelica/kits/<model-id>/<version>/parameter-schema.json` when a kit declares one
- `casys://modelica/runs/<run-id>/<artifact>` for artifacts named by a sealed run ledger

Each read reopens server-owned bytes and checks media type, byte length, strict UTF-8 where
applicable, and SHA-256. No resource accepts a caller path, arbitrary URI, source, or script. A BOM,
invalid/noncanonical UTF-8, missing file, changed digest, malformed ledger, or ambiguous artifact
fails closed.

Run publication follows the atomic `run.json` commit. Resources for one run are registered as one
batch; a rejected middle entry publishes neither a partial list nor a list-change notification. The
store is monotone for a server process and exposes no delete/archive operation.

A legacy v1 ledger publishes only the artifacts actually attested by that ledger. It does not gain a
scenario-source or compiler-schema resource retroactively. Qualified kit resources remain
independently readable by their own identity.
