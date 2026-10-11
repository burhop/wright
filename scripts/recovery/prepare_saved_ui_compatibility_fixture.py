"""Negative UI compatibility fixture; inactive and never presented/executed.

Transfers a definition to a fresh isolated scope through the bundle API. The
unsupported-version transport fixture exercises the actual backend validator.
It is not a generated, built, reviewed or accepted working interface.
"""

import json
from pathlib import Path
import sys
from uuid import uuid4

import httpx
from core.process_interfaces import Compatibility, InterfaceManifest
from core.process_interactions import ProcessRef
from workspace_service.process_interfaces.build import validate_manifest_bindings
from workspace_service.process_interfaces.errors import ProcessInterfaceError
from data_vault.process_interface_repository import ProcessInterfaceRepository


def main():
    artifact = Path(sys.argv[1])
    artifact.mkdir(parents=True, exist_ok=True)
    auth = json.loads(Path(sys.argv[2]).read_text(encoding="utf-8"))
    workspace = json.loads(Path(sys.argv[3]).read_text(encoding="utf-8"))[0]
    base = workspace["url"].split("/workspace/")[0]
    original = {
        "session_id": "083-printed-prompt-session-055",
        "path": "workflows/printed-replacement-part-mixed-default-071.workflow.wflow",
    }
    destination = f"workflows/ui-version-negative-{uuid4().hex[:8]}.workflow.wflow"
    with httpx.Client(base_url=base, timeout=60) as client:
        client.post(
            "/api/auth/session", json={"token": auth["api_token"]}
        ).raise_for_status()
        source = client.get("/api/workspace/workflow-sources", params=original)
        source.raise_for_status()
        source = source.json()
        exported = client.post(
            "/api/workspace/workflow-bundles/export",
            json={
                "session_id": original["session_id"],
                "path": original["path"],
                "expected_storage_digest": source["storage_digest"],
                "mode": "source",
                "selected_reference_paths": [],
                "selected_ui_ids": [],
            },
        )
        exported.raise_for_status()
        envelope = exported.json()
        imported = client.post(
            "/api/workspace/workflow-bundles/import",
            json={
                "session_id": workspace["session_id"],
                "bundle": envelope["bundle"],
                "destination_path": destination,
                "expected_bundle_digest": envelope["bundle_digest"],
            },
        )
        imported.raise_for_status()
        copied = imported.json()["source"]
        assert copied["source"] == source["source"]
    db = Path(".local-run/process-interfaces-083/instruction-portability/state.db")
    repository = ProcessInterfaceRepository(db)
    old = repository.get_revision(
        "083-fresh-prompt-055",
        "ui-f47e26fbcc2e44a2a7c4dc939aef1948",
        "revision-b1d66dc13ace45889297568cd38c6ee0",
    )
    process = {
        "workspace_id": workspace["workspace_id"],
        "source_path": destination,
        "source_digest": copied["storage_digest"],
    }
    ui_id, revision_id = "ui-" + uuid4().hex, "revision-" + uuid4().hex
    manifest = InterfaceManifest.model_validate(
        {
            **old.manifest.model_dump(mode="json"),
            "ui_id": ui_id,
            "revision_id": revision_id,
            "parent_revision": None,
            "process": process,
            "client_version": "999.0.0",
            "title": "Negative fixture: unsupported client version",
            "bindings": (),
            "navigation": (),
            "capabilities": ("process.read",),
        }
    )
    # The fixture is never registered or activated. No authoring/build chain is
    # fabricated. Its backend-computed response is only injected at the browser
    # transport boundary, separately from live saved-revision acceptance proof.
    try:
        validate_manifest_bindings(manifest, ProcessRef.model_validate(process), [])
    except ProcessInterfaceError as error:
        response = Compatibility(
            ui_id=ui_id,
            revision_id=revision_id,
            current_process=ProcessRef.model_validate(process),
            state="incompatible",
            reasons=(error.reason,),
        )
    else:
        raise AssertionError("Unsupported client version was accepted")
    (artifact / "backend-version-response.json").write_text(
        response.model_dump_json(indent=2),
        encoding="utf-8",
    )
    receipt = {
        "fixture_only": True,
        "inactive": True,
        "browser_transport_fixture": True,
        "registered": False,
        "workspace": workspace,
        "process": process,
        "ui_id": ui_id,
        "revision_id": revision_id,
    }
    (artifact / "fixture.json").write_text(
        json.dumps(receipt, indent=2), encoding="utf-8"
    )
    print(
        json.dumps(
            {
                "fixture": str(artifact / "fixture.json"),
                "active": False,
                "process_actions": 0,
            }
        )
    )


if __name__ == "__main__":
    main()
