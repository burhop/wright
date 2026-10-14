"""Fresh original template/data copies and explicit readiness, without execution.

Uses the template/source owners. No campaign state, credentials, runs, approvals,
provider installation, or substituted simplified workflow is copied or executed.
"""

import argparse
import asyncio
import hashlib
import json
from pathlib import Path
import shutil
from types import SimpleNamespace

from data_vault import WorkspaceRepository, upgrade_database
from data_vault.secret_provider import FileSecretProvider
from workspace_service.service import WorkspaceService
from workspace_service.workflow_source_execution import compile_prompt_workflow

from reasoning_probe import DesktopConnectionMetadata


async def main(state, *, resume=False):
    state.mkdir(mode=0o700, parents=True, exist_ok=resume)
    if (state / "existing-examples.json").exists():
        raise RuntimeError(
            "Completed evidence exists; inspect it rather than repeat the probe"
        )
    database = state / "wright.sqlite"
    upgrade_database(database)
    service = WorkspaceService(
        str(database),
        repository=WorkspaceRepository(
            str(database), secrets=FileSecretProvider(state / "credentials.json")
        ),
        parent_dir_provider=lambda: str(state / "workspaces"),
    )
    evidence = {"status": "readiness only; no engineering run", "examples": []}
    repository = Path(__file__).resolve().parents[2]
    datasets = repository / "tests/datasets/engineering-workflows"
    try:
        for template, scenario in (
            ("printed-replacement-part", "01-observatory-focus-wheel"),
            ("robot-tracking-diagnosis", "01-aisle-floor-seam"),
        ):
            name = "Desktop original " + template
            existing = service.repository.get_by_name(name) if resume else None
            if existing:
                root = Path(existing["local_path"]).resolve()
                assert root.is_relative_to((state / "workspaces").resolve())
                assert (
                    service.repository.list_sessions(existing["workspace_id"])[0][
                        "agent_id"
                    ]
                    == "openai-desktop-harness"
                )
                workspace = SimpleNamespace(**existing)
            else:
                workspace = await service.create_workspace(
                    name,
                    None,
                    DesktopConnectionMetadata(),
                    agent_id="openai-desktop-harness",
                )
            detail = service.engineering_workflow_templates.detail(template)
            instance = await service.engineering_workflow_templates.instantiate(
                workspace_id=workspace.workspace_id,
                workspace_dir=workspace.local_path,
                template_id=template,
                template_version=detail["version"],
                expected_source_digest=detail["source_digest"],
                workflow_path=f"workflows/{template}.workflow.wflow",
                request_id="desktop-original-example-01-" + template,
                created_by="local isolated prototype qualification",
            )
            original = datasets / "scenarios" / template / scenario
            copied = Path(workspace.local_path) / "inputs/original-scenario"
            if not copied.exists():
                shutil.copytree(original, copied)
            else:
                assert resume
                assert {
                    p.relative_to(copied) for p in copied.rglob("*") if p.is_file()
                } == {
                    p.relative_to(original) for p in original.rglob("*") if p.is_file()
                }
            hashes = {}
            for item in sorted(original.rglob("*")):
                if item.is_file():
                    relative = item.relative_to(original)
                    digest = hashlib.sha256(item.read_bytes()).hexdigest()
                    assert (
                        digest
                        == hashlib.sha256((copied / relative).read_bytes()).hexdigest()
                    )
                    hashes[str(relative)] = digest
            bindings = datasets / "bindings" / f"{template}.json"
            copied_bindings = (
                Path(workspace.local_path) / "inputs/original-bindings.json"
            )
            if copied_bindings.exists():
                assert resume and copied_bindings.read_bytes() == bindings.read_bytes()
            else:
                shutil.copyfile(bindings, copied_bindings)
            try:
                compile_prompt_workflow(instance.document.source)
                compilation = "accepted by compiler; runtime capabilities not qualified"
            except Exception as error:
                compilation = {
                    "status": "blocked",
                    "code": getattr(error, "code", type(error).__name__),
                    "message": str(error),
                }
            evidence["examples"].append(
                {
                    "workspace_id": workspace.workspace_id,
                    "session_id": workspace.session_id,
                    "workspace_path": workspace.local_path,
                    "template_id": template,
                    "template_version": instance.template_version,
                    "template_source_digest": instance.template_source_digest,
                    "source_path": instance.document.path,
                    "source_digest": instance.document.storage_digest,
                    "original_scenario": str(original.relative_to(repository)),
                    "scenario_hashes": hashes,
                    "bindings_sha256": hashlib.sha256(
                        bindings.read_bytes()
                    ).hexdigest(),
                    "catalog_readiness": detail["readiness"],
                    "capability_requirements": detail["capability_requirements"],
                    "compiler": compilation,
                    "execution": "not started; full original capabilities remain gated",
                }
            )
        editor = await service.create_workspace(
            "Desktop hosted editor qualification",
            None,
            DesktopConnectionMetadata(),
            agent_id="openai-desktop-harness",
        )
        evidence["editor_workspace"] = {
            "workspace_id": editor.workspace_id,
            "session_id": editor.session_id,
            "workspace_path": editor.local_path,
        }
        assert not list((state / "workspaces").glob("*/runs/**/*.json"))
        (state / "existing-examples.json").write_text(json.dumps(evidence, indent=2))
        print(
            json.dumps(
                {
                    "status": evidence["status"],
                    "evidence": str(state / "existing-examples.json"),
                    "editor_workspace": evidence["editor_workspace"],
                },
                indent=2,
            )
        )
    finally:
        await service.close()


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--state-dir", required=True, type=Path)
    parser.add_argument(
        "--resume",
        action="store_true",
        help="Reconcile a partial isolated copy using its existing template request identities",
    )
    options = parser.parse_args()
    asyncio.run(main(options.state_dir.resolve(), resume=options.resume))
