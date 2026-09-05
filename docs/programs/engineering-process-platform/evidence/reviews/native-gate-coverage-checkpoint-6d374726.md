# Native gate coverage follow-up

Recorded at: 2026-09-05T00:53:04.577193Z.

Candidate: `6d374726ad1602754bf7fcfdec1bfdd39937a866`.
The coordinator subsequently reported a coverage slice completing with **235
passed, 10 skipped, one resource warning, 85.28% coverage in 31.75 seconds**.
This is additional partial evidence after the earlier 17 affected tests passed.
The skips and warning remain explicit; neither observation establishes that the
entire required native push/merge gate has completed successfully. The original
eb63344c native compatibility assertion failure remains preserved in
[native gate and image checkpoint](native-gate-image-checkpoint-6d374726.md).

The Docker offline-startup correction `404269e9` is ready for separate independent
review and subsequent integration/build verification. No result for that new
code or a replacement image is claimed here. The previously observed image had
passed networked smoke but failed cold startup with networking disabled.

This observation records the coordinator's reported command result; the status
reviewer did not rerun or duplicate the active gate. Human study, native dev PR
integration, actual deployed journeys and final acceptance remain pending.
