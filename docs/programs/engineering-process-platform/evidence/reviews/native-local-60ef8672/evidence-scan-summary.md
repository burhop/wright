# Native browser evidence secret-scan review

Reviewed parent source `9b42124a6c00a399b8e06972e6a46b54fe7457eb`, limited to `docs/programs/engineering-process-platform/evidence/reviews/native-local-60ef8672/`. The existing repository configuration has SHA-256 `a70e677c00bcb159615f7a83714845ec0514fef6bf635e3a0b5f15a0213b564d`.

Used the already-cached repository-pinned Gitleaks v8.30.1 image, immutable ID `sha256:c00b6bd0aeb3071cbcb79009cb16a60dd9e0a7c60e2be9ab65d25e6bc8abbb7f`, with `dir`, existing configuration, `--redact=100`, read-only evidence mounts, `--pull never`, and `--network none`. No history/full gate, network query, scanner exclusion, or policy change was performed.

The original directory scan exited 1 with five `generic-api-key` findings. All five are `snapshot.token` values, not readiness or authorization credentials. `native_process_repository.py:145` derives them by SHA-256 over the workspace identity and saved envelope; `native_process_runs.py:238` copies that value into the immutable snapshot. Workspace authorization remains separate in the service. No credential finding was identified in this bounded scan.

Exact original directory-scan fingerprints:

- `/repo/docs/programs/engineering-process-platform/evidence/reviews/native-local-60ef8672/actual-native-example-runs.json.txt:generic-api-key:188` — `/0/snapshot/token`.
- `/repo/docs/programs/engineering-process-platform/evidence/reviews/native-local-60ef8672/actual-native-example-runs.json.txt:generic-api-key:480` — `/1/snapshot/token`.
- `/repo/docs/programs/engineering-process-platform/evidence/reviews/native-local-60ef8672/actual-native-runs.json.txt:generic-api-key:233` — `/initial/snapshot/token`.
- `/repo/docs/programs/engineering-process-platform/evidence/reviews/native-local-60ef8672/actual-native-runs.json.txt:generic-api-key:613` — `/failed/snapshot/token`.
- `/repo/docs/programs/engineering-process-platform/evidence/reviews/native-local-60ef8672/actual-native-runs.json.txt:generic-api-key:959` — `/corrected/snapshot/token`.

The `projection/` directory contains two explicitly derived review copies, a transformation/hash manifest, and a note. Only the five quoted CAS values are replaced with explicit omission markers; all other source bytes are retained. The manifest identifies original native browser output paths, original hashes, exact pointers/replacements, projection hashes, and additional byte-identical originals retained under `raw-originals/` outside the parent worktree. Original browser proof files and original parent attachments were not changed by this review.

The final same-image/same-configuration offline scan of all four projection files exited 0 with an empty JSON report, scanning 56,094 bytes. Evidence: `gitleaks.log`, redacted `gitleaks.json`, `classified-fields.json`, `projection-final-gitleaks.log`, `projection-final-gitleaks.json`, and `projection/projection-manifest.json.txt`.

The parent owns publication-history preparation and rebinding evidence references. A later edit alone does not remove an earlier raw attachment from reachable history; this directory scan makes no history-scan claim. No product code or test outcome changed.
