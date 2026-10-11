# Proposed handling of delivery scanner findings

Approved by the user on 11 October 2026 as part of the explicitly proposed
development checkpoint exception. The exact allowances are now implemented;
the earlier rejection and proposal below are retained as history.

The feature-history scan reported 47 generic-api-key matches in retained evidence. Independent inspection classified them as 31 file-integrity hashes, four stored-file UUID filenames, and 12 public idempotency identifiers. Historical file hashes were recomputed from Git blobs with their recorded LF/CRLF or packaged-path form. Storage filenames use FileVault UUID-plus-extension generation; idempotency keys are typed validation request identifiers.

Proposed change: allow only the exact generic-api-key match, field/value and evidence file for these findings. Keep all other fields and paths scanned. Add positive checks and negative checks for a neighboring synthetic API key, a changed value, and the same value at an unapproved path. Preserve evidence files and branch history.

Automatic approval review originally rejected modifying the scanner configuration
because that security configuration change was beyond the existing delivery
authorization. The subsequent explicit user approval resolves that authorization
requirement; it does not authorize broader exclusions.

The scanner-backed contract now allows all 47 approved entries across 32 exact
paths and detects 124 negative controls: neighboring synthetic API keys, changed
values and the approved values at unapproved paths. Eight scanner-configuration
tests pass. The exact-value fixture retains original observed commits and
classifications. Full history scanning remains a separate publication check.

No credential values are included here. The raw scanner report is redacted and remains local.

## Affected files and fields

- `artifacts/process-interfaces/083/20261001-authoring-foundation/checked-scope.json`: `public-api.md`
- `artifacts/process-interfaces/083/20261001-engineering-readers/checked-scope.json`: `public-api.md`, `test_process_artifact_access.py`
- `artifacts/process-interfaces/083/20261003-authoring-resource-primary-audit-verified/checked-scope.json`: `test_process_artifact_access.py`, `test_process_interfaces_api.py`
- `artifacts/process-interfaces/083/20261003-authoring-resource-primary-audit-verified/primary-review.json`: `public-api.md`, `tokens.css`
- `artifacts/process-interfaces/083/20261003-authority-primary-audit-verified/boundaries/command.json`: `test_process_artifact_access.py`
- `artifacts/process-interfaces/083/20261003-authority-primary-audit-verified/checked-scope.json`: `test_process_artifact_access.py`
- `artifacts/process-interfaces/083/20261003-current-docker-primary-audit-008-verified/checked-scope.json`: `test_process_artifact_access.py`, `test_process_interfaces_api.py`
- `artifacts/process-interfaces/083/20261003-current-regression-verified/backend/selection.json`: `test_process_artifact_access.py`, `test_process_definition_api.py`, `test_process_interfaces_api.py`
- `artifacts/process-interfaces/083/20261003-current-regression-verified/packaging/selection.json`: `test_process_artifact_access.py`, `test_process_definition_api.py`, `test_process_interfaces_api.py`
- `artifacts/process-interfaces/083/20261003-installed-revision-compatibility-verified/checked-scope.json`: `test_process_artifact_access.py`, `test_process_interfaces_api.py`
- `artifacts/process-interfaces/083/20261003-lifecycle-primary-audit-verified/checked-scope.json`: `test_workflow_approval_resume_api.py`
- `artifacts/process-interfaces/083/20261003-lifecycle-primary-audit-verified/command.json`: `test_workflow_approval_resume_api.py`
- `artifacts/process-interfaces/083/20261003-multihour-operation-budget-verified/checked-scope.json`: `test_workflow_approval_resume_api.py`
- `artifacts/process-interfaces/083/20261003-multihour-operation-budget-verified/regression/command.json`: `test_workflow_approval_resume_api.py`
- `artifacts/process-interfaces/083/20261003-negative-ui-primary-audit-verified/checked-scope.json`: `test_process_artifact_access.py`, `test_process_interfaces_api.py`
- `artifacts/process-interfaces/083/20261003-negative-ui-primary-audit-verified/regression/command.json`: `test_process_artifact_access.py`, `test_process_interfaces_api.py`
- `artifacts/process-interfaces/083/20261003-shared-ui-primary-audit-verified/checked-scope.json`: `test_process_artifact_access.py`, `tokens.css`
- `artifacts/process-interfaces/083/20261003-ui-revision-compatibility-verified/checked-scope.json`: `test_process_artifact_access.py`, `test_process_interfaces_api.py`
- `artifacts/process-interfaces/083/20261004-original-input-and-common-run-verified/actual-authoring/workspace/.wright/process-uis/ui-f47e26fbcc2e44a2a7c4dc939aef1948/revisions/revision-b1d66dc13ace45889297568cd38c6ee0/inventory.json`: `storage_key`
- `artifacts/process-interfaces/083/20261004-original-input-and-common-run-verified/actual-authoring/workspace/.wright/process-uis/ui-f47e26fbcc2e44a2a7c4dc939aef1948/revisions/revision-fd3eb8640fb4409d8e04a62a2408f503/inventory.json`: `storage_key`
- `artifacts/process-validation/serial-p001-canonical018-review/water-heater-sizing-01/report.json`: `idempotency_key`
- `artifacts/process-validation/serial-p001-canonical018-review/water-heater-sizing-02/report.json`: `idempotency_key`
- `artifacts/process-validation/serial-p001-canonical018-review/water-heater-sizing-03/report.json`: `idempotency_key`
- `artifacts/process-validation/serial-p001-canonical019-review/water-heater-sizing-01/report.json`: `idempotency_key`
- `artifacts/process-validation/serial-p001-canonical019-review/water-heater-sizing-02/report.json`: `idempotency_key`
- `artifacts/process-validation/serial-p001-canonical019-review/water-heater-sizing-03/report.json`: `idempotency_key`
- `artifacts/process-validation/serial-p001-native-successor/water-heater-sizing-01/report.json`: `idempotency_key`
- `artifacts/process-validation/serial-p001-native-successor/water-heater-sizing-02/report.json`: `idempotency_key`
- `artifacts/process-validation/serial-p001-native-successor/water-heater-sizing-03/report.json`: `idempotency_key`
- `artifacts/process-validation/serial-p001-reader-accounting/water-heater-sizing-01/report.json`: `idempotency_key`
- `artifacts/process-validation/serial-p001-reader-accounting/water-heater-sizing-02/report.json`: `idempotency_key`
- `artifacts/process-validation/serial-p001-reader-accounting/water-heater-sizing-03/report.json`: `idempotency_key`
