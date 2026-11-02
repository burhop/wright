from pathlib import Path

from scripts.release.workflow_policy import job_blocks

ROOT = Path(__file__).resolve().parents[1]


def test_publish_workflow_uses_exact_candidate_and_protected_trusted_publishing() -> (
    None
):
    workflow = (ROOT / ".github/workflows/release.yml").read_text(encoding="utf-8")

    assert not (ROOT / ".github/workflows/publish-python-packages.yml").exists()
    assert "uses: ./.github/workflows/publish-python-packages.yml" not in workflow
    assert "verified-python-candidate" in workflow
    assert "sha256sum --check SHA256SUMS" in workflow
    jobs = dict(job_blocks(workflow))
    publisher = "pypa/gh-action-pypi-publish@7245906fb61fa33a13554f9d5fb856fe61758086"
    publishing_jobs = {name for name, block in jobs.items() if publisher in block}
    assert publishing_jobs == {
        "publish-testpypi",
        "publish-pypi",
        "dev-publish-testpypi",
    }
    assert {name for name, block in jobs.items() if "id-token: write" in block} == (
        publishing_jobs | {"oci-candidate"}
    )
    for name in publishing_jobs:
        block = jobs[name]
        assert block.count(publisher) == 1
        assert block.count("id-token: write") == 1
        assert "sha256sum --check SHA256SUMS" in block
        assert block.count("cp dist/*.whl dist/*.tar.gz publish-dist/") == 1
        assert block.count("packages-dir: publish-dist") == 1
        assert (
            block.count('test "$(find publish-dist -maxdepth 1 -type f | wc -l)" = 2')
            == 1
        )
        if name == "publish-pypi":
            assert "name: pypi" in block
            assert "repository-url:" not in block
        else:
            assert "name: testpypi" in block
            assert "repository-url: https://test.pypi.org/legacy/" in block
    assert workflow.count("Verify hashes and stage only distributions") == 2
    assert "packages-dir: dist\n" not in workflow
    assert "wright-engineering" in workflow
    assert (
        workflow.index("\n  publish-testpypi:")
        < workflow.index("\n  verify-testpypi:")
        < workflow.index("\n  publish-pypi:")
    )
    assert "wright-core" not in workflow
    assert "wright-tool-registry" not in workflow


def test_pypi_publish_action_is_never_called_from_a_reusable_workflow() -> None:
    publisher = "pypa/gh-action-pypi-publish@7245906fb61fa33a13554f9d5fb856fe61758086"
    workflows = sorted((ROOT / ".github/workflows").glob("*.yml"))
    publishing_workflows = [
        path for path in workflows if publisher in path.read_text(encoding="utf-8")
    ]

    assert publishing_workflows == [ROOT / ".github/workflows/release.yml"]
    assert "workflow_call:" not in publishing_workflows[0].read_text(encoding="utf-8")
