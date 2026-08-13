"""Application use cases for the offline engineering-model catalog."""

from __future__ import annotations

import platform as platform_module
import shutil
from pathlib import Path
from typing import Callable

import psutil
from model_registry.catalog import ModelCatalog, ModelCatalogError, ModelCatalogFilters
from model_registry.policy import HostObservation
from tool_registry.model_library_port import EngineeringModelPortError


def observe_local_model_host(data_root: str | Path | None = None) -> HostObservation:
    platform_names = {
        "darwin": "macos",
        "linux": "linux",
        "windows": "windows",
    }
    architectures = {
        "amd64": "x86_64",
        "x86_64": "x86_64",
        "aarch64": "aarch64",
        "arm64": "aarch64",
    }
    system = platform_names.get(platform_module.system().lower(), "unknown")
    architecture = architectures.get(platform_module.machine().lower(), "unknown")
    target = Path(data_root) if data_root is not None else Path.cwd()
    try:
        available_disk = shutil.disk_usage(target).free
    except OSError:
        available_disk = 0
    return HostObservation(
        platform=system,
        architecture=architecture,
        available_disk_bytes=available_disk,
        available_ram_bytes=int(psutil.virtual_memory().available),
        accelerators=frozenset({"cpu"}),
        runtime_adapters={"wright-deterministic": "1.0.0"},
    )


class EngineeringModelService:
    """Read-only first slice; constructing it performs no source or runtime calls."""

    def __init__(
        self,
        *,
        catalog: ModelCatalog | None = None,
        host_observer: Callable[[], HostObservation] | None = None,
    ) -> None:
        self.catalog = catalog or ModelCatalog.load_bundled()
        self.host_observer = host_observer or observe_local_model_host

    def list_catalog(
        self,
        *,
        search: str | None = None,
        task: str | None = None,
        source_kind: str | None = None,
        readiness: tuple[str, ...] = (),
        platform: str | None = None,
        architecture: str | None = None,
        accelerator: str | None = None,
        evidence_state: str | None = None,
        maximum_bytes: int | None = None,
        cursor: str | None = None,
        limit: int = 50,
    ) -> dict:
        try:
            page = self.catalog.list(
                ModelCatalogFilters(
                    search=search,
                    task=task,
                    source_kind=source_kind,
                    readiness=readiness,
                    platform=platform,
                    architecture=architecture,
                    accelerator=accelerator,
                    evidence_state=evidence_state,
                    maximum_bytes=maximum_bytes,
                ),
                host=self.host_observer(),
                cursor=cursor,
                limit=limit,
            )
        except ModelCatalogError as error:
            raise EngineeringModelPortError(
                error.code,
                str(error),
                "Adjust the bounded filters or reload the current offline snapshot.",
            ) from error
        return {
            "snapshot": self.catalog.snapshot.projection(),
            "models": list(page.items),
            "next_cursor": page.next_cursor,
            "total": page.total,
        }

    def get_catalog_model(self, model_id: str) -> dict:
        try:
            return self.catalog.get_view(model_id, host=self.host_observer())
        except ModelCatalogError as error:
            raise EngineeringModelPortError(
                error.code,
                str(error),
                "Choose a model from the active offline catalog snapshot.",
            ) from error


__all__ = ["EngineeringModelService", "observe_local_model_host"]
