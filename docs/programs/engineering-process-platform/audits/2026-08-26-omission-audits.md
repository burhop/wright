# Independent Omission Audits — 2026-08-26

## Method and independence

Four bounded subagents independently performed read-only audits of repository guidance and frozen prototype evidence for:

1. engineering usability;
2. architecture;
3. commercial/release readiness;
4. benchmark quality.

They were prohibited from editing files, refs, index, branches or worktrees and did not write this plan. The primary coordinator is the sole writer and synthesizer. Each audit used `dev` baseline `ad162cca048ad23d848673ec4f49f588dcc77aff` and prototype tip `e7bb75c1d97e70e55b943e0c94a31ff85cf9f82d`.

All four found no safely detectable uncommitted-only prototype evidence: the prototype had no registered worktree and local/remote refs matched. This does not attest to deleted/unregistered external directories. The committed evidence is adequate to preserve the cited plans, contracts, tests, screenshots and lessons; absent raw live-run artifacts cannot support new claims.

## Converged P0 findings and dispositions

| Concern | Independent sources | Program disposition |
|---|---|---|
| Empty-context authority and fail-closed catch-up | Engineering usability, architecture | `README.md`, schema inventory, exact next action and precedence rules. |
| Exact machine state/evidence, not checkboxes/prose | Engineering usability, architecture, benchmark | Program/roadmap/transition/approval/benchmark/dashboard schemas; append-only attempts and compare-and-swap state. |
| One branch allocation and singleton isolation | Architecture | `speckit-git-feature` runs once via `speckit-specify` pre-hook; one mutating lease/isolated worktree; pointer verification/restoration. |
| Unsafe auto-commit/bulk staging | Architecture | Optional commit hooks have no authority; `git add .` forbidden; allowlisted staging and diff/leak checks. |
| Stale approval/verification after subject change | All but benchmark explicitly; benchmark equivalent | Commit/tree/artifact-digest approvals and exact unchanged-tree independent verification; material change invalidation. |
| Product feature completeness | Engineering usability, commercial | Mandatory feature readiness envelope covers UX, failures, inspectable I/O, tests, accessibility, security, compatibility, benchmark, docs/support and rollback. |
| Fixture/live trust and layered failure | Engineering usability, architecture, benchmark | `PROD-03`/`PROD-04`, prototype dispositions LL-001/002/003/005/008/009/012/019. |
| Durable liveness, output and application identity | Engineering usability, architecture, commercial, benchmark | `PROD-05`/`PROD-06`/`PROD-07`, roadmap split, and explicit P0 decisions 003/004/005/006/008. |
| Prototype is evidence, not architecture | Engineering usability, architecture, commercial | Frozen read-only boundary, no merge/cherry-pick/promotion, all 25 lessons dispositioned, React Flow/JSON/CP7 unproven. |
| Four independent readiness areas | All four | Separate gates/dashboard; release is logical AND plus human approval; no aggregate compensation. |
| 100-process sampling/distinctness | Architecture, benchmark | Stable identity/equivalence family, exact primary quotas, cross intersections, partition policy and DEC-P0-010. |
| Holdout integrity for autonomous agents | Engineering usability, benchmark | 60/20/20 partitions, external human custody, contamination ledger and DEC-P0-009. |
| Oracle/artifact correctness | Architecture, commercial, benchmark | Independent versioned oracles, negative controls, units/tolerances, lineage/openability/lifetime/actions/cleanup, DEC-P0-007. |
| Attempts/thresholds/reproducibility/freshness | Benchmark, architecture | Append-only attempts, one qualified infrastructure retry, exact material/environment identities, proposed all-100 T0/T1 rule, DEC-P0-011. |
| Commercial posture/privacy/compatibility/external controls | Commercial, engineering usability | Independent COMM gates; DEC-P0-001/012; local-inert dashboard/support data; exact host/artifact compatibility; external settings evidence. |
| Wright integration/release order | Architecture, commercial | Dev-push/full-merge/deployment gates, production merge, build once, identical public subjects, native lifecycles, docs and GitHub Release last. |

## Audit-specific material findings retained

### Engineering usability

- Tests and screenshots did not complete the equivalent-baseline moderated comprehension gate; no superiority claim is accepted.
- At-scale views need focus/filter and cannot equate rendering 100 blocks with usable information design.
- Primary actions, progressive disclosure, explicit modes, recovery and actionable outputs are product contracts.
- Ports, connections, runtime values/artifacts and component interfaces must stay distinct; visual concepts remain hypotheses.

### Architecture

- The checkpoint evidence contract is a useful seed but lacked prior/new state revision, artifact digests, approval invalidation and verifier identity; the new transition schema adds them.
- `.specify/feature.json` and managed `AGENTS.md` are worktree-local singleton coordination, not program state.
- `speckit-analyze` is read-only and its report must be persisted/digest-bound; remediation routes deterministically to the earliest affected lifecycle state.
- Every durable/public change declares compatibility/migration/rollback before implementation.

### Commercial/release

- The current posture is public alpha with no bundled SLA; production-commercial claims require a human decision.
- No CP7 decision, security certification, durable compatibility or scaling evidence came from the prototype.
- Repository settings remain unchecked external evidence and are release blockers until verified.
- Merge, `main` checks and public release are three separate gates; exact-subject train is mandatory.

### Benchmark quality

- A 100-block render is not a 100-process benchmark.
- Blind assets/oracles cannot live where autonomous development agents can read them.
- First-attempt/eventual semantics, denominators, allowed retries, per-stratum/profile thresholds and evidence ages are frozen before execution.
- Every process requires a source/licensing/safety review, independent oracle, artifact lineage, negative controls, full qualification lifecycle and reproducibility identity.

## Contradictions resolved by the primary coordinator

1. **Must all P0 questions be decided before plan approval?** The audits require no P0 be hidden or silently assumed. This control plane makes twelve P0 decisions explicit, owned and blocking the earliest affected future gate. Program approval approves that governance, not an option. Benchmark implementation/release remains blocked where the audits required a concrete decision.
2. **Can the plan propose thresholds while the benchmark audit says humans must choose them?** The plan proposes all 100 current T0/T1 passes and stricter holdout/evidence completeness. `benchmark-coverage.json` labels the threshold policy pending `DEC-P0-011`; execution cannot begin until a human accepts or changes it on an exact subject.
3. **Use `speckit-git-feature` and `speckit-specify` separately?** No. The former is used exactly once through the latter's mandatory pre-hook, satisfying both skill contracts without double branch creation.
4. **May product and benchmark infrastructure proceed in parallel?** Only read-only planning may overlap. One mutating Spec Kit lease exists; `EPP-F01` validator/dashboard precedes product implementation, while benchmark harness waits on its P0 decisions and product evidence spine.
5. **Are prototype contracts reusable?** Their invariants and examples are evidence; production artifacts are rewritten/re-specified from `dev`, and no prototype code or schema is promoted by implication.

## Remaining material questions

All remaining P0 questions are enumerated in `decision-register.json` with owner, options, required evidence, due transition and blocking gates. They cover commercial posture, canonical representation/apply, application identity, hard tool isolation, deadlines, output lifecycle, oracle authority, UI/headless equivalence, blind holdout custody, target population/claims, release thresholds/profile mix, and third-party rights.

No other material P0 question is known. Final audit conformity status is machine-readable in [`audit-status.json`](audit-status.json); it must be updated only after each original auditor reviews the written control plane.

## Final conformity results

All four bounded read-only audit areas passed after reviewing the written control plane and targeted corrections:

- engineering usability: design conformant; exact state/transition/manifest consistency was the final condition, now represented by the accepted state history and approval candidate;
- architecture: PASS after canonical new-state evidence, stable genesis snapshot identity, approval subject, and honest state sequencing corrections;
- commercial/release: PASS after state/approval sequencing and full COMM-blocking decision propagation corrections;
- benchmark quality: PASS after oracle/holdout schemas and stricter lifecycle, required-output, artifact, mandatory-check, identity and ordered-stage enforcement.

Residual non-blocking advice is retained rather than hidden: the first read-only product feature must pre-register a measurable moderated-usability protocol (`PROD-02`/`EPP-F02`), and implementation features must validate semantic cross-file invariants that JSON Schema alone cannot compare (for example, equality of referenced required-output-set digests).
