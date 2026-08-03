# Test results

- `npm --prefix integrations/rivet/spike test`: 5 passed.
- `uv run pytest tests/contract/rivet_spike/test_spike_isolation.py -q`: 1 passed.
- Runner, cancellation, editor, offline-static, debugger, patch-policy, and supply-chain scripts were exercised.
- The offline editor build intentionally reports a blocked result because required Windows artifacts are absent from the committed Yarn cache.
