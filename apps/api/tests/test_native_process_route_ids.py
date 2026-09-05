"""Every language-valid process ID has an unambiguous canonical HTTP resource."""

from __future__ import annotations

import json

import pytest
from fastapi.testclient import TestClient

from test_native_process_execution_api import (
    AUTH,
    BASE,
    SESSION,
    app_for,
    document,
    execution as execution,
    submission,
    wait_run,
)
from workspace_service.native_process_cli import main as cli_main


@pytest.mark.parametrize(
    "process_id", ["bindings", "contract", "examples", "runs", "check", "documents"]
)
def test_service_names_remain_usable_document_ids(
    execution, process_id, capsys, monkeypatch
):
    monkeypatch.setenv("WRIGHT_API_TOKEN", "native-api-test-token")
    collection = f"{BASE}/documents"
    path = f"{collection}/{process_id}"
    definition = document()
    definition["id"] = process_id
    with TestClient(app_for(execution), headers=AUTH) as client:
        created = client.post(
            collection,
            params=SESSION,
            json={
                "definition": definition,
                "presentation": {},
                "request_id": "create-reserved-id",
            },
        )
        assert created.status_code == 201, created.text
        saved = created.json()
        reopened = client.get(path, params=SESSION)
        assert reopened.status_code == 200, reopened.text
        assert reopened.json() == saved

        definition["title"] = "Updated reserved-ID process"
        updated = client.put(
            path,
            params=SESSION,
            json={
                "definition": definition,
                "presentation": {},
                "expected_token": saved["token"],
                "request_id": "update-reserved-id",
            },
        )
        assert updated.status_code == 200, updated.text
        saved = updated.json()
        assert saved["revision"] == 2
        assert client.get(path, params=SESSION).json() == saved
        listed = client.get(collection, params=SESSION)
        assert listed.status_code == 200, listed.text
        assert [item["id"] for item in listed.json()["documents"]] == [process_id]

        history = client.get(path + "/runs", params=SESSION)
        assert history.status_code == 200, history.text
        assert history.json() == {"runs": [], "next_cursor": None}
        started = client.post(
            path + "/runs",
            params=SESSION,
            json=submission(saved, "run-reserved-id"),
        )
        assert started.status_code == 202, started.text
        run_id = started.json()["run_id"]
        result = wait_run(client, run_id)
        assert result["state"] == "succeeded", result["reason"]
        assert result["snapshot"]["definition"] == definition
        history = client.get(path + "/runs", params=SESSION).json()["runs"]
        assert [(item["process_id"], item["run_id"]) for item in history] == [
            (process_id, run_id)
        ]

        # The real HTTP CLI replays the same submission through the canonical URL.
        requested = []
        client.event_hooks["request"].append(
            lambda request: requested.append(request.url.path)
        )
        capsys.readouterr()
        assert (
            cli_main(
                [
                    "--base-url",
                    "http://testserver",
                    "--session-id",
                    "session-one",
                    "run",
                    process_id,
                    "--expected-token",
                    saved["token"],
                    "--request-id",
                    "run-reserved-id",
                ],
                client=client,
            )
            == 0
        )
        assert requested == [path + "/runs"]
        assert json.loads(capsys.readouterr().out.splitlines()[-1]) == started.json()

        for scoped_path in (path, path + "/runs"):
            denied = client.get(scoped_path, params={"session_id": "session-two"})
            assert denied.status_code == 404, denied.text
            assert denied.json()["code"] == "NATIVE_NOT_FOUND"
        for action, field in (
            ("contract", "schema"),
            ("examples", "examples"),
            ("bindings", "bindings"),
        ):
            response = client.get(f"{BASE}/{action}", params=SESSION)
            assert response.status_code == 200, response.text
            assert field in response.json()


def test_legacy_aliases_remain_available_but_openapi_publishes_canonical_paths(
    execution,
):
    with TestClient(app_for(execution), headers=AUTH) as client:
        definition = document()
        created = client.post(
            BASE,
            params=SESSION,
            json={
                "definition": definition,
                "presentation": {},
                "request_id": "legacy-create",
            },
        )
        assert created.status_code == 201, created.text
        saved = created.json()
        legacy = f"{BASE}/{definition['id']}"
        assert client.get(legacy, params=SESSION).json() == saved
        assert (
            client.get(BASE, params=SESSION).json()["documents"][0]["id"]
            == definition["id"]
        )
        definition["title"] = "Updated using compatibility alias"
        updated = client.put(
            legacy,
            params=SESSION,
            json={
                "definition": definition,
                "presentation": {},
                "request_id": "legacy-update",
                "expected_token": saved["token"],
            },
        )
        assert updated.status_code == 200, updated.text
        started = client.post(
            legacy + "/runs", params=SESSION, json=submission(updated.json())
        )
        assert started.status_code == 202, started.text
        result = wait_run(client, started.json()["run_id"])
        assert result["state"] == "succeeded"
        assert (
            client.get(legacy + "/runs", params=SESSION).json()["runs"][0]["run_id"]
            == result["run_id"]
        )

        paths = client.get("/openapi.json").json()["paths"]
        assert f"{BASE}/documents" in paths
        assert f"{BASE}/documents/{{process_id}}" in paths
        assert f"{BASE}/documents/{{process_id}}/runs" in paths
        assert BASE not in paths
        assert f"{BASE}/{{process_id}}" not in paths
        assert f"{BASE}/{{process_id}}/runs" not in paths
