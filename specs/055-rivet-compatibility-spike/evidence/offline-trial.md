# Offline trial

The synthetic Node fixture and static asset authority scan did not use outbound network endpoints. The pinned source build was executed with `YARN_ENABLE_NETWORK=0` and stopped during Yarn fetch because multiple required Windows platform artifacts were missing from Rivet's committed cache. This is a build-supply-chain blocker, not evidence that a browser embedding is offline-safe.
