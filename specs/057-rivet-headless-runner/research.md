# Research

Slice 055 proved `@ironclad/rivet-node` executes a synthetic graph and receives abort, but its debugger accepts unauthenticated local WebSockets. Slice 056 supplies immutable revisioned files. Wright supervision and generation binding are mandatory.

## Decisions

1. **Use `ProcessSupervisor` rather than a new subprocess owner.** Its Windows
   Job Object and POSIX process-group adapters already bind process identity,
   generation, bounded logs, and descendant cleanup.
2. **Ship only an inert lifecycle fixture in this slice.** The package-cache
   limitation from slice 055 means a production `@ironclad/rivet-node` bundle
   cannot yet meet the offline requirement. The fixture proves the boundary
   while making no misleading production-execution claim.
3. **Treat the persisted workflow document as the launch snapshot.** The runner
   reads it once, records immutable workflow ID/revision/digest, and never
   gives a child process a writable workflow path or a tool token.
4. **Defer durable run/event indexes.** Slice 056 established only authored-file
   metadata. A migration for operational history belongs with slice 061
   workflow operations, when UI retention and provenance requirements are
   defined. This slice has a bounded in-memory projection and retained bounded
   process logs, sufficient for its lifecycle proof.
