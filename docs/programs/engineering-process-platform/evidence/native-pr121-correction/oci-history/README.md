# OCI correction history â€” public review projection

This is a selected historical projection, not a raw report or a completed full-gate result. Original files remain unchanged in private evidence storage. The machine projection links each phase to evidence IDs; the raw hash index contains only filenames, byte counts and SHA-256 values.

PR 121 H1 (`4480bf03`, workflow 33954211577/job 101274446563) failed its vulnerability-policy step. Its build and smoke succeeded. The full CI log proves that Hermes installed Tornado 6.5.6 at line 2222 and records `CVE-2026-82397:tornado` at line 3599. The built CI merge source was `055ca105`; it differs from the PR head. Upstream identifies versions through 6.5.7 as affected and 6.5.8 as fixed. The Docker pin was corrected accordingly. [Maintainer advisory](https://github.com/tornadoweb/tornado/security/advisories/GHSA-mpf4-983q-p7j4), [6.5.8 release notes](https://www.tornadoweb.org/en/stable/releases/v6.5.8.html).

The separate scan of retained old 40/image `2347e293` reproduced Tornado and found three OpenSSL package findings. Those OpenSSL findings belong to that older image, not H1.

| Record | Source / image | Observed result and limit |
| --- | --- | --- |
| First corrected build and smoke | `40b1d972` / `d134d432` | Both exited 0. Initial archive-description claim was later corrected: 3127 files had CRLF conversion; 346 were unchanged. |
| First shared scan | `d734f4c0` / `d134d432` | Zero reported fixable High/Critical findings; applies to the first exported context. |
| Separate corrected LF build and smoke | `40b1d972` / `336e4f0d` | Both exited 0; all 3473 archive file identities matched Git blobs. Both builds are retained; no publication occurred. |
| Historical LF-image scan | `fcb26a48` / `336e4f0d` | Zero reported findings under the unchanged policy; this is one stage, not full-gate acceptance. |
| Original helper review | `fa479118` / integrated `d734f4c0` | Three P2 findings: source-change cancellation, malformed finding acceptance and incomplete scan dispatch. |
| Corrected helper review | `8a2a5276` | All three independently closed. Original failing probes were retained and replayed; valid unfixed findings still follow existing policy. 108 writer tests passed. |
| Interrupted full gate | `fcb26a48` | Coordinator interrupted after the findings invalidated the candidate; tool exit 1. The original incomplete observation and interruption supplement are both preserved. |

The corrected validator also accepted the retained `d734` real Trivy report as a read-only compatibility control. This did not refresh its database, rerun a scan, or relabel it as the LF image. The standalone and interrupted-gate scans used the original helper before its review corrections; their actual clean-image observations remain distinct from the helper's broader correctness review.

The retained smoke checked installed dependencies/assets/permissions, standard entrypoint and cold offline API/Hermes readiness. Its printed historical backup/recovery instructions are not a new backup/restore proof. Platform scope is local Linux/amd64 Docker. No new browser, whole native lifecycle, multi-platform, human acceptance or published-dev deployment credit is added here.

Fresh candidate `28efd6cc`, frozen at `e15c0749`, had a full gate running when this bundle was requested. Its result is excluded. No aggregate pass, inferred timestamp, retry erasure or H2 CI success is claimed.

Import only the four files in this `public` directory. `bundle-manifest.json.txt` binds the other three files; the manifest's own hash is supplied separately at handoff. Private generation code, origin mappings, raw image environment/history, logs and scanner reports are excluded.
