# Manual Editor Surface Contract

`POST /api/workspace/workflows/editor/surface` accepts only a session identifier and returns the verified, server-provisioned `wright.rivet-editor` manifest. It returns unavailable when the feature is disabled or the artifact is missing, invalid, or conflicting. The manifest has isolated sharing, empty capabilities, a loopback-only command, and an explicit manual-import/export description. The caller must not provide process or path values.
