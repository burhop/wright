# Handle final-review authoring correction

The actual compiled editor saved revision 4 and reopened it from the existing isolated Wright workspace. All seven review subjects remain connected. The new command changes a task’s declared type through the existing atomic semantic batch and history; it does not approve a review or change backend enforcement.

- Before: accepted revision 3; Source edit rejected as an unsupported structural change.
- After: revision 4, exact digest and resource hash in [receipt](receipt.json).
- 28 focused editor tests pass, including actual handle source conversion, subject/connection retention, cold reopen and Undo/Redo. TypeScript passes.
- [Reopened diagram](reopened-diagram.png) uses a restrictive simulated Linux desktop iframe and actual storage. Windows remains unverified.
- Original failed attempts remain in `.local-run/experience-review/candidate-035/handle-review-01/` and `handle-review-02/`; successful attempt `handle-review-03/`.
- No engineering run or human approval occurred. Tool and validation bindings remain required. Installed plugin remains unchanged; candidate 0.35’s previously frozen resource is not this new resource.
