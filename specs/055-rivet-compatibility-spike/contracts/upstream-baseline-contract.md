# Contract: Upstream Baseline and Reproducible Build

**Owner slice**: `055-rivet-compatibility-spike`

## Purpose

Define the minimum evidence that makes a Rivet source/build candidate reviewable and reproducible. This is a development evidence contract, not a production dependency manifest.

## Baseline Record

Each candidate record MUST include:

- upstream repository HTTPS URL and immutable full commit hash;
- source archive digest and retrieval date;
- upstream release/tag metadata when applicable, treated as descriptive rather than immutable identity;
- exact Node and package-manager versions;
- lockfile digest and all resolved direct package versions/integrities;
- exact `@ironclad/rivet-core`, `@ironclad/rivet-node`, application, executor, and plugin resolutions consumed by the fixture;
- ordered isolated patch set with purpose, file list, patch digest, and clean-apply test;
- reproducible build command, normalized environment values, and generated asset manifest/checksum;
- direct/transitive license and security inventory, notices, package sizes, and known platform prerequisites;
- build, test, and offline evidence references.

## Candidate Rules

- The record must never use `main`, `latest`, floating ranges, an unpinned Git reference, or an unverified binary as the selected baseline.
- A patch may only target the selected source revision. A patch that applies to an unknown revision, globally monkey-patches host behavior, or exposes a production authority is rejected.
- Build inputs may be downloaded only during the documented acquisition phase. The supported runtime fixture must run using local declared inputs with outbound requests denied.
- Source artifacts and generated bundles must be clearly separated; generated binary/large assets are referenced by digest unless their inclusion is necessary for a later approved build fixture.

## Reproduction Result

Two clean runs are required. Each output includes baseline ID, environment, command digest, exit result, source/lock/asset digest, requested network authorities, elapsed time, and redacted log reference. Matching digests establish reproducibility; a mismatch blocks selection until explained.

## Promotion Boundary

No baseline record alone adds a package to Wright production. Later slices may adopt it only after their own approved plan repeats the required compatibility tests and adds ownership, licensing, packaging, migration, rollback, and support evidence.
