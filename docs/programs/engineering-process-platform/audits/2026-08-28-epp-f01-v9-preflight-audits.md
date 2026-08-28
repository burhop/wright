# EPP-F01 V9 Preflight Independent Audits

**Date:** 2026-08-28

**Mode:** bounded read-only audits; one primary writer applied dispositions

**Subject before freeze:** source checkpoint `9f30322859e8039863b47cdcb0e4c8f29354c9dc`; working-tree V9 planning delta
**Result:** PASS after bounded planning dispositions; no implementation result claimed

## Scope

The reviewers inspected only the two-claim `COR-EPP-F01-V9-PREFLIGHT-EVIDENCE-001` plan: exact external-schema binding for the immutable V8 discovery blob and exact TR-0051 complete-set/self-path-order disposition. They also checked the no-lease approval gate, T077–T080, preserved exclusions, and non-interference. No reviewer edited files.

## Independent results and dispositions

| Lens / reviewer | Initial result | Material findings | Sole-writer disposition | Final |
|---|---|---|---|---|
| Engineering usability / Aquinas | fail pending repair | V8-only `analysis.md` and audit status; insufficiently explicit T077 near misses; T079 baseline and T080 artifact/identity absent; local T073 stash not durably identified | Replaced analysis; expanded T077; bound T079 to APR-009/TR-0053; specified schema-valid `EPP-F01-V9.json` and independent verifier; recorded stash `bf05abcc...`, base, one-file/286-line inventory, non-authority and fresh-clone rule | PASS |
| Architecture / Avicenna | pass with freeze blocker | TR-0053 and this audit artifact had to exist before state/subject freeze | Added both artifacts last, with byte-identical current/archive state and regenerated output manifest/digests | PASS |
| Commercial/release / Parfit | fail pending repair | same missing analysis/audit/transition; ambiguity between planning action-rule update and correction-off/on lifecycle-policy non-interference | Replaced analysis; added audit/transition; specified that planning selects V9 action and T079 preserves frozen V9 policy bytes and roadmap-policy result | PASS |
| Benchmark quality / bounded V9 benchmark auditor | pass with corrections | task test mandate ended at SC-014; T079 omitted full benchmark projection vocabulary and synthetic non-authority | Extended mandate through SC-015; enumerated populations/counts, coverage, qualification, attempts, holdout, tiers, oracle/artifact, freshness, trend inputs and zero-authority synthetic fixture | PASS |

## Independently recomputed evidence

- Source checkpoint: commit `9f30322859e8039863b47cdcb0e4c8f29354c9dc`, tree `ec7b6aec43461cd3fbdbfc6c6c8ce366fdca2b03`, program tree `e244e592d57badfcddef08d0cfaa2265f18c069c`.
- Both targets' strict ancestor: commit `c12eb00308cb72d96977846c4ae876dc0baa7e7e`, tree `7323b292d279fde752004bc744a2db850ab670d0`, program tree `18e3d4ad3f33e244b1f9145b55b27f4e02d4b54b`.
- Discovery: blob `83beafb5fce4decb927f1ff549634ba664dd3a60`, raw SHA-256 `b6def7c089398b083bf9be118b9d428ac0179c001f2b048df0808c335bb9e6f5`.
- Exact external schema: blob `c6662ccec460b8a89b9d52f810b90fdc3aa55b23`, raw SHA-256 `33699e5ef2748b422d013679405f45d6df50ca98d418d9be4cf06b2f44301205`; planning/promoted bytes equal and `const` equals the discovery object.
- TR-0051: blob `cd9d7787325e251b8a365280e208eab567a0b662`, raw SHA-256 `27276a83671ca3a82e4981b1da5d0f176a1465ebf397d8d2fc45447fc2438c2a`; 35 unique paths equal the container set; recorded digest `cd195838...`, sorted/container digest `607dec372...`; self index 34 versus 9; no missing, extra or duplicate path.

## Preserved independent gates and exclusions

Product `not_started`, benchmark `not_started`, commercial `blocked`, and program health `blocked` remain independent. Benchmark remains honest `0/100`; dashboard bytes remain `candidate_not_evidence`; release eligibility remains false. V9 adds no browser page or graph. T073–T076, the roadmap-policy repair, T066–T068, EPP-F01B, dependencies, benchmark generation/execution, external change, push/PR/merge/dev integration, publication, and release remain unauthorized.

The only material question left visible is the separately excluded roadmap-policy test inversion. It is not a V9 finding and blocks later T066/V8 resumption until separate human disposition. No V9 audit waives it.
