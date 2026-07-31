from __future__ import annotations

from pathlib import Path

import pytest

from data_vault import (
    GenerationProvenanceRepository,
    SurfaceDiagnosticRepository,
    SurfaceGrantRepository,
    SurfacePreferenceRepository,
    SurfaceRepository,
    SurfaceRuntimeRepository,
    SurfaceVault,
)
from workspace_service.composition import build_surface_application


pytestmark = [pytest.mark.workspace_surfaces, pytest.mark.asyncio]


async def test_surface_application_owns_complete_foundation_graph(
    tmp_path: Path,
) -> None:
    application = build_surface_application(tmp_path / "state.db")

    assert isinstance(application.repository, SurfaceRepository)
    assert isinstance(
        application.provenance_repository, GenerationProvenanceRepository
    )
    assert isinstance(application.preference_repository, SurfacePreferenceRepository)
    assert isinstance(application.grant_repository, SurfaceGrantRepository)
    assert isinstance(application.runtime_repository, SurfaceRuntimeRepository)
    assert isinstance(application.diagnostic_repository, SurfaceDiagnosticRepository)
    assert isinstance(application.vault, SurfaceVault)
    assert application.service.repository is application.repository
    assert application.service.events is application.events
    assert application.accepting_commands is False

    await application.reconcile_startup()
    assert application.accepting_commands is True
    await application.close()
    assert application.accepting_commands is False
