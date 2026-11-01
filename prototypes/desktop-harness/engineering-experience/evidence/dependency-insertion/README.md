# Inserted steps stay near their inputs

The shared source editor now places added blocks after their known predecessors
without moving saved blocks. Multiple additions use dependency order rather than
source-section order. Collision checks reserve the inserted card's port-derived
height. This is presentation only: no execution dependency or authority changes.

Thirty-four focused authoring/command tests and TypeScript checking pass. The
actual compiled editor created a disposable copy, applied the handle refinement,
saved it and reopened it against isolated backend storage. Its new repair card is
to the right of its strength-check input. A separate read-only Find step check
shows the card completely inside the viewport at readable width.

- [Save/reopen and exact resource identity](report.json)
- [Measured node positions](placement.json)
- [Readable focus measurements](focus.json)
- [Overview](reopened-diagram.png)
- [Focused repair and inspector](focused-repair.png)

The goal's independent reviewer identified source-order placement and tall-card
collision risks; both were fixed and received explicit regression tests. The
focused recheck found no additional correctness concern. Card height remains an
estimate, not proof against every possible title/inspector combination.

This is Chromium in a simulated desktop host with actual isolated Wright storage.
Windows/native-tab rendering remains unverified. Existing workflow positions and
historical runs were preserved. No engineering process, model or provider ran.
The named installed plugin remains unchanged.
