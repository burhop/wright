# Runtime corrections and full local tool process

Production checkpoint: `0f40f414e6daf5d4a2c2b63e891a73ce5e6c03de`.

Independent correction review closed all four runtime findings at `cfb00d3824249d3b1ee6c4a005f5fec601f5e54e`. The reviewer reran the original four probes unchanged, nine bounded runtime JSON tests and the snapshot/replay test: 14 passed. Parent correction validation ran 33 focused tests successfully. Definitions retain their strict canonical identity profile; runtime data preserves literal Unicode and finite fractional tool arguments. Artifact text limits count decoded characters. An abandonment event closes the late-promotion cleanup race; removal failures retain a bounded cleanup diagnostic.

MCP corrections at `9d8c518c531b163a1b14d3dc8dd42a13697d42a8` passed independent closure with nine checks. Native telemetry correction `1441484759705246d587469fa632d8f592a34f77` and execution/MCP coverage extension `0f40f414` passed independent exporter/API/MCP exception-chain and cancellation checks. Legacy tracing defaults remain unchanged.

The opt-in protocol test now exercises two paths: the adapter boundary and a complete native process. Both passed on the actual Windows host using the existing Python 3.13.5 interpreter. The complete process submits literal `{"value":0.5}` to the real disposable local stdio measurement server, uses its fixture multiplier of 2.5, writes actual `{"value":1.25}` bytes to `measurement.json`, reads those bytes back, and verifies producing run/definition provenance and digest. The fixture input file remains unchanged and the child process exits during scoped teardown.

[Captured full-process protocol, run, steps, artifact and audit evidence](native-process-mcp-protocol.json) is distinct from mocked adapter tests. It is a disposable integration fixture, not engineering catalog qualification or benchmark credit. The exact test command was `WRIGHT_NATIVE_MCP_PROTOCOL=1 python -m pytest packages/workspace_service/tests/test_native_process_mcp_protocol.py -q` with all package paths pointing at the isolated implementation worktree. Result: 2 passed, 0 skipped. The test extension was uncommitted while this observation was taken; production code was exactly the checkpoint above.

Browser execution through the combined HTTP API, actual process-death recovery, packaging, human usability and dev integration still need their own evidence.
