from pathlib import Path

import pytest

from scripts.release.version import (
    ReleaseIdentityError,
    parse_product_version,
    validate_release_version,
)


ROOT = Path(__file__).resolve().parents[2]


def test_product_version_normalizes_semver_prerelease_to_pep440() -> None:
    version = parse_product_version("v1.2.3-rc.4")
    assert version.semver == "1.2.3-rc.4"
    assert version.python == "1.2.3rc4"
    assert version.tag == "v1.2.3-rc.4"
    assert version.prerelease


@pytest.mark.parametrize("value", ["1.2", "01.2.3", "1.2.3-dev.1", "latest"])
def test_product_version_rejects_unsupported_identity(value: str) -> None:
    with pytest.raises(ReleaseIdentityError):
        parse_product_version(value)


def test_tag_must_match_root_version() -> None:
    assert validate_release_version(ROOT, tag="v0.1.0").python == "0.1.0"
    with pytest.raises(ReleaseIdentityError):
        validate_release_version(ROOT, tag="v0.1.1")
