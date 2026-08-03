# Rollback and preservation evidence

The feature gate defaults off and imports no Rivet or Node dependency. Disabling it hides the new API while leaving ordinary workspace files unchanged. Delete moves the workflow directory, including dataset sidecars, to `workflows/.deleted/<workflow-id>-<revision>/`; recovery uses an atomic move back into a new safe slug. SQLite holds a rebuildable metadata projection only and may be recreated by scanning workspace files.

Platform limitation: the staged-write implementation calls file `fsync` and same-directory `os.replace`; directory `fsync` is not currently available in the Windows test environment and needs native/Docker hardening coverage before a cross-platform durability claim.
