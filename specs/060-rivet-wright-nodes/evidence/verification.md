# Verification

Focused bridge test passes. It proves a run cannot invoke the gateway through a
different workspace and that client approval hints are always false. Gateway
policy/approval and audit remain delegated to the existing service.

Rollback is removal of the bridge feature; it owns no data or credentials.
