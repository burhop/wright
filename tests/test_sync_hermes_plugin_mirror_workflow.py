from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def test_sync_workflow_can_publish_mirror_with_history_preserved() -> None:
    workflow = (ROOT / ".github/workflows/sync-hermes-plugin-mirror.yml").read_text(
        encoding="utf-8"
    )

    assert "publish:" in workflow
    assert "HERMES_PLUGIN_MIRROR_SSH_KEY" in workflow
    assert "git@github.com:burhop/hermes-plugin-wright.git" in workflow
    assert "git ls-remote --exit-code --heads" in workflow
    assert "git clone --depth 1 --branch" in workflow
    assert 'git -C "$publish_dir" commit' in workflow
    assert 'git -C "$publish_dir" push origin "HEAD:$MIRROR_BRANCH"' in workflow
    assert "--force" not in workflow
