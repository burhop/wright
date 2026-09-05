# Development registry identity requirement

Independent reviewer `/root/native_candidate_review`, 2026-09-05. **Development acceptance may retain distinct immutable GHCR and Docker Hub manifests if their image configuration and ordered uncompressed layer contents are independently shown equivalent. Production digest-equality acceptance remains unfulfilled.** This is an interpretation of the existing dev scope, not a waiver or a claim that equivalence has already been proved.

Applicable local evidence:

- `AGENTS.md` explicitly attaches identical registry digests to production integration and the production release runbook.
- `docs/release/release-runbook.md` identifies its scope as production; its protected order requires copying the same tested manifest and says digest divergence leaves the release incomplete.
- `docs/contributing/ci-cd-workflows.md` places byte-identical registry distribution in release-tag publication and its Release Publishing section. Its distinct engineering-image-family row describes dev branch publication with matching tags.
- `AUTH-EPP-N01-2026-002.md`, accepted scope items 1/2/6 and the completion paragraph, authorizes dev images and requires actual source/image identities, substantive checks and successful integrated journeys; it does not require equal registry manifest digests. Production remains excluded.
- The actual `.github/workflows/docker-image-family.yml` publishes the same local image separately to both registries and inspects both tags. It does not compare their manifest digests. N01 contracts/T031 require actual integrated-build verification, not production release acceptance.

Do not ignore the equality check in the previously reviewed private preparation/helpers. A narrowly reviewed **dev-only** alternative must retain both actual manifest digests, the exact successful source/workflow/job/attempt, and an explicit equivalence proof. Keep the deployed GHCR digest as the exact runtime subject; never substitute it for Docker Hub's different digest or claim byte-identical publication. Existing source, health, actual-browser and cleanup obligations remain.

Minimum sufficient evidence for each platform:

1. Fetch both manifests by immutable digest, verify raw SHA-256 and byte lengths, and retain actual media types, ordered descriptors and all differences. Fetch the config blob and verify its declared digest/size; require identical raw config bytes and the expected platform, `rootfs.type=layers`, and ordered DiffID population.
2. For every differing compressed layer pair, verify each downloaded compressed blob's SHA-256/length against its own descriptor. Stream decompression without extracting files, and require both uncompressed tar SHA-256 values to equal the corresponding config DiffID. Compare every remaining ordered descriptor exactly. A missing/failed/mismatching pair leaves equivalence pending.
3. Retain immutable-reference publication/source attribution and actual deployed-image inspection. Execute the approved integrated journeys against that selected immutable image. ARM publication/equivalence does not imply ARM local journey execution if only AMD is exercised.

This distinction follows the published formats: manifest descriptors identify distributed blob bytes and sizes; a DiffID identifies the uncompressed layer tar, while the configuration commits to the ordered DiffID list and runtime parameters. Equal config/rootfs commitments do not make two different manifest digests equal. [CNCF Distribution schema 2](https://distribution.github.io/distribution/spec/manifest-v2-2/), [OCI image configuration](https://github.com/opencontainers/image-spec/blob/main/config.md).

Current bounded ARM observation: actual retained platform manifests are `13ec37a3…` (GHCR) and `f6b83378…` (Docker Hub), both Docker schema 2, with the same config descriptor and 52 layers. Only base-layer descriptor 0 differs; the remaining 51 descriptors match. The formatted configs/diffID lists agree, but that metadata alone does not prove the downloaded compressed blobs decompress identically. The separate read-only layer/config proof is in progress. AMD proof remains separate; no actual payload equivalence, deployment, production acceptance, rebuild or registry mutation was performed by this review.
