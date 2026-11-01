"""Mock API fixtures; not claims of actual customer or guest behavior."""

import copy
import importlib.util
import json
from pathlib import Path
import re

import pytest


ROOT = Path(__file__).resolve().parents[2]
PATH = ROOT / "scripts/synthetic_beta_testing/assets/prepare-handle-checkpoint.py"
SPEC = importlib.util.spec_from_file_location("beta_checkpoint_fixture", PATH)
checkpoint = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(checkpoint)
SOURCE = (
    ROOT
    / "packages/workspace_service/src/workspace_service/engineering_workflow_templates/templates/replacement-drawer-handle.workflow.wflow"
).read_text()


class FakeClient:
    def __init__(self, root, token="t" + "a" * 24, alteration=None):
        self.events = []
        self.root, self.token, self.alteration = root, token, alteration
        self.source = SOURCE
        self.layout = {"workflowId": "workflow.__instance__", "positions": {}}
        self.instructions = {
            "schema_version": "wright.workflow-instructions/1",
            "profile_id": "fixture.defaults",
            "profile_version": "1.2.1",
            "assets": [
                {
                    "body": "Fixture saved policy",
                    "body_digest": checkpoint.digest(b"Fixture saved policy"),
                }
            ],
            "bindings": [],
        }
        names = set(re.findall(r"__input_root__/([A-Za-z0-9_./-]+)", self.source))
        for name in names:
            path = root / "inputs" / token / name
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text("Fixed fixture resource: " + name)

    def request(self, path, body=None, **kwargs):
        self.events.append(
            {
                "method": "POST" if body else "GET",
                "path": path,
                "body": copy.deepcopy(body),
            }
        )
        if kwargs.get("document"):
            assert path == "/"
            return b"Native browser bootstrap fixture"
        if kwargs.get("binary"):
            return b"Fixture preview"
        if path.endswith("?version=1.0.1"):
            value = {
                "template": {
                    "template_id": checkpoint.TEMPLATE_ID,
                    "version": "wrong" if self.alteration == "version" else "1.0.1",
                    "source_digest": checkpoint.TEMPLATE_SHA256,
                    "source": self.source,
                    "layout": self.layout,
                    "layout_digest": "b" * 64,
                }
            }
            return value
        if path.endswith("/create"):
            return {
                "workspace_id": "workspace-" + self.token,
                "session_id": "session-" + self.token,
                "local_path": str(self.root),
            }
        if path.endswith("/activate"):
            return {}
        if "/instruction-defaults?" in path:
            return {
                "instructions": self.instructions,
                "digest": checkpoint.canonical_digest(self.instructions),
                "origin": "packaged",
                "revision": "d" * 64,
            }
        if path.endswith("/instances"):
            source = self.source.replace("__instance__", self.token).replace(
                "__input_root__", "inputs/" + self.token
            )
            lines = source.splitlines(keepends=True)
            index = next(
                i
                for i, line in enumerate(lines)
                if line.strip() == "workflow " + self.token
            )
            lines.insert(
                index + 1,
                "  instructions: "
                + json.dumps(self.instructions, separators=(",", ":"))
                + "\n",
            )
            source = "".join(lines)
            if self.alteration == "engineering":
                source = source.replace("96 mm", "97 mm")
            return {
                "workspace_id": "workspace-" + self.token,
                "workflow_id": "workflow." + self.token,
                "path": checkpoint.WORKFLOW_PATH,
                "source": source,
                "layout": json.loads(
                    json.dumps(self.layout).replace("__instance__", self.token)
                ),
                "storage_digest": checkpoint.digest(source.encode()),
                "storage_revision": 1,
                "definition_revision": 1,
                "metadata_authority": "wright_host",
                "template": {
                    "template_id": checkpoint.TEMPLATE_ID,
                    "version": "1.0.1",
                    "source_digest": checkpoint.TEMPLATE_SHA256,
                    "layout_digest": "b" * 64,
                },
            }
        if path.endswith("/setup/options"):
            assert body["session_id"] == "session-" + self.token
            return {
                "workspace_id": "workspace-" + self.token,
                "workflow_id": self.token,
                "path": checkpoint.WORKFLOW_PATH,
                "workspace_mount": str(self.root),
                "tools": {
                    "construction": [{"name": "existing-tool"}]
                    if self.alteration == "tool"
                    else [],
                    "geometry": [],
                    "slicer": [],
                    "inspection": [],
                },
                "recipe": {
                    "id": "printed-handle-orca",
                    "version": "2",
                    "digest": "c" * 64,
                },
                "requirements": ["Retain all engineering requirements"],
                "profiles": {
                    "mode": "workspace_files",
                    "roles": [
                        "machine",
                        "process_original",
                        "process_orca",
                        "filament",
                    ],
                },
            }
        raise AssertionError("Undeclared API action " + path)


def test_exact_template_instance_and_scope_are_preserved(tmp_path):
    client = FakeClient(tmp_path)
    result = checkpoint.prepare(client)
    assert result["storage_revision"] == 1
    assert result["entry_url"].startswith("http://wright.localhost:8000/workspace/")
    assert (
        "workflow=canonical&workflowPath=workflows%2Freplace-a-broken-drawer-handle.workflow.wflow"
        in result["entry_url"]
    )
    assert result["logical_checkpoint"]["source_sha256"] == checkpoint.TEMPLATE_SHA256
    assert all("not customer" in result[key] for key in ["scope"])
    assert client.events[0]["path"] == "/"
    mutations = [event["path"] for event in client.events if event["method"] == "POST"]
    assert mutations == [
        "/api/workspace/create",
        "/api/workspace/activate",
        "/api/workspace/workflow-source-templates/replacement-drawer-handle/instances",
        "/api/workspace/workflow-source-templates/replacement-drawer-handle/setup/options",
    ]
    assert not any(
        "accept" in path or "/run" in path or "proposal" in path for path in mutations
    )


def test_checkpoint_logical_identity_only_normalizes_platform_ids(tmp_path):
    first = checkpoint.prepare(FakeClient(tmp_path / "one", "t" + "a" * 24))
    second = checkpoint.prepare(FakeClient(tmp_path / "two", "t" + "b" * 24))
    assert first["workspace_id"] != second["workspace_id"]
    assert first["storage_digest"] != second["storage_digest"]
    assert first["logical_checkpoint_sha256"] == second["logical_checkpoint_sha256"]
    resource = tmp_path / "two/inputs" / ("t" + "b" * 24) / "scenario.json"
    resource.write_text("Different engineering input")
    second_client = FakeClient(tmp_path / "three", "t" + "c" * 24)
    changed_resource = tmp_path / "three/inputs" / second_client.token / "scenario.json"
    changed_resource.write_text("Different engineering input")
    changed = checkpoint.prepare(second_client)
    assert first["logical_checkpoint_sha256"] != changed["logical_checkpoint_sha256"]


@pytest.mark.parametrize(
    "alteration,message",
    [
        ("version", "predeclared"),
        ("engineering", "template expansion"),
        ("tool", "missing-tools"),
    ],
)
def test_changed_subject_or_readiness_cannot_qualify_checkpoint(
    tmp_path, alteration, message
):
    client = FakeClient(tmp_path, alteration=alteration)
    with pytest.raises(RuntimeError, match=message):
        checkpoint.prepare(client)
    if alteration == "version":
        assert not any(event["method"] == "POST" for event in client.events)


def test_native_bootstrap_uses_cookie_session_without_bearer_or_secret_recording():
    client = checkpoint.NativeClient()
    calls = []

    class Response:
        status = 200

        def __enter__(self):
            return self

        def __exit__(self, *_):
            pass

        def geturl(self):
            return checkpoint.ORIGIN + "/"

        def read(self, _):
            return b"native document"

    class Opener:
        def open(self, request, timeout):
            calls.append(request)
            assert timeout == 30
            return Response()

    client.opener = Opener()
    client.request("/", document=True)
    request = calls[0]
    assert request.get_header("Origin") == checkpoint.ORIGIN
    assert request.get_header("Sec-fetch-mode") == "navigate"
    assert request.get_header("Authorization") is None
    assert client.events == [{"method": "GET", "path": "/", "status": 200}]
    assert "cookie" not in json.dumps(client.events).lower()


def test_resource_symlink_cannot_enter_comparison(tmp_path):
    client = FakeClient(tmp_path)
    directory = tmp_path / "inputs" / client.token
    (directory / "external.txt").symlink_to(tmp_path / "outside.txt")
    with pytest.raises(RuntimeError, match="symlink"):
        checkpoint.prepare(client)


def test_saved_instruction_policy_is_retained_in_logical_identity(tmp_path):
    first = checkpoint.prepare(FakeClient(tmp_path / "one"))
    changed = FakeClient(tmp_path / "two")
    changed.instructions["assets"][0]["body"] = "Different saved engineering policy"
    changed.instructions["assets"][0]["body_digest"] = checkpoint.digest(
        b"Different saved engineering policy"
    )
    second = checkpoint.prepare(changed)
    assert first["logical_checkpoint_sha256"] != second["logical_checkpoint_sha256"]
    assert (
        first["logical_checkpoint"]["instantiated_source_normalized_sha256"]
        != second["logical_checkpoint"]["instantiated_source_normalized_sha256"]
    )
    assert first["instruction_defaults"]["profile_version"] == "1.2.1"
    assert first["instruction_defaults"]["origin"] == "packaged"


@pytest.mark.parametrize(
    "alteration", ["body-digest", "different-policy", "extra-field"]
)
def test_unverified_policy_changes_cannot_be_normalized_away(tmp_path, alteration):
    client = FakeClient(tmp_path)
    source = SOURCE.replace("__instance__", client.token).replace(
        "__input_root__", "inputs/" + client.token
    )
    defaults = {
        "instructions": client.instructions,
        "digest": checkpoint.canonical_digest(client.instructions),
        "origin": "packaged",
    }
    saved = copy.deepcopy(client.instructions)
    if alteration == "body-digest":
        defaults["instructions"]["assets"][0]["body_digest"] = "0" * 64
        defaults["digest"] = checkpoint.canonical_digest(defaults["instructions"])
        saved = copy.deepcopy(defaults["instructions"])
    elif alteration == "different-policy":
        saved["profile_version"] = "different"
    lines = source.splitlines(keepends=True)
    lines.insert(
        2, "  instructions: " + json.dumps(saved, separators=(",", ":")) + "\n"
    )
    if alteration == "extra-field":
        lines.insert(3, '  purpose: "Changed engineering purpose"\n')
    with pytest.raises(RuntimeError):
        checkpoint.verify_source_snapshot(
            SOURCE, "".join(lines), client.token, defaults
        )


def test_existing_checkpoint_diagnosis_uses_get_only(tmp_path):
    client = FakeClient(tmp_path)
    document = client.request("/fixture/instances", {})
    client.events.clear()
    original = client.request

    def read_existing(path, body=None, **kwargs):
        if path == "/api/workspace/list":
            client.events.append({"method": "GET", "path": path})
            return {
                "workspaces": [
                    {
                        "workspace_id": "workspace-" + client.token,
                        "session_id": "session-" + client.token,
                        "workspace_name": "Handle beta checkpoint",
                        "local_path": str(tmp_path),
                    }
                ]
            }
        if path.startswith("/api/workspace/workflow-sources?"):
            client.events.append({"method": "GET", "path": path})
            return document
        assert body is None
        return original(path, **kwargs)

    client.request = read_existing
    result = checkpoint.inspect_existing(client)
    assert result["instruction_defaults"]["origin"] == "packaged"
    assert all(event["method"] == "GET" for event in client.events)
    assert "retried mutations" in result["scope"]
