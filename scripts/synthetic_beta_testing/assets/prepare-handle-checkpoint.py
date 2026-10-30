"""Declared technical checkpoint creation; never customer observation evidence.

Run inside a fresh guest after normal candidate installation. Uses the native
browser bootstrap and existing workspace/template APIs. It grants no source
acceptance, engineering review, execution, provider or dispatch authority.
"""

from __future__ import annotations

import argparse
import hashlib
import http.cookiejar
import http.client
import json
from pathlib import Path
import re
import socket
import urllib.error
import urllib.parse
import urllib.request
import uuid


ORIGIN = "http://wright.localhost:8000"
TEMPLATE_ID = "replacement-drawer-handle"
TEMPLATE_VERSION = "1.0.3"
TEMPLATE_SHA256 = "9b4d35cb7fd746b3482535df5f1263d61b21e501f868228488c5522bad2cacb2"
WORKFLOW_PATH = "workflows/replace-a-broken-drawer-handle.workflow.wflow"
MAX_BYTES = 8 * 1024**2


def digest(value):
    return hashlib.sha256(value).hexdigest()


def canonical_digest(value):
    return digest(
        json.dumps(
            value,
            sort_keys=True,
            separators=(",", ":"),
            ensure_ascii=False,
            allow_nan=False,
        ).encode()
    )


def verify_source_snapshot(template_source, actual, token, defaults):
    """Preserve original engineering bytes and the backend's saved default policy."""
    instructions = defaults.get("instructions", {})
    if (
        instructions.get("schema_version") != "wright.workflow-instructions/1"
        or defaults.get("digest") != canonical_digest(instructions)
        or defaults.get("origin") != "packaged"
        or not instructions.get("assets")
    ):
        raise RuntimeError(
            "Checkpoint instruction defaults differ from the packaged contract"
        )
    for asset in instructions["assets"]:
        if not isinstance(asset.get("body"), str) or asset.get("body_digest") != digest(
            asset["body"].encode()
        ):
            raise RuntimeError("Checkpoint instruction asset body identity is invalid")
    expected = template_source.replace("__instance__", token).replace(
        "__input_root__", f"inputs/{token}"
    )
    lines = actual.splitlines(keepends=True)
    index = next(
        (i for i, line in enumerate(lines) if line.strip() == f"workflow {token}"), -1
    )
    if (
        index < 0
        or index + 1 >= len(lines)
        or not lines[index + 1].startswith("  instructions: ")
    ):
        raise RuntimeError("Created instance omitted its saved instruction defaults")
    saved_line = lines[index + 1]
    if json.loads(saved_line.removeprefix("  instructions: ")) != instructions:
        raise RuntimeError("Created instance saved different instruction policy")
    if "".join(lines[: index + 1] + lines[index + 2 :]) != expected:
        raise RuntimeError(
            "Created instance differs from the exact declared template expansion"
        )
    normalized = template_source.splitlines(keepends=True)
    position = next(
        i
        for i, line in enumerate(normalized)
        if line.strip() == "workflow __instance__"
    )
    normalized.insert(position + 1, saved_line)
    return digest("".join(normalized).encode())


class _NativeConnection(http.client.HTTPConnection):
    """Use native loopback without depending on desktop browser DNS handling."""

    def connect(self):
        if self.host != "wright.localhost" or self.port != 8000:
            raise RuntimeError(
                "Checkpoint HTTP transport is confined to the native guest origin"
            )
        self.sock = socket.create_connection(("127.0.0.1", 8000), self.timeout)


class _NativeHandler(urllib.request.HTTPHandler):
    def http_open(self, request):
        return self.do_open(_NativeConnection, request)


class _NoRedirect(urllib.request.HTTPRedirectHandler):
    def redirect_request(self, request, response, code, message, headers, newurl):
        return None


class NativeClient:
    def __init__(self):
        self.cookies = (
            http.cookiejar.CookieJar()
        )  # Memory only; never persisted or printed.
        self.opener = urllib.request.build_opener(
            urllib.request.ProxyHandler({}),
            _NativeHandler(),
            _NoRedirect(),
            urllib.request.HTTPCookieProcessor(self.cookies),
        )
        self.events = []

    def request(self, path, body=None, *, document=False, binary=False):
        if not path.startswith("/") or path.startswith("//"):
            raise RuntimeError("Native checkpoint path is invalid")
        headers = {"Origin": ORIGIN, "Accept": "application/json"}
        if document:
            headers.update({"Sec-Fetch-Mode": "navigate", "Sec-Fetch-Dest": "document"})
        if body is not None:
            headers["Content-Type"] = "application/json"
        method = "POST" if body is not None else "GET"
        request = urllib.request.Request(
            ORIGIN + path,
            data=json.dumps(body).encode() if body is not None else None,
            headers=headers,
            method=method,
        )
        # No retry of mutations: an uncertain creation requires inspection first.
        try:
            with self.opener.open(request, timeout=30) as response:
                if (
                    urllib.parse.urlsplit(response.geturl()).netloc
                    != "wright.localhost:8000"
                ):
                    raise RuntimeError(
                        "Native checkpoint request redirected outside its origin"
                    )
                content = response.read(MAX_BYTES + 1)
                if len(content) > MAX_BYTES:
                    raise RuntimeError(
                        "Native checkpoint response exceeds the inspection budget"
                    )
                self.events.append(
                    {"method": method, "path": path, "status": response.status}
                )
        except urllib.error.HTTPError as error:
            # Do not echo headers, authentication cookies or arbitrary error bodies.
            raise RuntimeError(
                f"Native checkpoint request failed: {method} {path}, HTTP {error.code}"
            ) from None
        if document or binary:
            return content
        value = json.loads(content)
        if not isinstance(value, dict):
            raise RuntimeError(
                "Native checkpoint API returned an unexpected response shape"
            )
        return value


def resource_inventory(workspace_path, token):
    workspace = Path(workspace_path)
    if (
        not workspace.is_absolute()
        or workspace.resolve() != workspace
        or not workspace.is_dir()
    ):
        raise RuntimeError(
            "Returned managed workspace must be a real existing directory"
        )
    directory = workspace / "inputs" / token
    if directory.resolve() != directory or not directory.is_dir():
        raise RuntimeError("Template input directory is absent or redirected")
    result = []
    total = 0
    for path in sorted(directory.rglob("*")):
        if path.is_symlink() or path.resolve() != path:
            raise RuntimeError("Template resource uses a symlink")
        if path.is_dir():
            continue
        if not path.is_file() or len(result) >= 16:
            raise RuntimeError(
                "Template resource inventory exceeds its declared boundary"
            )
        size = path.stat().st_size
        if total + size > MAX_BYTES:
            raise RuntimeError("Template resources exceed the inspection budget")
        content = path.read_bytes()
        total += len(content)
        name = path.relative_to(directory).as_posix()
        result.append(
            {
                "path": f"inputs/{token}/{name}",
                "normalized_path": f"inputs/__instance__/{name}",
                "sha256": digest(content),
                "bytes": len(content),
            }
        )
    if not result:
        raise RuntimeError("Template supplied no input resources")
    return result


def prepare(client=None):
    client = NativeClient() if client is None else client
    client.request("/", document=True)
    # Verify the exact packaged subject before any workspace mutation.
    detail = client.request(
        f"/api/workspace/workflow-source-templates/{TEMPLATE_ID}?version={TEMPLATE_VERSION}"
    )["template"]
    source = detail.get("source")
    if (
        detail.get("template_id") != TEMPLATE_ID
        or detail.get("version") != TEMPLATE_VERSION
        or detail.get("source_digest") != TEMPLATE_SHA256
        or not isinstance(source, str)
        or digest(source.encode()) != TEMPLATE_SHA256
    ):
        raise RuntimeError(
            "Packaged handle template differs from the predeclared 1.0.3 subject"
        )
    preview = client.request(
        f"/api/workspace/workflow-source-templates/{TEMPLATE_ID}/preview?version={TEMPLATE_VERSION}",
        binary=True,
    )
    workspace = client.request(
        "/api/workspace/create", {"name": "Handle beta checkpoint"}
    )
    session_id = workspace["session_id"]
    workspace_id = workspace["workspace_id"]
    client.request("/api/workspace/activate", {"session_id": session_id})
    defaults = client.request(
        "/api/workspace/workflow-sources/instruction-defaults?"
        + urllib.parse.urlencode({"session_id": session_id})
    )
    instance = client.request(
        f"/api/workspace/workflow-source-templates/{TEMPLATE_ID}/instances",
        {
            "session_id": session_id,
            "template_version": TEMPLATE_VERSION,
            "expected_source_digest": TEMPLATE_SHA256,
            "workflow_path": WORKFLOW_PATH,
            "request_id": str(uuid.uuid4()),
        },
    )
    workflow_id = instance.get("workflow_id", "")
    if not re.fullmatch(r"workflow\.t[0-9a-f]{24}", workflow_id):
        raise RuntimeError("Unexpected platform-generated workflow identity")
    token = workflow_id.removeprefix("workflow.")
    actual = instance.get("source", "")
    normalized_source_sha256 = verify_source_snapshot(source, actual, token, defaults)
    expected_layout = json.loads(
        json.dumps(detail["layout"]).replace("__instance__", token)
    )
    if (
        instance.get("workspace_id") != workspace_id
        or instance.get("path") != WORKFLOW_PATH
        or instance.get("storage_digest") != digest(actual.encode())
        or instance.get("storage_revision") != 1
        or instance.get("metadata_authority") != "wright_host"
        or instance.get("layout") != expected_layout
    ):
        raise RuntimeError(
            "Created instance differs from the exact declared template expansion"
        )
    if instance.get("template") != {
        "template_id": TEMPLATE_ID,
        "version": TEMPLATE_VERSION,
        "source_digest": TEMPLATE_SHA256,
        "layout_digest": detail["layout_digest"],
    }:
        raise RuntimeError("Created instance has unexpected template lineage")
    scope = {
        "session_id": session_id,
        "path": WORKFLOW_PATH,
        "expected_storage_revision": instance["storage_revision"],
        "expected_storage_digest": instance["storage_digest"],
    }
    options = client.request(
        f"/api/workspace/workflow-source-templates/{TEMPLATE_ID}/setup/options", scope
    )
    tools = options.get("tools", {})
    if (
        options.get("workspace_id") != workspace_id
        or options.get("path") != WORKFLOW_PATH
        or options.get("workflow_id") != token
        or set(tools) != {"construction", "geometry", "slicer", "inspection"}
        or any(not isinstance(choices, list) or choices for choices in tools.values())
    ):
        raise RuntimeError(
            "Checkpoint is not the declared source-scoped, missing-tools starting state"
        )
    recipe = options.get("recipe", {})
    if (
        recipe.get("id") != "printed-handle-orca"
        or recipe.get("version") != "2"
        or not re.fullmatch(r"[0-9a-f]{64}", recipe.get("digest", ""))
        or options.get("workspace_mount") != workspace["local_path"]
    ):
        raise RuntimeError(
            "Checkpoint setup recipe or exact workspace mount is unexpected"
        )
    resources = resource_inventory(workspace["local_path"], token)
    required_names = set(re.findall(r"__input_root__/([A-Za-z0-9_./-]+)", source))
    observed_names = {
        item["normalized_path"].removeprefix("inputs/__instance__/")
        for item in resources
    }
    if not required_names.issubset(observed_names):
        raise RuntimeError(
            "Template instance omitted a source-referenced input resource"
        )
    logical = {
        "template_id": TEMPLATE_ID,
        "version": TEMPLATE_VERSION,
        "source_sha256": TEMPLATE_SHA256,
        "instantiated_source_normalized_sha256": normalized_source_sha256,
        "instruction_defaults_digest": defaults["digest"],
        "instruction_profile_id": defaults["instructions"]["profile_id"],
        "instruction_profile_version": defaults["instructions"]["profile_version"],
        "layout_sha256": detail["layout_digest"],
        "preview_sha256": digest(preview),
        "recipe": options["recipe"],
        "requirements": options["requirements"],
        "profiles": options["profiles"],
        "tool_counts": {role: len(values) for role, values in sorted(tools.items())},
        "resources": [
            {key: value for key, value in item.items() if key != "path"}
            for item in resources
        ],
    }
    return {
        "schema": 1,
        "scope": "Declared prepared workspace; technical setup is not customer evidence or calibration credit",
        "workspace_id": workspace_id,
        "session_id": session_id,
        "workspace_path": workspace["local_path"],
        "source_path": WORKFLOW_PATH,
        "storage_revision": instance["storage_revision"],
        "storage_digest": instance["storage_digest"],
        "definition_revision": instance["definition_revision"],
        "workflow_id": workflow_id,
        "template": instance["template"],
        "instruction_defaults": {
            "digest": defaults["digest"],
            "revision": defaults.get("revision"),
            "origin": defaults["origin"],
            "profile_id": defaults["instructions"]["profile_id"],
            "profile_version": defaults["instructions"]["profile_version"],
            "snapshot_contract": "Existing backend materialize_new_workflow_instructions saves the complete current defaults in one workflow header field",
        },
        "resources": resources,
        "setup_scope": scope,
        "workspace_mount": options["workspace_mount"],
        "entry_url": ORIGIN
        + "/workspace/"
        + urllib.parse.quote(workspace_id, safe="")
        + "?"
        + urllib.parse.urlencode(
            {"workflow": "canonical", "workflowPath": WORKFLOW_PATH}
        ),
        "logical_checkpoint": logical,
        "logical_checkpoint_sha256": canonical_digest(logical),
        "normalization": "Only declared platform placeholders were normalized. Original template bytes match exactly; the single added workflow instruction line matches packaged API defaults and is retained in the normalized full-source identity. No engineering or policy fields were stripped.",
        "ui_preparation": "Setup dialog opening and Side selection remain explicit visible preparation steps, not completed by this script",
        "requests": client.events,
    }


def inspect_existing(client=None):
    """Replayable GET-only diagnosis after a failed factory; never recreate it."""
    client = NativeClient() if client is None else client
    client.request("/", document=True)
    rows = client.request("/api/workspace/list").get("workspaces", [])
    candidates = [
        row for row in rows if row.get("workspace_name") == "Handle beta checkpoint"
    ]
    if len(candidates) != 1:
        raise RuntimeError(
            "Read-only diagnosis requires exactly one existing checkpoint workspace"
        )
    workspace = candidates[0]
    query = urllib.parse.urlencode(
        {"session_id": workspace["session_id"], "path": WORKFLOW_PATH}
    )
    document = client.request("/api/workspace/workflow-sources?" + query)
    detail = client.request(
        f"/api/workspace/workflow-source-templates/{TEMPLATE_ID}?version={TEMPLATE_VERSION}"
    )["template"]
    defaults = client.request(
        "/api/workspace/workflow-sources/instruction-defaults?"
        + urllib.parse.urlencode({"session_id": workspace["session_id"]})
    )
    if (
        detail.get("version") != TEMPLATE_VERSION
        or digest(detail["source"].encode()) != TEMPLATE_SHA256
    ):
        raise RuntimeError(
            "Read-only diagnosis encountered a different packaged template"
        )
    match = re.search(r"^workflow (t[0-9a-f]{24})$", document["source"], re.MULTILINE)
    if match is None:
        raise RuntimeError("Existing checkpoint has an unexpected workflow identity")
    normalized = verify_source_snapshot(
        detail["source"], document["source"], match.group(1), defaults
    )
    return {
        "scope": "Read-only technical contract diagnosis; no customer evidence or retried mutations",
        "workspace": {
            key: workspace[key]
            for key in ("workspace_id", "session_id", "workspace_name", "local_path")
        },
        "document": document,
        "template": detail,
        "instruction_defaults": defaults,
        "normalized_source_sha256": normalized,
        "requests": client.events,
    }


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--technical-checkpoint-only", action="store_true", required=True
    )
    parser.add_argument("--output", required=True, type=Path)
    parser.add_argument(
        "--inspect-existing",
        action="store_true",
        help="GET-only diagnosis of an already-created checkpoint; create or change nothing",
    )
    args = parser.parse_args(argv)
    if not Path(
        "/var/lib/wright-beta/provisioned.json"
    ).is_file() or Path.home() != Path("/home/customer"):
        parser.error("Run only inside the disposable customer guest")
    if args.output.exists() or args.output.is_symlink():
        parser.error(
            "Preserve existing checkpoint evidence; choose a fresh output path"
        )
    result = inspect_existing() if args.inspect_existing else prepare()
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, indent=2) + "\n")
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
