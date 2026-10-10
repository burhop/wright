"""Read inactive UI source through the existing import receipt and file owner."""

import hashlib
import json
from pathlib import Path

from pydantic import TypeAdapter

from core.process_validation import Identifier
from core.workflow_bundle import (
    ASSET_MAX_BYTES,
    BundleDependency,
    ImportedInterfaceReference,
    PortableInterface,
    portable_path,
)

from ..workflow_sources import WorkspaceWorkflowSourceStore, WorkflowSourceStorageError
from .errors import ProcessInterfaceError


def _unavailable():
    return ProcessInterfaceError(
        "UI_INCOMPATIBLE",
        "The imported interface source is unavailable or has changed.",
        "Refresh imported interfaces or restore the imported files. The common view and local interfaces remain available.",
    )


class ImportedInterfaceLibrary:
    def __init__(self, workspace_dir, source_path):
        self.store = WorkspaceWorkflowSourceStore(workspace_dir)
        self.store._source_path(source_path)
        slug = Path(source_path).name.removesuffix(".workflow.wflow")
        self.directory = portable_path(f"imported-assets/{slug}")
        self.root = Path(workspace_dir)
        self.source_path = source_path

    def _inventory(self):
        receipt = self.directory + "/manifest.json"
        # No imported interface is an ordinary condition. Existing paths still
        # go through the pinned, bounded reader (including reparse-point checks).
        if not (self.root / receipt).exists():
            return {}
        value = json.loads(self.store.read_artifact_bytes(receipt, max_bytes=1_048_576))
        if (
            not isinstance(value, dict)
            or value.get("authority") != "definition-only-local-readiness-required"
        ):
            raise ValueError("Invalid import receipt")
        if value.get("destination_path", self.source_path) != self.source_path:
            raise ValueError("Import receipt belongs to another workflow")
        ids = TypeAdapter(tuple[Identifier, ...]).validate_python(
            value["interface_candidates"]
        )
        if len(ids) > 16 or len(set(ids)) != len(ids):
            raise ValueError("Invalid candidate inventory")
        dependencies = TypeAdapter(tuple[BundleDependency, ...]).validate_python(
            value["requirements"]
        )
        if len(dependencies) > 256:
            raise ValueError("Oversized import receipt")
        ui_dependencies = [
            d
            for d in dependencies
            if d.category == "ui" and d.disposition == "embedded"
        ]
        if len(ui_dependencies) != len(ids) or {
            d.identity for d in ui_dependencies
        } != set(ids):
            raise ValueError("Interface inventory disagrees with import receipt")
        return {d.identity: d.sha256 for d in ui_dependencies}

    def _read(self, identity, inventory):
        if identity not in inventory:
            raise ValueError("Candidate not declared by this import")
        name = portable_path(f"{self.directory}/interfaces/{identity}.json")
        raw = self.store.read_artifact_bytes(name, max_bytes=ASSET_MAX_BYTES)
        value = PortableInterface.model_validate_json(raw)
        if (
            value.manifest.ui_id != identity
            or value.source_digest != inventory[identity]
        ):
            raise ValueError("Candidate differs from its import receipt")
        return value, hashlib.sha256(raw).hexdigest()

    def list(self):
        try:
            inventory = self._inventory()
        except (OSError, ValueError, KeyError, WorkflowSourceStorageError):
            return {"candidates": [], "reasons": [_unavailable().reason]}
        candidates, reasons = [], []
        for identity in inventory:
            try:
                value, digest = self._read(identity, inventory)
                candidates.append(
                    {
                        "ui_id": identity,
                        "sha256": digest,
                        "title": value.manifest.title,
                        "client_version": value.manifest.client_version,
                        "kit_version": value.manifest.kit_version,
                    }
                )
            except (OSError, ValueError, KeyError, WorkflowSourceStorageError):
                reasons.append(_unavailable().reason)
        return {"candidates": candidates, "reasons": reasons}

    def read(self, reference: ImportedInterfaceReference):
        try:
            value, digest = self._read(reference.ui_id, self._inventory())
            if digest != reference.sha256:
                raise ValueError("Selected candidate changed")
            return value
        except (OSError, ValueError, KeyError, WorkflowSourceStorageError) as error:
            raise _unavailable() from error
