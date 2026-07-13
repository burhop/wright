# Data Model: Python and OCI Release Train

## ReleaseIdentity

- `product`: fixed `wright`
- `version`: normalized SemVer product version
- `python_version`: equivalent PEP 440 version
- `tag`: exact `v<version>` release tag
- `source_repository`: canonical repository identity
- `source_commit`: full reviewed commit SHA
- `created_at`: reproducible release timestamp input
- `prerelease`: derived boolean

Validation: every consumer must match; commit is full SHA; stable/prerelease classification is derived, not independently supplied. A version/source pair is immutable after candidate creation.

## PythonArtifact

- `filename`, `kind` (`wheel` or `sdist`), `size`, `sha256`
- `distribution`, `version`, `python_tag`, `platform_tag`
- `content_manifest_sha256`, `metadata_result`, `readme_result`
- `safe_paths`, `secret_scan_result`, `private_import_scan_result`
- `built_from_commit`

Relationship: exactly two primary artifacts belong to one `ReleaseIdentity`. TestPyPI/PyPI records reference these objects by SHA-256; they never embed rebuilt files.

## PythonInstallEvidence

- `artifact_sha256`, `python_version`, `os`, `installer_version`
- `source_isolated`, `commands`, `results`, `duration_seconds`
- `installed_files_sha256`, `uninstall_reinstall_result`

Validation: one passing record per artifact per admitted Python version. Source-tree paths must be absent.

## OciCandidate

- `repository`, `digest`, `platforms`
- `source_commit`, `product_version`, `created_at`
- `base_digests`, `tool_versions_and_checksums`, `dependency_lock_sha256`
- `labels`, `config_digest`, `manifest_media_type`

Validation: digest is immutable; initial platform list is exactly `linux/amd64`; labels match `ReleaseIdentity`.

## OciGateEvidence

- `candidate_digest`
- `smoke_result`, `inventory_sha256`, `license_result`
- `vulnerability_report_sha256`, `policy_result`
- `sbom_subject_digest`, `sbom_sha256`
- `provenance_subject_digest`, `attestation_verification_result`

Validation: all subjects equal the candidate digest; every required gate passes before promotion.

## VulnerabilityException

- `id`, `vulnerability_id`, `package`, `installed_version`
- `owner`, `rationale`, `compensating_control`
- `approved_by`, `approved_at`, `expires_at`
- `candidate_scope`

State: `proposed -> active -> expired/revoked`. Missing fields, past expiry, scope mismatch, or unreviewed status fail closed.

## PromotionRecord

- `source_digest_or_hash`
- `destination`, `reference`, `resolved_digest_or_hash`
- `environment`, `approval_identity`, `promoted_at`
- `operation` (`upload`, `manifest-copy`, `tag`, `verify`)
- `status`, `optional`

Validation: source equals resolved destination subject. Mirror records must match the canonical OCI manifest. Optional skips are explicit terminal records.

## ReleaseEvidenceManifest

- `schema_version`, `release_identity`
- `python_artifacts`, `python_install_evidence`
- `oci_candidate`, `oci_gate_evidence`
- `promotions`, `stage_results`, `approvals`, `skipped_optional_stages`
- `status`, `failure_reason`, `generated_at`, `manifest_sha256`

State transitions:

`preflight -> candidates_built -> candidates_verified -> test_index_verified -> approved -> promoted -> post_verified -> docs_verified -> release_ready`

Any stage can move to `failed` or `quarantined`. No transition may skip a required predecessor. Rehearsal terminates at `release_ready` with `mode=dry-run` and zero external mutations.

## RecoveryDecision

- `release_identity`, `incident_type`, `observed_subjects`
- `decision` (`resume`, `new_patch`, `yank`, `quarantine`, `restore_alias`, `hold_draft`)
- `target_subject`, `last_verified_subject`, `commands`, `approver`, `evidence_links`
- `dry_run`, `result`

Validation: immutable subjects are never overwritten; alias restoration targets a subject already marked verified; differing hashes require `new_patch`.
