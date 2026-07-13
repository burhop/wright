from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def test_publish_workflow_uses_exact_candidate_and_protected_trusted_publishing() -> (
    None
):
    workflow = (ROOT / ".github/workflows/publish-python-packages.yml").read_text(
        encoding="utf-8"
    )

    assert "workflow_call:" in workflow
    assert "artifact-name:" in workflow
    assert "verified-python-candidate" in workflow
    assert "sha256sum --check SHA256SUMS" in workflow
    assert "scripts/build-python-distributions.sh" not in workflow
    assert "id-token: write" in workflow
    assert workflow.count("id-token: write") == 2
    assert "name: pypi" in workflow
    assert "name: testpypi" in workflow
    assert (
        workflow.count(
            "pypa/gh-action-pypi-publish@cef221092ed1bacb1cc03d23a2d87d1d172e277b"
        )
        == 2
    )
    assert "repository-url: https://test.pypi.org/legacy/" in workflow
    assert "wright-engineering" in workflow
    assert (
        workflow.index("publish-testpypi:")
        < workflow.index("verify-testpypi:")
        < workflow.index("publish-pypi:")
    )
    assert "wright-core" not in workflow
    assert "wright-tool-registry" not in workflow
