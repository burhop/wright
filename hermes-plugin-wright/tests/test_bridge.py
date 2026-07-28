from __future__ import annotations

import pytest

from hermes_plugin_wright.bridge import LegacyBridgeRemoved, migration_required


def test_legacy_repository_bridge_fails_with_migration_guidance() -> None:
    with pytest.raises(LegacyBridgeRemoved, match="wright-engineering"):
        migration_required()


def test_legacy_bridge_contains_no_repository_detection() -> None:
    import hermes_plugin_wright.bridge as bridge

    source = open(bridge.__file__, encoding="utf-8").read().lower()
    assert "detect_repo_dir" not in source
    assert "wright_repo_dir" not in source
