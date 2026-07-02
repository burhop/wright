from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def test_publish_workflow_uses_trusted_publishing_and_package_inputs() -> None:
    workflow = (ROOT / ".github/workflows/publish-python-packages.yml").read_text(
        encoding="utf-8"
    )

    assert "workflow_dispatch:" in workflow
    assert "package:" in workflow
    assert "target:" in workflow
    assert "id-token: write" in workflow
    assert "environment:" in workflow
    assert "name: pypi" in workflow
    assert "name: testpypi" in workflow
    assert "pypa/gh-action-pypi-publish" in workflow
    assert "repository-url: https://test.pypi.org/legacy/" in workflow
    assert "scripts/build-python-distributions.sh" in workflow
