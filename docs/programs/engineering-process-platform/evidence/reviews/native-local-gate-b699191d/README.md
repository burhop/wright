# Composed local verification and fixed native acceptance

Candidate `b699191d763b30fbdce130a46d571a87446b2cae` has composed scoped verification: unchanged completed stages from original `40ebc645ddb641503706dcb3a7d9c84a2b685359` (full script exit1) plus the complete corrected browser stage on `114fba07a1912a28c0251f1d24ece76c71447406` (exit0), observed at `2026-09-05T05:59:48.311128+00:00`. No new complete-script exit0 is claimed. The clean-source flag describes gate start; generated build outputs may differ and require separate derivation/artifact evidence. It does not claim an unchanged worktree throughout the gate or whole packaging acceptance. The accompanying allowlisted record binds the actual terminal log digest, browser outcomes, unchanged required test-source hashes and reviewed actual Docker/browser evidence. It contains no environment or reporter configuration.

Required case counts are per check and overlap: Q-SEMANTICS 65/65, Q-RUNTIME 204/204, Q-COMBINED 269/269, Q-DASHBOARD 124/124, Q-EDITOR 10/10. Raw default-gate skips and separately satisfied live cases remain distinct.

This restores scoped local acceptance only. Required push checks, terminal CI, final exact-candidate review, packaging consolidation, dev integration/verification and actual human study remain separate obligations. Prior failed attempts and original evidence remain unchanged.
