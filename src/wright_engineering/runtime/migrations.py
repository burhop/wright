"""Native activation preflight around Wright's durable data-vault migrations."""

from __future__ import annotations

import hashlib
import json
import os
import sqlite3
import subprocess
from pathlib import Path
from typing import Any

from .installer import RuntimeInstaller
from .layout import NativeLayout
from .models import RuntimeStatus
from .state import ManifestStore


_PROGRAM_STATE_TABLES = (
    "catalog_snapshots",
    "catalog_state",
    "mcp_servers",
    "engineering_workspaces",
    "workspace_workflow_binding_sets",
    "workspace_workflow_run_manifests",
    "engineering_scenario_runs",
    "engineering_scenario_assertions",
    "model_catalog_snapshots",
    "model_content_objects",
    "model_installations",
    "model_capability_bindings",
    "model_references",
)


def _digest(value: object) -> str:
    encoded = json.dumps(
        value, sort_keys=True, separators=(",", ":"), ensure_ascii=True
    ).encode("utf-8")
    return f"sha256:{hashlib.sha256(encoded).hexdigest()}"


class MigrationPreflightError(RuntimeError):
    pass


class NativeMigrationManager:
    def __init__(self, layout: NativeLayout | None = None) -> None:
        self.layout = layout

    def _installed_call(self, action: str, data_root: Path, **arguments: Any) -> Any:
        """Use installed vault dependencies, retaining the same migration owner."""
        assert self.layout is not None
        if data_root.resolve() != self.layout.data.resolve():
            raise MigrationPreflightError("migration_data_root_mismatch")
        manifest = ManifestStore(self.layout).load(create=False)
        runtime_id = manifest.active_runtime_id
        if action == "prepare_activation":
            runtime_id = (
                manifest.current_operation.candidate_runtime_id
                if manifest.current_operation
                else None
            )
        elif action != "current_schema":
            raise MigrationPreflightError("migration_operation_invalid")
        runtime = manifest.runtimes.get(runtime_id or "")
        if runtime is None or runtime.status not in {
            RuntimeStatus.ACTIVE,
            RuntimeStatus.VERIFIED,
        }:
            raise MigrationPreflightError("migration_runtime_unavailable")
        environment = self.layout.require_contained(
            Path(runtime.environment_path), self.layout.runtimes
        )
        python = RuntimeInstaller.environment_python(environment)
        if not python.is_file():
            raise MigrationPreflightError("migration_runtime_unavailable")
        # Both methods exist in predecessor runtimes. An unconfigured manager in
        # the child executes locally, so this also avoids recursive delegation.
        program = (
            "import json, sys; from pathlib import Path; "
            "from wright_engineering.runtime.migrations import NativeMigrationManager; "
            "p=json.load(sys.stdin); p['data_root']=Path(p['data_root']); "
            f"print(json.dumps(NativeMigrationManager().{action}(**p)))"
        )
        try:
            completed = subprocess.run(
                [str(python), "-I", "-c", program],
                input=json.dumps({"data_root": str(data_root), **arguments}),
                capture_output=True,
                text=True,
                timeout=180,
                check=True,
            )
            return json.loads(completed.stdout)
        except (OSError, subprocess.SubprocessError, json.JSONDecodeError) as exc:
            # Do not copy database contents or child tracebacks into CLI evidence.
            raise MigrationPreflightError("installed_migration_failed") from exc

    @staticmethod
    def database_path(data_root: Path) -> Path:
        return data_root / "wright.db"

    def current_schema(self, data_root: Path) -> int:
        if self.layout is not None:
            version = self._installed_call("current_schema", data_root)
            if type(version) is not int or version < 0:
                raise MigrationPreflightError("installed_schema_invalid")
            return version
        from data_vault import database_status

        return database_status(self.database_path(data_root)).current_version

    def prepare_activation(
        self,
        *,
        data_root: Path,
        data_schema_min: int,
        data_schema_max: int,
        operation_id: str,
    ) -> str | None:
        if self.layout is not None:
            backup = self._installed_call(
                "prepare_activation",
                data_root,
                data_schema_min=data_schema_min,
                data_schema_max=data_schema_max,
                operation_id=operation_id,
            )
            if backup is not None:
                if not isinstance(backup, str):
                    raise MigrationPreflightError("installed_backup_invalid")
                self.layout.require_contained(Path(backup), self.layout.data)
            return backup
        from data_vault import upgrade_database
        from data_vault.migrations import require_schema_compatible

        database = self.database_path(data_root)
        receipt_dir = data_root / "migrations"
        receipt_path = receipt_dir / (
            "activation-"
            + hashlib.sha256(operation_id.encode("utf-8")).hexdigest()
            + ".json"
        )
        plan_digest = _digest(
            {
                "data_schema_min": data_schema_min,
                "data_schema_max": data_schema_max,
            }
        )
        if receipt_path.is_file():
            try:
                receipt = json.loads(receipt_path.read_text(encoding="utf-8"))
            except (OSError, json.JSONDecodeError) as exc:
                raise MigrationPreflightError("activation_receipt_invalid") from exc
            if receipt.get("plan_digest") != plan_digest:
                raise MigrationPreflightError("activation_operation_conflict")
            current = self.current_schema(data_root)
            if not data_schema_min <= current <= data_schema_max:
                raise MigrationPreflightError("activation_receipt_state_changed")
            backup_relative = receipt.get("backup_manifest")
            return (
                str((data_root / backup_relative).resolve())
                if isinstance(backup_relative, str)
                else None
            )
        before = self.current_schema(data_root)
        if before > data_schema_max:
            raise MigrationPreflightError("data_schema_newer_than_candidate")
        result = upgrade_database(database, backup_dir=data_root / "backups")
        require_schema_compatible(
            result.ending_version,
            minimum=data_schema_min,
            maximum=data_schema_max,
        )
        receipt_dir.mkdir(parents=True, exist_ok=True)
        backup_relative = None
        if result.backup_manifest:
            backup_relative = os.path.relpath(result.backup_manifest, data_root)
        temporary = receipt_path.with_suffix(".json.tmp")
        temporary.write_text(
            json.dumps(
                {
                    "schema_version": "1.0",
                    "plan_digest": plan_digest,
                    "ending_schema": result.ending_version,
                    "backup_manifest": backup_relative,
                    "state": "succeeded",
                },
                sort_keys=True,
                separators=(",", ":"),
            )
            + "\n",
            encoding="utf-8",
        )
        os.replace(temporary, receipt_path)
        return result.backup_manifest

    def capture_state_inventory(self, data_root: Path) -> dict[str, Any]:
        """Capture bounded public identities and counts without database rows."""

        database = self.database_path(data_root)
        data_schema = self.current_schema(data_root)
        counts: dict[str, int] = {}
        catalog: dict[str, Any] = {
            "channel": "bundled",
            "sequence": 0,
            "digest": _digest("catalog-unavailable"),
            "state": "unavailable",
        }
        connection = sqlite3.connect(f"file:{database.as_posix()}?mode=ro", uri=True)
        try:
            existing = {
                str(row[0])
                for row in connection.execute(
                    "SELECT name FROM sqlite_master WHERE type = 'table'"
                )
            }
            for table in _PROGRAM_STATE_TABLES:
                if table in existing:
                    counts[table] = int(
                        connection.execute(
                            f'SELECT COUNT(*) FROM "{table}"'
                        ).fetchone()[0]
                    )
            if {"catalog_state", "catalog_snapshots"} <= existing:
                active = connection.execute(
                    """SELECT snapshots.channel, snapshots.sequence,
                              snapshots.payload_sha256
                       FROM catalog_state AS state
                       JOIN catalog_snapshots AS snapshots
                         ON snapshots.snapshot_id = state.active_snapshot_id
                       WHERE state.state_id = 1"""
                ).fetchone()
                if active:
                    catalog = {
                        "channel": str(active[0])[:32],
                        "sequence": int(active[1]),
                        "digest": f"sha256:{active[2]}",
                        "state": "active",
                    }
        finally:
            connection.close()

        material = {
            "data_schema": data_schema,
            "catalog_snapshot": catalog,
            "counts": counts,
        }
        storage = []
        for root in (
            "data",
            "config",
            "workspaces",
            "models",
            "catalog",
            "reports",
            "manager",
        ):
            path = data_root if root == "data" else data_root / root
            storage.append(
                {
                    "root": root,
                    "persistence": "native-data-root",
                    "available": path.exists(),
                    "writable": path.exists() and os.access(path, os.W_OK),
                }
            )
        return {
            "schema_version": "1.0",
            "data_schema": data_schema,
            "catalog_snapshot": catalog,
            "counts": counts,
            "digests": {"program_material": _digest(material)},
            "storage": storage,
        }

    @staticmethod
    def compare_state_inventories(
        before: dict[str, Any], after: dict[str, Any]
    ) -> dict[str, Any]:
        """Explain state changes using stable categories, never raw rows."""

        before_counts = before.get("counts", {})
        after_counts = after.get("counts", {})
        keys = sorted(set(before_counts) | set(after_counts))
        count_changes = {
            key: {
                "before": int(before_counts.get(key, 0)),
                "after": int(after_counts.get(key, 0)),
                "disposition": (
                    "retained"
                    if before_counts.get(key, 0) == after_counts.get(key, 0)
                    else "migrated"
                    if after_counts.get(key, 0) >= before_counts.get(key, 0)
                    else "removed"
                ),
            }
            for key in keys
        }
        return {
            "schema_version": "1.0",
            "before_digest": before.get("digests", {}).get("program_material"),
            "after_digest": after.get("digests", {}).get("program_material"),
            "schema_transition": [before.get("data_schema"), after.get("data_schema")],
            "counts": count_changes,
        }
