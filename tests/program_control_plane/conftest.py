"""Shared isolated fixtures for the EPP control-plane suite."""

from __future__ import annotations

import sys
from datetime import datetime, timezone
from pathlib import Path

import pytest


REPOSITORY_ROOT = Path(__file__).resolve().parents[2]
SCRIPTS_ROOT = REPOSITORY_ROOT / "scripts"
if str(SCRIPTS_ROOT) not in sys.path:
    sys.path.insert(0, str(SCRIPTS_ROOT))

from fixture_builder import GitFixtureBuilder  # noqa: E402


@pytest.fixture
def fixed_now() -> datetime:
    return datetime(2026, 1, 2, 3, 4, 5, tzinfo=timezone.utc)


@pytest.fixture
def git_builder(tmp_path: Path) -> GitFixtureBuilder:
    return GitFixtureBuilder(tmp_path)


@pytest.fixture(scope="session")
def repository_root() -> Path:
    return REPOSITORY_ROOT
