# Runtime Checklist: Rivet Compatibility Spike

**Purpose**: Confirm the experiment can establish a reliable optional runtime baseline.

- [x] Candidate source, Node/package-manager versions, lockfile, package integrity, and build outputs are captured.
- [x] Reproducibility requires two clean runs with matching checksums.
- [x] Editor base path, static assets, Tauri/native assumptions, and browser persistence are traced.
- [x] Node execution, events, cancellation, and debugger behavior are observed through a fixture.
- [x] Browser/Hermes/native/Docker/offline status is reported as supported, unverified, or blocked.
- [x] Build/runtime external requests are observed under a denied network policy.
- [x] Performance observations are recorded without making unsupported product claims.
- [x] All experimental assets remain excluded from production/runtime packaging.
