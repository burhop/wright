from __future__ import annotations

import pytest

from workspace_service.executor import BoundedExecutor
from workspace_service.adapters.filesystem import LocalWorkspaceFiles
from workspace_service.adapters.runtime import WorkspaceManager
from workspace_service.use_cases.files import WorkspaceFileUseCases


@pytest.mark.asyncio
async def test_file_use_cases_preserve_tree_text_binary_and_mutations(tmp_path):
    db_path = str(tmp_path / "unused.db")
    workspace = tmp_path / "workspace"
    workspace.mkdir()
    WorkspaceManager(str(workspace))
    executor = BoundedExecutor(max_workers=2)
    use_cases = WorkspaceFileUseCases(db_path, executor, LocalWorkspaceFiles)

    await use_cases.create(str(workspace), "notes.txt", "file")
    await use_cases.write(str(workspace), "notes.txt", "hello")
    result = await use_cases.read(str(workspace), "notes.txt")
    assert result.content == b"hello"
    assert not result.binary
    assert any(
        child["name"] == "notes.txt"
        for child in (await use_cases.tree(str(workspace)))["children"]
    )
    await use_cases.move(str(workspace), "notes.txt", "moved.txt")
    await use_cases.delete(str(workspace), "moved.txt")
    await executor.close()


@pytest.mark.asyncio
async def test_file_use_cases_reject_escape(tmp_path):
    workspace = tmp_path / "workspace"
    workspace.mkdir()
    executor = BoundedExecutor(max_workers=1)
    use_cases = WorkspaceFileUseCases(
        str(tmp_path / "unused.db"), executor, LocalWorkspaceFiles
    )
    with pytest.raises(ValueError):
        await use_cases.write(str(workspace), "../outside.txt", "no")
    await executor.close()
