"""Atomic lifecycle manifest persistence and bounded operation locking."""

from __future__ import annotations

import json
import os
import shutil
import time
from contextlib import contextmanager
from typing import Iterator

from .layout import NativeLayout
from .models import Manifest, utc_now


class StateError(RuntimeError):
    def __init__(self, code: str, message: str = "") -> None:
        self.code = code
        super().__init__(f"{code}: {message}" if message else code)


class LifecycleBusy(StateError):
    def __init__(self, operation_id: str | None) -> None:
        self.operation_id = operation_id
        super().__init__("lifecycle_busy", operation_id or "unknown operation")


class ManifestStore:
    def __init__(self, layout: NativeLayout) -> None:
        self.layout = layout
        self.manifest_path = layout.manifest
        self.snapshot_path = layout.state / "installation.previous.json"
        self.corrupt_dir = layout.state / "corrupt"
        self.quarantine_path = layout.state / "quarantine" / "newer-data.json"

    def load(self, *, create: bool = True) -> Manifest:
        if not self.manifest_path.exists():
            if not create:
                raise StateError("manifest_missing")
            return Manifest.create(self.layout.wright_home, self.layout.data)
        try:
            payload = json.loads(self.manifest_path.read_text(encoding="utf-8"))
            manifest = Manifest.from_dict(payload)
            manifest.validate()
            return manifest
        except (OSError, json.JSONDecodeError, ValueError, TypeError) as exc:
            self._preserve_corrupt_manifest()
            raise StateError("manifest_corrupt", str(exc)) from exc

    def save(self, manifest: Manifest) -> None:
        manifest.updated_at = utc_now()
        manifest.validate()
        self.layout.state.mkdir(parents=True, exist_ok=True)
        temporary = self.manifest_path.with_suffix(".json.tmp")
        encoded = (
            json.dumps(manifest.to_dict(), sort_keys=True, indent=2, ensure_ascii=False)
            + "\n"
        )
        try:
            if self.manifest_path.exists():
                shutil.copyfile(self.manifest_path, self.snapshot_path)
            with temporary.open("w", encoding="utf-8", newline="\n") as handle:
                handle.write(encoded)
                handle.flush()
                os.fsync(handle.fileno())
            os.replace(temporary, self.manifest_path)
        except OSError as exc:
            try:
                temporary.unlink(missing_ok=True)
            except OSError:
                pass
            raise StateError("manifest_write_failed", str(exc)) from exc

    def record_newer_state_quarantine(
        self,
        *,
        data_schema: int,
        candidate_runtime_id: str,
        supported_max: int,
    ) -> dict[str, object]:
        """Persist an explicit non-destructive rollback compatibility record."""

        record: dict[str, object] = {
            "schema_version": "1.0",
            "state": "quarantined-from-older-runtime",
            "reason": "DATA_SCHEMA_NEWER_THAN_CANDIDATE",
            "data_schema": data_schema,
            "candidate_runtime_id": candidate_runtime_id,
            "supported_max": supported_max,
            "recovery": "USE_COMPATIBLE_RUNTIME_OR_EXPLICIT_BACKUP_RECOVERY",
        }
        if self.quarantine_path.is_file():
            try:
                existing = json.loads(self.quarantine_path.read_text(encoding="utf-8"))
            except (OSError, json.JSONDecodeError):
                existing = None
            if existing == record:
                return record
        self.quarantine_path.parent.mkdir(parents=True, exist_ok=True)
        temporary = self.quarantine_path.with_suffix(".json.tmp")
        temporary.write_text(
            json.dumps(record, sort_keys=True, indent=2, ensure_ascii=True) + "\n",
            encoding="utf-8",
        )
        os.replace(temporary, self.quarantine_path)
        return record

    def load_newer_state_quarantine(self) -> dict[str, object] | None:
        if not self.quarantine_path.is_file():
            return None
        try:
            value = json.loads(self.quarantine_path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError) as exc:
            raise StateError("quarantine_record_corrupt") from exc
        if not isinstance(value, dict):
            raise StateError("quarantine_record_corrupt")
        return value

    @contextmanager
    def lock(
        self,
        *,
        operation_id: str,
        timeout: float = 5.0,
        poll_interval: float = 0.025,
        stale_after: float = 3600.0,
    ) -> Iterator[None]:
        self.layout.state.mkdir(parents=True, exist_ok=True)
        deadline = time.monotonic() + max(timeout, 0)
        payload = {
            "operation_id": operation_id,
            "pid": os.getpid(),
            "created_at": time.time(),
        }
        acquired = False
        while not acquired:
            try:
                descriptor = os.open(
                    self.layout.lock_file,
                    os.O_CREAT | os.O_EXCL | os.O_WRONLY,
                    0o600,
                )
                with os.fdopen(descriptor, "w", encoding="utf-8") as handle:
                    json.dump(payload, handle, sort_keys=True)
                    handle.flush()
                    os.fsync(handle.fileno())
                acquired = True
            except FileExistsError:
                holder = self._read_lock()
                if self._lock_is_stale(holder, stale_after):
                    try:
                        self.layout.lock_file.unlink()
                        continue
                    except OSError:
                        pass
                if time.monotonic() >= deadline:
                    holder_operation = holder.get("operation_id")
                    raise LifecycleBusy(
                        holder_operation if isinstance(holder_operation, str) else None
                    )
                time.sleep(poll_interval)
        try:
            yield
        finally:
            current = self._read_lock()
            if (
                current.get("operation_id") == operation_id
                and current.get("pid") == os.getpid()
            ):
                self.layout.lock_file.unlink(missing_ok=True)

    def _read_lock(self) -> dict[str, object]:
        try:
            value = json.loads(self.layout.lock_file.read_text(encoding="utf-8"))
            return value if isinstance(value, dict) else {}
        except (OSError, json.JSONDecodeError):
            return {}

    @staticmethod
    def _lock_is_stale(holder: dict[str, object], stale_after: float) -> bool:
        created_at = holder.get("created_at")
        pid = holder.get("pid")
        if not isinstance(created_at, (int, float)) or not isinstance(pid, int):
            return False
        if time.time() - float(created_at) < stale_after:
            return False
        if pid == os.getpid():
            return False
        try:
            os.kill(pid, 0)
        except OSError:
            return True
        return False

    def _preserve_corrupt_manifest(self) -> None:
        if not self.manifest_path.exists():
            return
        try:
            self.corrupt_dir.mkdir(parents=True, exist_ok=True)
            timestamp = utc_now().replace(":", "-")
            shutil.copyfile(
                self.manifest_path,
                self.corrupt_dir / f"installation-{timestamp}.json",
            )
        except OSError:
            pass
