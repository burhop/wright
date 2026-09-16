# Engineering process-validation evidence

The retained qualifying run is [`20260916T213859Z`](20260916T213859Z/). It
contains two isolated canonical processes:

- a real AI/MCP jig producer that first created an out-of-tolerance STEP file,
  received typed measured feedback, created a distinct corrected STEP revision,
  passed fresh geometry validation, and released its consumer;
- an MCP-staged heat-output process that read five retained campaign artifacts
  without modifying them, produced 15 independent measurements, passed the
  frozen numerical profile, and released its consumer.

`manifest.json` records the byte count and SHA-256 digest of every retained
file. `tests/external/process_validation/test_engineering_process_evidence.py`
checks the manifest, process lineage, measurements, correction packet, output
identities, actual tool arguments, retained-input hashes, and final release
states.

Any other locally generated timestamped directories are diagnostic runs and
are not qualifying evidence unless separately retained and verified.
