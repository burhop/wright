# Native Hermes Release Contract

## Build-once subjects

One reviewed source commit produces:

- the existing immutable Python wheel/source archive for
  `wright-engineering`, now containing plugin and runtime code plus UI;
- the runtime-extra dependency lock/evidence;
- the existing OCI candidate digest and supply-chain evidence;
- a compatibility contract shared by plugin, runtime, docs, and tests.

No stage rebuilds either Python or OCI subjects after candidate verification.

## Pull-request train

Mandatory checks include:

1. package content/base-import/runtime-extra contracts;
2. plugin/lifecycle unit and integration tests;
3. candidate clean install on every claimed native platform using the Hermes
   package-plugin fixture;
4. previous-stable update and rollback tests using public predecessor artifacts;
5. uninstall/preserve/reinstall/purge tests;
6. provider-neutral MCP and frontend tests against the packaged runtime;
7. forbidden dependency and secret scans;
8. existing Python, Docker, security, docs, and release-policy checks.

The fixture proves Wright behavior but does not prove released Hermes support.

## Production order

The unified release train orders native work as follows:

1. preflight and all ordinary CI;
2. build Python and OCI candidates exactly once;
3. exact-artifact package, UI, security, native fixture, and Docker candidate gates;
4. TestPyPI publication and clean installation of the exact Python files;
5. protected PyPI promotion of those exact files;
6. stable Hermes package-plugin channel activation for that immutable version;
7. OCI promotion to GHCR and mandatory byte-identical Docker Hub mirror;
8. public native install/start/update/rollback/uninstall verification using a
   released compatible Hermes and published Wright artifacts;
9. post-publication Python, OCI, Docker, documentation, and evidence verification;
10. versioned documentation;
11. GitHub Release last.

Any failed or absent dependency blocks later completion. Stable-channel
activation is reversible until public native verification passes.

## Evidence requirements

Final release evidence extends the existing schema with:

- Hermes version and package-plugin capability;
- plugin/runtime product version and compatibility hash;
- PyPI filename/hash used by Hermes and by isolated runtime install;
- base-environment and runtime-environment inventory separation;
- claimed platform matrix and per-platform lifecycle results;
- forbidden executable probe;
- previous stable version and retained-data/rollback results;
- uninstall and purge scope results;
- stable Hermes channel identity and verification URL;
- explicit Docker GHCR/Docker Hub evidence retained unchanged.

Missing native or Docker evidence is a schema/verification failure, not an
optional skip.

## Feature-branch safety

Feature and pull-request workflows use only local candidates or isolated test
channels. They have no production publication environments, credentials, or
permissions. They MUST NOT publish to PyPI/TestPyPI, GHCR, Docker Hub, GitHub
Releases, production docs, or the stable Hermes channel.

## Recovery

- Failed stable Hermes activation restores the prior channel pointer and records
  both immutable versions.
- Bad Python files require a new patch; immutable files are never replaced.
- Bad native runtime restores a compatible predecessor where data permits, or
  follows backup recovery without discarding new work silently.
- Docker recovery remains the existing digest/alias process and is never replaced
  by native recovery.
- GitHub Release stays absent or draft until both distribution paths verify.

