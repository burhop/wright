"""Native regression inputs preserve their original captured byte identities."""

import hashlib
import json
from pathlib import Path


def test_retained_native_regression_files_match_their_manifest():
    root = Path(__file__).parent / "fixtures/retained-process-validation"
    manifest = json.loads((root / "manifest.json").read_bytes())
    rows = {row["path"]: row for row in manifest["files"]}
    actual = {
        path.relative_to(root).as_posix(): path
        for path in root.rglob("*")
        if path.is_file() and path.name not in {"manifest.json", "README.md"}
    }
    assert manifest["schema_version"] == 1
    assert len(rows) == len(manifest["files"]) == 36
    assert set(actual) == set(rows)
    for name, path in actual.items():
        row = rows[name]
        assert row["source"] == "artifacts/engineering-workflow-datasets/output/" + name
        payload = path.read_bytes()
        assert len(payload) == row["bytes"]
        assert hashlib.sha256(payload).hexdigest() == row["sha256"]
