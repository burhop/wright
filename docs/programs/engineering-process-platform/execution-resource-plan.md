# Execution Resource Plan: Windows and Dell GB10

This plan improves throughput without changing scope or weakening gates. It becomes operational only after the comparison below is recorded on one exact commit.

## Baseline benchmark

Use separate clean worktrees at the same immutable commit. Capture CPU, RAM, free disk, filesystem, Docker version/storage driver, Python/Node versions, workers, peak memory, wall/CPU time, disk I/O, exit code, test totals, and output digests. Use one warm-up plus three measured runs for:

1. focused parallel backend tests;
2. program validators;
3. Docker application-image build with equal cache state;
4. Python/native packaging and artifact verification; and
5. an independent read-only candidate verification bundle.

Do not run duplicate measured suites concurrently. Keep UI/Playwright, Windows-native lifecycle, Microsoft integrations, and final local integration on Windows.

## Adoption gates

Move a workload to GB10 only when its three-run median is at least 20% faster or Windows cannot finish within the declared memory limit, results are semantically identical, required digests match, and a second commit confirms the result. Otherwise retain Windows. Rebenchmark after material hardware, Docker, dependency, or gate changes.

## Ownership and provenance

- At most one integration lane and one feature lane; each branch/worktree has one writer.
- Hosts never write the same worktree or run the same suite concurrently.
- Transfer via exact Git commit or read-only bundle containing commit, tree, command, host facts, timestamps, tool versions, and SHA-256 manifest.
- GB10 verification consumes an immutable candidate and returns evidence only; fixes occur in the owning worktree as a new commit.
- Final Windows integration verifies commit/tree and manifest before gates.

## Initial routing after adoption

- **GB10 candidates**: memory-heavy/parallel backend tests, validators, Docker builds, packaging, independent Linux verification.
- **Windows authoritative**: React/Playwright, Windows-native lifecycle, Microsoft/CAD integrations, Windows packaging checks, final local integration.
- **Either**: small focused deterministic checks, choosing the idle host only with explicit ownership/provenance.

Start with validators and one backend slice. Expand one workload at a time. Roll back routing on divergent results, provenance gaps, shared writes, flaky transfer, or a slower two-commit median.
