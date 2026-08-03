# Runner and debugger probes

The pinned Node packages executed a synthetic graph through `wright_mock_operation` and returned the expected string. An `AbortController` fired while a slow external operation was running and Rivet emitted an abort callback.

The built-in debugger accepted an unauthenticated local WebSocket connection. The production design must use a Wright-owned authenticated, one-run channel; direct debugger exposure is prohibited.
