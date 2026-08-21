from __future__ import annotations

import io
import json
import hashlib
import zipfile

import numpy as np
import pytest

from model_registry.chatter_runtime import load_forest
from model_registry.generated import (
    chatter_fixture_artifacts,
    generated_chatter_package,
)
from model_registry.models import canonical_digest


def _write(root, artifacts):
    for name, value in artifacts.items():
        path = root.joinpath(*name.split("/"))
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(value)


def test_loader_rejects_object_arrays_before_model_use(tmp_path) -> None:
    artifacts = chatter_fixture_artifacts(generated_chatter_package())
    output = io.BytesIO()
    with zipfile.ZipFile(output, "w") as archive:
        member = io.BytesIO()
        np.lib.format.write_array(
            member, np.asarray([object()], dtype=object), allow_pickle=True
        )
        archive.writestr("tree_offsets.npy", member.getvalue())
    artifacts["model/forest.npz"] = output.getvalue()
    _write(tmp_path, artifacts)
    with pytest.raises((ValueError, OSError)):
        load_forest(tmp_path)


def test_loader_rejects_extra_members_and_changed_topology(tmp_path) -> None:
    artifacts = chatter_fixture_artifacts(generated_chatter_package())
    _write(tmp_path, artifacts)
    forest = tmp_path / "model" / "forest.npz"
    with zipfile.ZipFile(forest, "a") as archive:
        archive.writestr("extra.npy", b"not-an-array")
    with pytest.raises(ValueError, match="digest"):
        load_forest(tmp_path)


def _mutated_artifacts(change):
    artifacts = chatter_fixture_artifacts(generated_chatter_package())
    with np.load(
        io.BytesIO(artifacts["model/forest.npz"]), allow_pickle=False
    ) as archive:
        arrays = {name: np.asarray(archive[name]).copy() for name in archive.files}
    change(arrays)
    output = io.BytesIO()
    np.savez(output, **arrays)
    forest = output.getvalue()
    metadata = json.loads(artifacts["model/serving-metadata.json"])
    metadata["classifier"]["forest_sha256"] = hashlib.sha256(forest).hexdigest()
    material = dict(metadata)
    material.pop("metadata_digest")
    metadata["metadata_digest"] = canonical_digest(material)
    artifacts["model/forest.npz"] = forest
    artifacts["model/serving-metadata.json"] = json.dumps(
        metadata, sort_keys=True, separators=(",", ":")
    ).encode()
    return artifacts


@pytest.mark.parametrize(
    "change",
    [
        lambda arrays: arrays.__setitem__(
            "threshold", arrays["threshold"].astype("float32")
        ),
        lambda arrays: arrays.__setitem__(
            "threshold", arrays["threshold"].reshape((-1, 1))
        ),
        lambda arrays: arrays["threshold"].__setitem__(0, np.inf),
        lambda arrays: arrays["leaf_class_fraction"].__setitem__(0, 2.0),
        lambda arrays: arrays["children_left"].__setitem__(0, 0),
        lambda arrays: arrays["feature"].__setitem__(0, 999),
    ],
)
def test_loader_rejects_dtype_shape_finiteness_topology_and_index_bombs(
    tmp_path, change
) -> None:
    _write(tmp_path, _mutated_artifacts(change))
    with pytest.raises(ValueError):
        load_forest(tmp_path)
