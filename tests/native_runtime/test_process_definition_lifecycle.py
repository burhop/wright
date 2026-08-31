from __future__ import annotations

import hashlib
import json
from importlib.resources import files
from pathlib import Path

from tool_registry.process_definition import (
    DEFINITION_FILENAME,
    PROCESS_ID,
    ProcessDefinitionReader,
    canonical_process_json_bytes,
)

from .support import artifact, lifecycle, seed_runtime


class _StableSchema:
    def current_schema(self, _data_root: Path) -> int:
        return 5

    def prepare_activation(self, **kwargs: object) -> str:
        data_root = Path(str(kwargs["data_root"]))
        return str(data_root / "backups" / "process-definition.manifest.json")


def test_installed_process_definition_survives_update_rollback_and_uninstall(
    tmp_path: Path,
) -> None:
    runtime = lifecycle(tmp_path, migration_manager=_StableSchema())
    seed_runtime(runtime, version="0.1.4", runtime_id="previous", running=True)
    installed_root = runtime.layout.data / "process-definitions"
    packaged_root = Path(
        str(files("wright_engineering").joinpath("static/process-definitions"))
    )
    reader = ProcessDefinitionReader(installed_root, packaged_root)

    packaged = reader.read(PROCESS_ID)
    assert packaged.source_kind == "packaged_fallback"
    assert not installed_root.exists()

    installed_root.mkdir(parents=True)
    installed_value = json.loads(
        (packaged_root / DEFINITION_FILENAME).read_text(encoding="utf-8")
    )
    installed_value["title"] = (
        "Installed product definition retained by the native data lifecycle"
    )
    digest_material = dict(installed_value)
    digest_material.pop("content_sha256")
    installed_value["content_sha256"] = hashlib.sha256(
        canonical_process_json_bytes(digest_material)
    ).hexdigest()
    installed_bytes = canonical_process_json_bytes(installed_value)
    installed_path = installed_root / DEFINITION_FILENAME
    installed_path.write_bytes(installed_bytes)

    initial = reader.read(PROCESS_ID)
    assert initial.source_kind == "installed"
    assert initial.source_sha256 == hashlib.sha256(installed_bytes).hexdigest()
    assert initial.source_sha256 != packaged.source_sha256

    assert runtime.update(artifact=artifact(tmp_path, "0.1.5")).ok
    after_update = reader.read(PROCESS_ID)
    assert after_update.canonical_bytes == initial.canonical_bytes
    assert after_update.source_sha256 == initial.source_sha256
    assert installed_path.read_bytes() == installed_bytes

    assert runtime.rollback().ok
    after_rollback = reader.read(PROCESS_ID)
    assert after_rollback.canonical_bytes == initial.canonical_bytes
    assert after_rollback.source_sha256 == initial.source_sha256
    assert installed_path.read_bytes() == installed_bytes

    assert runtime.uninstall().ok
    after_uninstall = reader.read(PROCESS_ID)
    assert after_uninstall.canonical_bytes == initial.canonical_bytes
    assert after_uninstall.source_sha256 == initial.source_sha256
    assert installed_path.read_bytes() == installed_bytes
