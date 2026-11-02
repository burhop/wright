# Iteration Integrity

- Repeated lifecycle visits generate attempt 1, attempt 2, and later occurrence
  identities while retaining one recognizable graph node.
- Canonical task references produce explicit connection traversal records for
  each ordered source/target attempt; connection selection links to the exact
  target attempt. Rivet reports traversal evidence unavailable when its runtime
  did not emit an equivalent fact.
- Superseded canonical revision attempts remain ordered before the accepted
  attempt and are labeled `superseded`.
- Immutable artifact-version records reject changed bytes under an existing
  identity. Export disambiguates repeated filenames and checks supplied SHA-256
  digests before packaging.
- Executed graph snapshots are captured at run start, so later editor changes do
  not replace the retained definition. Historical records without a snapshot
  explicitly report that gap instead of projecting the current graph.
