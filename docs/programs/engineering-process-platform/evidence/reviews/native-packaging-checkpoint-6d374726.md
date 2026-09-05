# Native packaging checkpoint

Source input: `6d374726ad1602754bf7fcfdec1bfdd39937a866` on Windows x86_64, Python 3.13.5 and Node 25.2.0. These are local development artifacts; nothing was published.

`npm run build --workspace=apps/web` passed (858 modules; Vite build 7.29 seconds). The existing Vite configuration and large-chunk warnings remain. The native packaging command reused this fresh frontend through `WRIGHT_NATIVE_SKIP_FRONTEND_BUILD=1` and ran `scripts/build-python-distributions.sh --dist-root dist/dev-merge-python .`.

Both native artifacts passed content/hash validation and separate clean-environment installs/imports:

- Wheel: `wright_engineering-0.1.9-py3-none-any.whl`, 16,185,905 bytes, SHA-256 `0c2cd56eca16db9b5989e58fe6a9d90b925a4fb531c42c05a58f33268804fa9c`.
- Source distribution: `wright_engineering-0.1.9.tar.gz`, 15,788,044 bytes, SHA-256 `415c1405d4e2d96a848683a59fb6312d1780cfe6a71f98e5223ec75b3429fece`.

The source-distribution installation rebuilt a byte-identical wheel. The generated packaged frontend and runtime-extra-lock metadata are build outputs, subsequently retained in the implementation branch. Their presence is not evidence of a full gate pass.

This check does not claim offline installation, a different-version upgrade, Docker startup acceptance, other-platform execution, human acceptance or dev integration. The clean installs used the configured package cache/index. Separate earlier native installed-runtime and Docker diagnostic records retain their own limits.
