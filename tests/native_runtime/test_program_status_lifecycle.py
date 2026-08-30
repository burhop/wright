from __future__ import annotations

from pathlib import Path

from .support import artifact, lifecycle, seed_runtime


class _StableSchema:
    def current_schema(self, _data_root: Path) -> int:
        return 5

    def prepare_activation(self, **kwargs: object) -> str:
        data_root = Path(str(kwargs["data_root"]))
        return str(data_root / "backups" / "program-status.manifest.json")


def test_program_status_data_survives_update_rollback_and_uninstall(
    tmp_path: Path,
) -> None:
    runtime = lifecycle(tmp_path, migration_manager=_StableSchema())
    seed_runtime(runtime, version="0.1.4", runtime_id="previous", running=True)
    installed = runtime.layout.data / "program-status" / "current.json"
    installed.parent.mkdir(parents=True)
    expected = b'{"bundle_id":"retained-program-status"}\n'
    installed.write_bytes(expected)

    assert runtime.update(artifact=artifact(tmp_path, "0.1.5")).ok
    assert installed.read_bytes() == expected

    assert runtime.rollback().ok
    assert installed.read_bytes() == expected

    assert runtime.uninstall().ok
    assert installed.read_bytes() == expected
