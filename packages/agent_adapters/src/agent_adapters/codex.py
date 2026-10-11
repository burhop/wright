"""Experimental text-chat adapter; native-tool exception does not qualify roles."""

from __future__ import annotations

import asyncio
import hashlib
import json
import os
from pathlib import Path
import time
import uuid

from core.agent_platform import (
    AGENT_TURN_TERMINAL,
    AgentChatSessionRecord,
    AgentChatRepository,
    AgentPlatformConflict,
    AgentConfiguration,
    AgentPlatformSession,
    AgentPlatformTurn,
)
from core.process_validation import canonical_digest, canonical_json
from core.redaction import redact_mapping

from .base import (
    AgentChatMessage,
    AgentChatRequest,
    AgentInvocationCapabilities,
    AgentSessionInfo,
    AgentStreamEvent,
    BaseAgentEngine,
)
from .codex_policy import (
    CONFIG_OVERRIDES,
    GATEWAY_READ_TOOL,
    NO_TOOLS_REASON,
    RUNTIME_VERSION,
    SDK_VERSION,
)
from .codex_transport import (
    CodexRuntimeSettings,
    CodexSdkTransport,
    CodexTransportError,
)
from .workflow_instructions import embedded_instruction_set

CHAT_EXCEPTION = "wright.codex-native-chat-tools-exception/1"


def now_ms():
    return int(time.time() * 1000)


class CodexAdapter(BaseAgentEngine):
    """Own chat receipts only. Wright workflow and authoring owners are unchanged."""

    platform = "codex"

    def __init__(
        self,
        db_path: str,
        settings: CodexRuntimeSettings,
        *,
        repository: AgentChatRepository,
        model: str,
        effort: str = "high",
        auth_method: str = "chatgpt",
        transport_factory=CodexSdkTransport,
    ):
        if not model.strip() or len(model) > 160:
            raise ValueError("An explicit Codex model is required")
        if effort not in {"none", "minimal", "low", "medium", "high", "xhigh"}:
            raise ValueError("Unsupported Codex reasoning effort")
        if auth_method not in {"chatgpt", "apiKey", "fixture"}:
            raise ValueError("An explicit Codex authentication route is required")
        self.db_path, self.settings = db_path, settings
        self.model, self.effort, self.auth_method = model, effort, auth_method
        self.repository = repository
        self._factory = transport_factory
        self._transport = None
        self._start_lock = asyncio.Lock()
        # Serialize submissions and their observer ownership; cancellation is separate.
        self._chat_lock = asyncio.Lock()
        self._observer = None
        self._active = {}
        self._pending_sessions = set()
        self._cancel_requests = set()
        self._gateway_handler = None
        self._turn_ack = None
        self._loaded = set()
        self._empty_threads = set()

    async def _observe(self, record):
        if self._observer is not None:
            await self._observer(record)

    async def _client(self):
        async with self._start_lock:
            if self._transport is None:
                client = self._factory(
                    self.settings,
                    observer=self._observe,
                    tool_handler=self._gateway_call,
                )
                try:
                    await client.start()
                except BaseException:
                    await client.close()
                    raise
                self._transport = client
        return self._transport

    async def _gateway_call(self, params):
        denied = {
            "success": False,
            "contentItems": [
                {"type": "inputText", "text": "Wright gateway request denied."}
            ],
        }
        if self._turn_ack is None or self._gateway_handler is None:
            return denied
        async with asyncio.timeout(5):
            await self._turn_ack.wait()
        if (params["threadId"], params["turnId"]) not in self._active.values():
            return denied
        return await self._gateway_handler(params)

    async def close(self):
        async with self._start_lock:
            if self._transport is not None:
                await self._transport.close()
                self._transport = None
                self._loaded.clear()
                self._empty_threads.clear()

    async def _resolved(self):
        client = await self._client()
        config = (await client.request("config/read", {}))["config"]
        if config.get("mcp_servers"):
            raise ValueError("Codex chat may not load external MCP configuration")
        account = (await client.request("account/read", {})).get("account")
        if self.auth_method == "fixture":
            if account or config.get("model_provider") != "qualification":
                raise ValueError(
                    "Local qualification requires the explicit fixture provider"
                )
        elif not account or account.get("type") != self.auth_method:
            raise ValueError(
                "Codex authentication is missing or uses a different route"
            )
        elif self.auth_method == "chatgpt":
            # Public account identity from the private credential metadata, never
            # token bytes. SDK account/read exposes only email and plan type.
            auth = json.loads(
                (self.settings.state_root / "home" / "auth.json").read_text()
            )
            account_id = (auth.get("tokens") or {}).get("account_id")
            if not isinstance(account_id, str) or not account_id:
                raise ValueError("Codex lacks a stable isolated account identity")
            account = {**account, "identity_digest": canonical_digest(account_id)}
        models = (await client.request("model/list", {})).get("data", [])
        selected = next((row for row in models if row.get("model") == self.model), None)
        if selected is None:
            raise ValueError("The configured Codex model is not in the runtime catalog")
        efforts = {
            row["reasoningEffort"]
            for row in selected.get("supportedReasoningEfforts", [])
        }
        if self.effort not in efforts:
            raise ValueError("The configured Codex reasoning effort is unavailable")
        return client, config, account, selected

    async def check_health(self):
        started = time.monotonic()
        try:
            await self._resolved()
            return {
                "state": "connected",
                "latencyMs": (time.monotonic() - started) * 1000,
                "platform": "codex",
                "experimental": True,
                "nativeToolException": CHAT_EXCEPTION,
                "noTools": False,
            }
        except (CodexTransportError, ValueError, OSError, KeyError):
            return {
                "state": "disconnected",
                "latencyMs": (time.monotonic() - started) * 1000,
                "error": "Codex chat is not ready. Check its pinned installation, private authentication and explicit model/effort.",
                "platform": "codex",
                "experimental": True,
                "noTools": False,
            }

    check_llm_backend_health = check_health

    async def get_invocation_capabilities(self):
        return AgentInvocationCapabilities(
            adapter="codex", no_tools=False, reason=NO_TOOLS_REASON
        )

    async def get_models(self):
        client = await self._client()
        return (await client.request("model/list", {})).get("data", [])

    def _tool_configuration(self):
        return {
            "controls": CONFIG_OVERRIDES,
            "exception": CHAT_EXCEPTION,
            "gateway": GATEWAY_READ_TOOL if self.settings.gateway_enabled else None,
        }

    def _effective_configuration(self, config, account, selected):
        return {
            "configuration": redact_mapping(config),
            "account": canonical_digest(account),
            "model": selected,
            "effort": self.effort,
            "exception": CHAT_EXCEPTION,
        }

    def _configuration(self, instructions, config, account, selected):
        return AgentConfiguration(
            platform="codex",
            model_reference=self.model,
            runtime_version=RUNTIME_VERSION,
            client_version=SDK_VERSION,
            transport="app-server-sdk",
            auth_method=self.auth_method,
            instructions_digest=hashlib.sha256(instructions.encode()).hexdigest(),
            tools_digest=canonical_digest(self._tool_configuration()),
            effective_configuration_digest=canonical_digest(
                self._effective_configuration(config, account, selected)
            ),
        )

    async def create_session(self, workspace=None, instructions=None):
        if not workspace or not Path(workspace).is_absolute():
            raise ValueError("Codex chat requires an absolute Wright workspace path")
        async with self._chat_lock:
            client, config, account, selected = await self._resolved()
            instructions = (
                instructions or embedded_instruction_set().resolve("chat").text
            )
            configuration = self._configuration(instructions, config, account, selected)
            response = await client.request(
                "thread/start",
                {
                    "model": self.model,
                    "developerInstructions": instructions,
                    "ephemeral": False,
                },
            )
            thread = response["thread"]
            self._verify_thread(thread)
            record = AgentChatSessionRecord(
                session_id=f"codex-{uuid.uuid4()}",
                backend_thread_id=thread["id"],
                workspace_path=workspace,
                configuration=configuration,
                instructions=instructions,
                resolved_configuration_json=canonical_json(
                    self._effective_configuration(config, account, selected)
                ),
                tool_configuration_json=canonical_json(self._tool_configuration()),
                reasoning_effort=self.effort,
                account_digest=canonical_digest(account),
                created_at_ms=now_ms(),
            )
            self.repository.create_chat_session(record)
            self._loaded.add(record.backend_thread_id)
            self._empty_threads.add(record.backend_thread_id)
            return self._info(record)

    def _verify_thread(self, thread):
        if (
            thread.get("model") != self.model
            or thread.get("cliVersion") != RUNTIME_VERSION
        ):
            raise ValueError("Codex returned a different model/runtime identity")

    def _info(self, record):
        timestamp = record.created_at_ms // 1000
        return AgentSessionInfo(
            record.session_id,
            "Codex Chat",
            timestamp,
            timestamp,
            0,
            record.workspace_path,
        )

    async def list_sessions(self):
        return [self._info(row) for row in self.repository.list_chat_sessions("codex")]

    async def get_session_workspace(self, session_id):
        try:
            return self.repository.get_chat_session(session_id).workspace_path
        except KeyError:
            return None

    async def save_context(self, session_id, workspace_id):
        self._bind(self.repository.get_chat_session(session_id), workspace_id)
        return True

    async def load_context(self, session_id, workspace_id):
        record = self.repository.get_session(session_id)
        if record.workspace_id != workspace_id:
            raise AgentPlatformConflict(
                "Codex session belongs to a different workspace"
            )
        return {
            "session_id": session_id,
            "platform": "codex",
            "configuration_digest": record.configuration.digest,
        }

    def _bind(self, chat, workspace_id=None):
        # The workspace service owns the actual association; the adapter cannot invent one.
        binding = self.repository.resolve_workspace_binding(chat.session_id)
        if (
            binding.workspace_path != chat.workspace_path
            or binding.platform != "codex"
            or (workspace_id is not None and binding.workspace_id != workspace_id)
        ):
            raise AgentPlatformConflict(
                "Codex chat has no matching Wright workspace binding"
            )
        return self.repository.create_session(
            AgentPlatformSession(
                session_id=chat.session_id,
                workspace_id=binding.workspace_id,
                backend_thread_id=chat.backend_thread_id,
                configuration=chat.configuration,
                created_at_ms=chat.created_at_ms,
                gateway_binding_digest=(
                    self.repository.get_chat_gateway(chat.session_id).digest
                    if self.repository.get_chat_gateway(chat.session_id)
                    else None
                ),
            )
        )

    async def _resume(self, chat, instructions):
        client, config, account, selected = await self._resolved()
        current = self._configuration(instructions, config, account, selected)
        if current != chat.configuration or self.effort != chat.reasoning_effort:
            raise AgentPlatformConflict(
                "Frozen Codex chat configuration changed; create a new session"
            )
        self._bind(chat)
        if chat.backend_thread_id in self._loaded:
            return client
        response = await client.request(
            "thread/resume",
            {
                "threadId": chat.backend_thread_id,
                "model": self.model,
                "developerInstructions": chat.instructions,
            },
        )
        if response["thread"]["id"] != chat.backend_thread_id:
            raise AgentPlatformConflict("Codex resumed a different thread")
        self._verify_thread(response["thread"])
        self._loaded.add(chat.backend_thread_id)
        return client

    async def reconcile(self, session_id):
        chat = self.repository.get_chat_session(session_id)
        client = await self._client()
        response = await client.request(
            "thread/read", {"threadId": chat.backend_thread_id}
        )
        thread = response["thread"]
        if thread["id"] != chat.backend_thread_id:
            raise AgentPlatformConflict("Codex history belongs to a different thread")
        self._verify_thread(thread)
        for receipt in self.repository.unresolved_turns(session_id):
            if not receipt.backend_turn_id:
                raise AgentPlatformConflict(
                    "Unacknowledged Codex turn requires manual reconciliation; no replay"
                )
            turn = next(
                (
                    row
                    for row in thread.get("turns", [])
                    if row["id"] == receipt.backend_turn_id
                ),
                None,
            )
            if turn is None or turn["status"] not in AGENT_TURN_TERMINAL:
                raise AgentPlatformConflict("Codex turn is unresolved; no replay")
            self.repository.transition(
                receipt,
                receipt.model_copy(
                    update={
                        "status": turn["status"],
                        "updated_at_ms": now_ms(),
                    }
                ),
            )
        return thread

    async def get_chat_history(self, session_id):
        chat = self.repository.get_chat_session(session_id)
        # A thread/start acknowledgement precedes native history materialization.
        # Only this worker's known fresh thread can report an empty history.
        if chat.backend_thread_id in self._empty_threads:
            return []
        thread = await self.reconcile(session_id)
        messages = []
        for turn in thread.get("turns", []):
            timestamp = (turn.get("startedAt") or thread.get("createdAt") or 0) * 1000
            for item in turn.get("items", []):
                if item.get("type") == "userMessage":
                    text = "\n".join(
                        row["text"]
                        for row in item["content"]
                        if row.get("type") == "text"
                    )
                    role = "user"
                elif item.get("type") == "agentMessage":
                    text, role = item["text"], "assistant"
                else:
                    continue
                messages.append(AgentChatMessage(item["id"], role, text, timestamp))
        return messages

    async def delete_session(self, session_id):
        try:
            chat = self.repository.get_chat_session(session_id)
        except KeyError:
            return False
        await self.reconcile(session_id)
        client = await self._client()
        await client.request("thread/archive", {"threadId": chat.backend_thread_id})
        self.repository.archive_chat_session(session_id)
        return True

    async def get_commands(self):
        return []

    async def stream_chat(self, request: AgentChatRequest):
        if request.invocation_context is not None:
            yield AgentStreamEvent(
                "error", {"message": NO_TOOLS_REASON, "code": "CODEX_ROLE_UNAVAILABLE"}
            )
            yield AgentStreamEvent("stream_end", {"status": "failed"})
            return
        if request.attachments:
            yield AgentStreamEvent(
                "error",
                {
                    "message": "Codex pilot supports text only.",
                    "code": "CODEX_ATTACHMENTS_UNAVAILABLE",
                },
            )
            yield AgentStreamEvent("stream_end", {"status": "failed"})
            return
        async with self._chat_lock:
            receipt = None
            self._observer = request.invocation_observer
            self._gateway_handler = request.gateway_handler
            self._turn_ack = asyncio.Event()
            try:
                chat = self.repository.get_chat_session(request.session_id)
                if self.settings.gateway_enabled and (
                    request.gateway_handler is None
                    or self.repository.get_chat_gateway(request.session_id) is None
                ):
                    raise AgentPlatformConflict(
                        "The read-only Wright gateway binding is unavailable"
                    )
                instructions = (
                    embedded_instruction_set(request.instruction_set)
                    .resolve("chat")
                    .text
                )
                client = await self._resume(chat, instructions)
                if self.repository.unresolved_turns(request.session_id):
                    await self.reconcile(request.session_id)
                stamp = now_ms()
                receipt = self.repository.prepare_turn(
                    AgentPlatformTurn(
                        session_id=request.session_id,
                        attempt_id=request.trace_id or str(uuid.uuid4()),
                        message_digest=canonical_digest(request.message),
                        configuration_digest=chat.configuration.digest,
                        created_at_ms=stamp,
                        updated_at_ms=stamp,
                    )
                )
                if receipt.status != "prepared":
                    raise AgentPlatformConflict(
                        "Codex attempt is already submitted; no replay"
                    )
                # Mark uncertainty before handoff, including cancellation during submission.
                receipt = self.repository.transition(
                    receipt,
                    receipt.model_copy(
                        update={"status": "dispatching", "updated_at_ms": now_ms()}
                    ),
                )
                self._pending_sessions.add(request.session_id)
                self._empty_threads.discard(chat.backend_thread_id)
                response = await client.request(
                    "turn/start",
                    {
                        "threadId": chat.backend_thread_id,
                        "model": self.model,
                        "effort": self.effort,
                        "input": [{"type": "text", "text": request.message}],
                    },
                )
                receipt = self.repository.transition(
                    receipt,
                    receipt.model_copy(
                        update={
                            "status": "submitted",
                            "backend_turn_id": response["turn"]["id"],
                            "updated_at_ms": now_ms(),
                        }
                    ),
                )
                self._active[request.session_id] = (
                    chat.backend_thread_id,
                    receipt.backend_turn_id,
                )
                self._turn_ack.set()
                self._pending_sessions.discard(request.session_id)
                if request.session_id in self._cancel_requests:
                    await self.cancel_chat(request.session_id)
                delivered_items = set()
                async for event in client.events(receipt.backend_turn_id):
                    params, method = event["params"], event["method"]
                    await self._observe(
                        {
                            "schema_version": "wright.codex-client-evidence/1",
                            "capture_scope": "app_server_sdk_call",
                            "phase": "notification",
                            "method": method,
                            "fields": redact_mapping(params),
                        }
                    )
                    if params.get("threadId") not in {None, chat.backend_thread_id}:
                        raise AgentPlatformConflict(
                            "Codex event belongs to a different thread"
                        )
                    if method == "model/rerouted":
                        raise AgentPlatformConflict(
                            "Codex attempted a model reroute; no alternate model is accepted"
                        )
                    if method == "item/agentMessage/delta":
                        delivered_items.add(params.get("itemId"))
                        yield AgentStreamEvent("token", {"content": params["delta"]})
                    elif method in {"item/started", "item/completed"}:
                        item = params.get("item", {})
                        if (
                            method == "item/completed"
                            and item.get("type") == "agentMessage"
                            and item.get("id") not in delivered_items
                        ):
                            delivered_items.add(item.get("id"))
                            yield AgentStreamEvent("token", {"content": item["text"]})
                        if item.get("type") not in {
                            "userMessage",
                            "agentMessage",
                            "reasoning",
                        }:
                            yield AgentStreamEvent(
                                "tool",
                                {
                                    "platform": "codex",
                                    "native": True,
                                    "name": item.get("type", "Codex tool"),
                                    "call_id": item.get("id"),
                                    "event": method,
                                    "item": redact_mapping(item),
                                },
                            )
                    elif method == "turn/completed":
                        turn = params["turn"]
                        if (
                            turn["id"] != receipt.backend_turn_id
                            or turn["status"] not in AGENT_TURN_TERMINAL
                        ):
                            raise AgentPlatformConflict(
                                "Invalid Codex terminal receipt"
                            )
                        receipt = self.repository.transition(
                            receipt,
                            receipt.model_copy(
                                update={
                                    "status": turn["status"],
                                    "updated_at_ms": now_ms(),
                                }
                            ),
                        )
                        if receipt.status == "failed":
                            yield AgentStreamEvent(
                                "error",
                                {
                                    "message": "Codex turn failed.",
                                    "code": "CODEX_TURN_FAILED",
                                },
                            )
                        yield AgentStreamEvent(
                            "stream_end",
                            {
                                "status": receipt.status,
                                "turn_id": receipt.backend_turn_id,
                            },
                        )
            except asyncio.CancelledError:
                if receipt and receipt.status not in AGENT_TURN_TERMINAL:
                    await asyncio.shield(self.cancel_chat(request.session_id))
                    if receipt.status != "unknown":
                        self.repository.transition(
                            receipt,
                            receipt.model_copy(
                                update={"status": "unknown", "updated_at_ms": now_ms()}
                            ),
                        )
                raise
            except Exception as error:
                if (
                    receipt
                    and receipt.status not in AGENT_TURN_TERMINAL
                    and receipt.status != "unknown"
                ):
                    receipt = self.repository.transition(
                        receipt,
                        receipt.model_copy(
                            update={"status": "unknown", "updated_at_ms": now_ms()}
                        ),
                    )
                code = (
                    error.code
                    if isinstance(error, CodexTransportError)
                    else "CODEX_CHAT_REJECTED"
                )
                if isinstance(error, CodexTransportError):
                    # Restart only the owned transport; the durable unknown receipt
                    # still forbids replay and requires native reconciliation.
                    await self.close()
                yield AgentStreamEvent(
                    "error",
                    {
                        "message": "Codex chat failed or requires reconciliation. No turn was replayed.",
                        "code": code,
                    },
                )
                yield AgentStreamEvent(
                    "stream_end",
                    {
                        "status": "unknown"
                        if receipt and receipt.status not in AGENT_TURN_TERMINAL
                        else "failed"
                    },
                )
            finally:
                self._active.pop(request.session_id, None)
                self._pending_sessions.discard(request.session_id)
                self._cancel_requests.discard(request.session_id)
                self._observer = None
                self._gateway_handler = None
                self._turn_ack.set()
                self._turn_ack = None

    async def cancel_chat(self, session_id):
        if session_id in self._pending_sessions:
            self._cancel_requests.add(session_id)
            return True  # Intent accepted; interruption awaits the backend turn ID.
        active = self._active.get(session_id)
        if active is None:
            chat = self.repository.get_chat_session(session_id)
            receipts = self.repository.unresolved_turns(session_id)
            if not receipts or not receipts[0].backend_turn_id:
                return False
            active = chat.backend_thread_id, receipts[0].backend_turn_id
        client = await self._client()
        await client.request(
            "turn/interrupt", {"threadId": active[0], "turnId": active[1]}
        )
        return True  # Acknowledgement only; terminal event/history owns the outcome.


def create_codex_engine(db_path, *, repository: AgentChatRepository):
    if os.getenv("WRIGHT_CODEX_CHAT_EXPERIMENTAL") != "1":
        raise ValueError(
            "Enable WRIGHT_CODEX_CHAT_EXPERIMENTAL=1 for the documented native-tool chat exception"
        )
    root, model = os.getenv("WRIGHT_CODEX_STATE_ROOT"), os.getenv("WRIGHT_CODEX_MODEL")
    if not root or not model:
        raise ValueError(
            "Codex requires WRIGHT_CODEX_STATE_ROOT and WRIGHT_CODEX_MODEL"
        )
    auth_method = os.getenv("WRIGHT_CODEX_AUTH_METHOD") or "chatgpt"
    if auth_method != "chatgpt":
        raise ValueError(
            "Only ChatGPT authentication is qualified for the Codex chat pilot; no billing route was substituted"
        )
    if (Path(root) / "home" / "config.toml").exists():
        raise ValueError(
            "The isolated Codex pilot home must not load a user configuration profile"
        )
    if os.name == "nt":
        raise ValueError(
            "Codex chat is gated on native Windows pending descendant cleanup and isolation qualification"
        )
    return CodexAdapter(
        db_path,
        CodexRuntimeSettings(
            Path(root),
            python=Path(os.getenv("WRIGHT_CODEX_PYTHON") or os.sys.executable),
            gateway_enabled=True,
        ),
        repository=repository,
        model=model,
        effort=os.getenv("WRIGHT_CODEX_EFFORT") or "high",
        auth_method=auth_method,
    )
