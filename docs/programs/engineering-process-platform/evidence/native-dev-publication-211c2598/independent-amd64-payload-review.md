# AMD64 development-image payload equivalence

Independent reviewer `/root/native_candidate_review`, 2026-09-05 11:18:31Z. **Passed bounded byte verification** for the two retained AMD64 dev manifests associated with source `211c2598ca803c70d0bff0bb2c7ba9c468132b7b`. This is the separate AMD counterpart to the ARM proof, not application/deployment acceptance.

Both raw manifest hashes and exact 30,368-byte config hashes verify. GHCR manifest `c3a8500d…` and Docker Hub manifest `2365fc93…` remain different. Their identical config is `16a3933f2f7f0b7583739f002593f14d7416cb88a957dd26b211a9931ffd4310`, with Linux/AMD64 and 52 ordered layer DiffIDs. All non-layer manifest fields and 51 ordered descriptors match.

Independently hashed the sole differing compressed pair against its own descriptors (30,782,609 versus 29,780,765 bytes), then fully decompressed both. Each produces 81,049,600 tar bytes with SHA-256 `6f94328331290cbd81edab450664d42da7b64c191416c9346cd5d28c84f76035`, matching config DiffID 0. The pair differs in compression representation; remaining layers share exact content-addressed descriptors.

No network, tar extraction, rebuild, recompression, registry write or application execution occurred. Config environment/history was not displayed. Both registry identities must remain explicit; production identical-manifest acceptance remains false. The dev-only helper must enforce these proof boundaries before actual deployment acceptance.

Retained probe/results: `review-amd64-registry-payload-equivalence.py` and `amd64-registry-payload-independent-review.json`. The original ARM probe is unchanged; the AMD wrapper only substitutes platform and independently observed byte counts. Raw producer files remain under `native-dev-publication-211c2598/amd64-registry-manifests/`.
