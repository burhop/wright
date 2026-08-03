# Data Model

- `EditorAssetManifest`: Rivet version, entry point, digest, licenses,
compatibility state.
- `EditorBootstrapGrant`: opaque ID, workspace/session/workflow/revision,
expiration and revocation state; never stored in project files/browser storage.
- `EditorBootstrap`: availability, grant ID and selected workflow metadata only.
- `AdapterResult`: success, conflict, forbidden, expired, disabled, missing, or
incompatible.
