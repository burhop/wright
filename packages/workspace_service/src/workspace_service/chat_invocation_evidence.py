"""Bounded immutable request sidecars for an already-owned workspace chat session.

This observes a request. It does not own chat history, model execution or action
authority and cannot replay a turn.
"""

import asyncio
from pathlib import Path

from core.process_validation import canonical_digest, canonical_json
from core.redaction import redact_mapping
from data_vault.process_ui_artifacts import ImmutableFileSet

from .workspace_path import WorkspacePath


class ChatInvocationRecorder:
    def __init__(self, service, *, workspace_id, workspace_dir, session_id, request_id):
        if any(
            not isinstance(value, str) or not value or len(value) > 256
            for value in (workspace_id, session_id, request_id)
        ):
            raise ValueError("A scoped chat request identity is required")
        self.service = service
        self.workspace_id, self.workspace_dir = workspace_id, workspace_dir
        self.session_id, self.request_id = session_id, request_id
        self.identities = {
            "workspace_id": workspace_id,
            "session_id": session_id,
            "request_id": request_id,
        }
        self.paths = WorkspacePath(workspace_dir)
        self.prefix = (
            ".wright/chat-invocations/"
            + canonical_digest(session_id)
            + "/"
            + canonical_digest(request_id)
        )
        self.count = 0
        self.receipts = []

    def _scope(self):
        current = self.service.lifecycle.get_by_session(self.session_id)
        if not current or current.get("workspace_id") != self.workspace_id:
            raise ValueError("The chat session is outside its captured workspace")
        root = self.service.ensure_workspace_path_safe(str(current["local_path"]))
        if Path(root).resolve() != self.paths.root:
            raise ValueError("The chat workspace binding changed")

    async def observe(self, invocation):
        self._scope()
        codex = isinstance(invocation, dict) and (
            invocation.get("schema_version") == "wright.codex-client-evidence/1"
            and invocation.get("capture_scope") == "app_server_sdk_call"
            and invocation.get("phase")
            in {
                "prepared",
                "sdk_call_started",
                "acknowledged",
                "permission_denied",
                "unclaimed_reply",
                "notification",
                "runtime_notice",
                "gateway_request",
                "gateway_result",
            }
            and isinstance(invocation.get("method"), str)
            and len(invocation["method"]) <= 160
            and isinstance(invocation.get("fields"), dict)
        )
        hermes = isinstance(invocation, dict) and (
            invocation.get("schema_version") == "wright.workflow-invocation/1"
            and invocation.get("operation") == "hermes-chat-http"
            and invocation.get("capture_scope") == "primary_adapter_request"
            and isinstance(invocation.get("request_fields"), dict)
            and invocation["request_fields"].get("session_id") == self.session_id
        )
        if not (codex or hermes) or self.count >= (384 if codex else 4):
            raise ValueError("Invalid scoped chat invocation evidence")
        raw = canonical_json(
            {"scope": self.identities, "invocation": redact_mapping(invocation)}
        ).encode()
        if len(raw) > 2_097_152:
            raise ValueError("Chat invocation evidence exceeds its bound")
        self.count += 1
        relative = self.prefix + f"/invocation-{self.count}"
        root = self.paths.resolve(relative)
        digest = await asyncio.to_thread(
            ImmutableFileSet(root, maximum_bytes=2_097_152, maximum_files=1).publish,
            {"invocation.json": raw},
        )
        self.receipts.append({"path": relative, "inventory_digest": digest})

    def read(self, receipt):
        self._scope()
        path = receipt.get("path", "")
        if path not in {
            self.prefix + f"/invocation-{index}" for index in range(1, 385)
        }:
            raise ValueError("Chat invocation evidence is outside this request")
        files = ImmutableFileSet(
            self.paths.resolve(path), maximum_bytes=2_097_152, maximum_files=1
        ).read(receipt["inventory_digest"])
        import json

        record = json.loads(files["invocation.json"])
        if record["scope"] != self.identities:
            raise ValueError("Chat invocation evidence has another owner")
        return record
