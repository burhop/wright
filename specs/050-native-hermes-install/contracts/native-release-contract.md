# Native Agent-Manager Release Contract

## Build-once subjects

One reviewed source commit produces:

- the existing immutable Python wheel/source archive for
  `wright-engineering`, now containing plugin and runtime code plus UI;
- the runtime-extra dependency lock/evidence;
- the existing OCI candidate digest and supply-chain evidence;
- a compatibility contract shared by manager adapters, runtime, docs, and tests.

No stage rebuilds either Python or OCI subjects after candidate verification.

## Pull-request train

Mandatory checks include:

1. package content/base-import/runtime-extra contracts;
2. manager-adapter/lifecycle unit and integration tests;
3. candidate clean install on every claimed native platform using the real
   Hermes Git plugin interface plus a direct Codex profile contract probe;
4. previous-stable update and rollback tests using public predecessor artifacts,
   or two immutable candidates for the first native release;
5. uninstall/preserve/reinstall/purge tests;
6. provider-neutral MCP and frontend tests against the packaged runtime;
7. forbidden dependency and secret scans;
8. existing Python, Docker, security, docs, and release-policy checks.

Local immutable subjects prove the candidate without mutating public channels;
production support requires the published adapter identities.

## Production order

The unified release train orders native work as follows:

1. preflight and all ordinary CI;
2. build Python and OCI candidates exactly once;
3. exact-artifact package, UI, security, real Hermes Git-adapter,
   direct Codex profile, and Docker candidate gates;
4. TestPyPI publication and clean installation of the exact Python files;
5. protected PyPI promotion of those exact files;
6. immutable Hermes adapter tag activation plus every other claimed manager
   adapter publication for that version;
7. OCI promotion to GHCR and mandatory byte-identical Docker Hub mirror;
8. public Hermes Git install and shared Wright lifecycle verification using
   released Hermes and published Wright artifacts, plus direct MCP verification
   for every other claimed manager adapter;
9. post-publication Python, OCI, Docker, documentation, and evidence verification;
10. versioned documentation;
11. GitHub Release last.

Any failed or absent dependency blocks later completion. Stable-channel
activation is reversible until public native verification passes.

## Evidence requirements

Final release evidence extends the existing schema with:

- manager versions, adapter identities/protocols, and prerequisites;
- runtime product version and compatibility hash;
- PyPI filename/hash used by Hermes and by isolated runtime install;
- manager-process and Wright-runtime environment separation;
- claimed platform matrix and per-platform lifecycle results;
- phase-aware prerequisite/executable probe;
- previous stable version and retained-data/rollback results;
- uninstall and purge scope results;
- stable manager adapter identities and verification URLs;
- explicit Docker GHCR/Docker Hub evidence retained unchanged.

Missing native or Docker evidence is a schema/verification failure, not an
optional skip.

## Feature-branch safety

Feature and pull-request workflows use only local candidates, immutable local Git
subjects, or isolated test channels. They have no production publication
environments, credentials, or permissions. They MUST NOT publish to
PyPI/TestPyPI, GHCR, Docker Hub, GitHub Releases, production docs, or stable
manager channels.

## Recovery

- Failed Hermes adapter activation restores the prior Git ref; other managers
  use their documented package/marketplace rollback; evidence records both
  immutable identities.
- Bad Python files require a new patch; immutable files are never replaced.
- Bad native runtime restores a compatible predecessor where data permits, or
  follows backup recovery without discarding new work silently.
- Docker recovery remains the existing digest/alias process and is never replaced
  by native recovery.
- GitHub Release stays absent or draft until both distribution paths verify.
