# Feature Specification: Rivet Headless Runner

**Branch**: `057-rivet-headless-runner`
**Base**: `af7c54a`
**Prerequisite**: 056 workspace persistence

Implement an optional supervised Node runner for immutable workspace workflow revisions. It starts no editor, exposes no direct MCP/tool authority, and defaults unavailable when Node/Rivet is absent.

Requirements: bind every operation to server-derived workspace, revision, user/session, and runtime generation; snapshot persisted revision before launch; supervise process tree, resources, events, cancellation, and crash reconciliation; return typed absence states; keep graph operations mocked.

Success: fixture run streams bounded events and cancels within two seconds; no owned process/listener remains after crash or cancel; stale generation attempts fail; Node/Rivet absence leaves Wright healthy; offline package status is evidenced.

Excluded: editor, tab, direct MCP, approvals, Wright nodes, catalog, and agent publication.
