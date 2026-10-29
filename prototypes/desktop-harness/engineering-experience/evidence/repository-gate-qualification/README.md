# Repository qualification in progress

The clean Git archive at `3327dcbf2eb8627e006a9e099a676cc016b64afb` built
ARM64 image `sha256:eab4c3a1520fefe6a494b89d3909cb98908ad6810e47f402c4b98d63667ebf3e`.
The existing pinned image scanner passed. The first full gate stopped because
no candidate image had been supplied; the second uses this immutable image.
Neither event establishes a complete repository gate or native acceptance.

The second gate's completed history scan identified four exact historical
credential-binding digests. Each original commit/line contains SHA-256 of `{}`.
The validation owner hashes a map of credential-status booleans, not credential
values; the empty map also matches its published EMPTY_BINDING_DIGEST constant.
The attached classification records the original fingerprints. `.gitleaksignore`
adds only those exact historical findings; evidence, history and scanner rules
are unchanged.

A disposable Git repository with the pinned Gitleaks 8.30.1 image verifies an
empty-map finding is detected initially, its exact fingerprint is excluded, and
a neighboring synthetic key remains detected. All 15 existing scanner setup /
public-alpha leak regressions pass. This does not claim the full history scan
passed: it exited 1 after scanning 1,709 commits with exactly these four
findings. The corrected full gate remains pending.

Private original logs and reproducer: `.local-run/experience-review/gates-20261029/`.
No installed plugin, live server, credential, engineering run or review changed.
