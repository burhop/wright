# ARM64 development-image payload equivalence

Independent reviewer `/root/native_candidate_review`, 2026-09-05 11:12:17Z. **Passed bounded byte verification** for the two retained ARM64 dev manifests associated with source `211c2598ca803c70d0bff0bb2c7ba9c468132b7b`. This supplements the separate dev-versus-production requirement analysis; it does not assert application/deployment acceptance.

Independently recomputed both raw manifest hashes, both exact 30,420-byte config hashes, compressed layer hashes/sizes and full decompressed tar hashes. GHCR manifest `13ec37a3…` and Docker Hub manifest `f6b83378…` remain different. Their config bytes are identical (`e37b681f77137c8a473ccc90c010f1cf39b5b3ef4d7cc2508f231ddea4918e21`), with Linux/ARM64 and 52 ordered layer DiffIDs. All fields outside the layer list and 51 ordered layer descriptors match.

The sole differing pair is base layer 0: GHCR compressed bytes 31,381,582 versus Hub 30,143,609. Both blobs verify against their own manifest descriptors and fully decompress to 102,983,680 tar bytes with SHA-256 `c01c35a040a25a51cd473910e3212a46d85fb700a6467c687f231d7edd47cbc1`, matching config DiffID 0. This proves that pair's difference is compression representation, with shared content commitments for the remaining layers.

No network fetch, tar extraction, rebuild, recompression, registry write or application execution occurred in this independent review. Config environment/history values were not displayed. AMD64 remains a separate proof. Production identical-manifest acceptance remains false; preserve both actual immutable registry identities.

Retained probe/results: `review-arm64-registry-payload-equivalence.py` and `arm64-registry-payload-independent-review.json` in this scratch directory. Raw producer files remain under `native-dev-publication-211c2598/arm64-registry-manifests/`.
