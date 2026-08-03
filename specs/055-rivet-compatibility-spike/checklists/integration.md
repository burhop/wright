# Integration Checklist: Rivet Compatibility Spike

**Purpose**: Confirm later slices receive concrete, scoped compatibility conclusions.

- [x] External Call is evaluated before proposing a Wright plugin.
- [x] The editor adapter seam covers IO, dataset, native API, plugin, and debugger configuration.
- [x] The runner seam covers immutable fixture input, host operation, events, cancellation, and debugger behavior.
- [x] Workspace Surface and process-supervisor boundaries are consumed, not replaced.
- [x] No production API, database schema, UI surface, package dependency, Docker change, or user feature is introduced.
- [x] Each finding has a disposition, evidence reference, required control, and next owning slice.
- [x] Go/conditional-go/no-go criteria explicitly constrain persistence, runner, and editor-adapter follow-on work.
- [x] A material incompatibility requires an umbrella-plan amendment before implementation continues.
