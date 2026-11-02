from __future__ import annotations

import base64
import hashlib
from pathlib import Path
import zipfile

from check_wheel_contents.contents import WheelContents
import pytest

from scripts.release.wheel_policy import (
    DUPLICATE_RESOURCE_GROUPS,
    NATIVE_PACKAGE_ROOTS,
    PATH_ADDRESSED_SCRIPTS,
    WheelPolicyError,
    inspect_findings,
    main,
)


ROOT = Path(__file__).resolve().parents[2]


def contents(files: dict[str, bytes]) -> WheelContents:
    result = WheelContents(
        "wright_engineering-1.dist-info", "wright_engineering-1.data"
    )
    files = {
        **{f"{root}__init__.py": repr(root).encode() for root in NATIVE_PACKAGE_ROOTS},
        **files,
    }
    for path, payload in files.items():
        digest = base64.urlsafe_b64encode(hashlib.sha256(payload).digest()).rstrip(b"=")
        result.add_record_rows([[path, "sha256=" + digest.decode(), str(len(payload))]])
    return result


@pytest.mark.parametrize("group", DUPLICATE_RESOURCE_GROUPS)
def test_only_reviewed_duplicate_resource_subjects_are_accepted(
    group: frozenset[str],
) -> None:
    findings = inspect_findings(
        contents(dict.fromkeys(group, b'{"shared": "resource"}'))
    )
    assert {finding.check.name for finding in findings} == {"W002", "W009"}


@pytest.mark.parametrize("path", sorted(PATH_ADDRESSED_SCRIPTS))
def test_path_addressed_setup_scripts_are_accepted(path: str) -> None:
    findings = inspect_findings(contents({path: b"print('setup resource')\n"}))
    assert {finding.check.name for finding in findings} == {"W004", "W009"}


def test_new_duplicate_next_to_reviewed_resources_is_rejected() -> None:
    files = dict.fromkeys(DUPLICATE_RESOURCE_GROUPS[0], b'{"shared": "resource"}')
    files["workspace_service/unreviewed.json"] = b'{"shared": "resource"}'
    with pytest.raises(WheelPolicyError, match="W002"):
        inspect_findings(contents(files))


def test_unrelated_duplicate_group_is_rejected() -> None:
    with pytest.raises(WheelPolicyError, match="W002"):
        inspect_findings(
            contents({"core/one.json": b"same data", "core/two.json": b"same data"})
        )


def test_new_nonimportable_script_in_reviewed_directory_is_rejected() -> None:
    path = next(iter(PATH_ADDRESSED_SCRIPTS)).rsplit("/", 1)[0] + "/unreviewed.py"
    with pytest.raises(WheelPolicyError, match="W004"):
        inspect_findings(contents({path: b"print('unreviewed resource')\n"}))


def test_new_package_root_is_rejected() -> None:
    with pytest.raises(WheelPolicyError, match="W009"):
        inspect_findings(contents({"unreviewed/__init__.py": b"'unreviewed'"}))


def test_other_checker_findings_are_still_blocking() -> None:
    with pytest.raises(WheelPolicyError, match="W001"):
        inspect_findings(contents({"core/cache.pyc": b"compiled data"}))


def test_command_rejects_a_non_native_wheel_before_resource_exceptions(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    wheel = tmp_path / "unreviewed-1.0-py3-none-any.whl"
    with zipfile.ZipFile(wheel, "w") as archive:
        archive.writestr("unreviewed/__init__.py", "'unreviewed'\n")
        archive.writestr(
            "unreviewed-1.0.dist-info/METADATA", "Name: unreviewed\nVersion: 1.0\n"
        )
    assert main([str(wheel)]) == 1
    assert wheel.name in capsys.readouterr().err


def test_every_publication_and_native_pr_gate_uses_the_same_policy() -> None:
    release = (ROOT / ".github/workflows/release.yml").read_text()
    native = (ROOT / ".github/workflows/native-hermes-pr.yml").read_text()
    merge = (ROOT / "scripts/check-dev-merge.sh").read_text()
    production = (ROOT / "scripts/check-prod-merge.sh").read_text()
    assert release.count("python -m scripts.release.wheel_policy") == 2
    for text in (native, merge, production):
        assert "python -m scripts.release.wheel_policy" in text
        assert "check-wheel-contents==0.6.3" in text
