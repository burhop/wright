import os
import time
import json
import re
from pathlib import Path
from typing import Any, AsyncIterator
import httpx
from httpx_sse import aconnect_sse
import structlog

from .base import (
    BaseAgentEngine,
    AgentStreamEvent,
    AgentChatRequest,
    AgentSessionInfo,
    AgentChatMessage,
    AgentCommand,
)
from .hermes_config import hermes_config_path, resolve_hermes_api_settings

logger = structlog.get_logger(__name__)


WRIGHT_SYSTEM_HINT = (
    "You are running inside Wright with MCP tools exposed through the "
    "wrightgateway. For Onshape requests, do not ask the user for document, "
    "workspace, or element IDs when they provided a document or part name. "
    "First use jarvisonshapemcp__search_documents or "
    "jarvisonshapemcp__list_documents to find the document. If there are "
    "multiple exact title matches, prefer the most recently modified one "
    "unless the user specified another date or version. Then inspect the "
    "document with jarvisonshapemcp__get_document_summary, "
    "jarvisonshapemcp__get_elements, or "
    "jarvisonshapemcp__find_part_studios before exporting with "
    "jarvisonshapemcp__export_part_studio or "
    "jarvisonshapemcp__export_assembly. Ask a clarifying question only when "
    "search results are ambiguous after you have searched."
)


def _gateway_unavailable_message(last_error: Exception | str | None) -> str:
    return (
        "Hermes API Server is not reachable. Start Hermes Gateway with "
        "`hermes gateway run`, or enable API_SERVER_ENABLED=true, "
        "API_SERVER_PORT=8642, and API_SERVER_KEY in %LOCALAPPDATA%\\hermes\\.env "
        "and restart Hermes Desktop/Gateway. "
        f"Last error: {last_error}"
    )


def _is_placeholder(value: str | None) -> bool:
    if not value:
        return False
    return value.strip().lower() in {
        "https://your-llm-endpoint/v1",
        "your-default-model",
        "sk-your-key-here",
    }


def _load_mapping_file(path: str | None) -> dict[str, Any]:
    if not path:
        return {}
    try:
        text = Path(path).read_text(encoding="utf-8", errors="ignore")
    except OSError:
        return {}

    try:
        loaded = json.loads(text)
        return loaded if isinstance(loaded, dict) else {}
    except json.JSONDecodeError:
        pass

    try:
        import yaml  # type: ignore

        loaded = yaml.safe_load(text)
        return loaded if isinstance(loaded, dict) else {}
    except Exception:
        return {}


def _unique_urls(urls: list[str]) -> list[str]:
    result = []
    for url in urls:
        cleaned = (url or "").strip()
        if cleaned and cleaned not in result:
            result.append(cleaned)
    return result


def _hermes_auth_path_for_config(config_path: str | None) -> Path | None:
    if not config_path:
        return None
    config_file = Path(config_path)
    return config_file.with_name("auth.json")


def _openai_codex_auth_is_present(config_path: str | None) -> bool:
    auth_path = _hermes_auth_path_for_config(config_path)
    if not auth_path or not auth_path.exists():
        return False

    auth = _load_mapping_file(str(auth_path))
    providers = auth.get("providers") if isinstance(auth.get("providers"), dict) else {}
    codex = providers.get("openai-codex") if isinstance(providers, dict) else None
    if isinstance(codex, dict):
        tokens = codex.get("tokens")
        if isinstance(tokens, dict) and str(tokens.get("access_token") or "").strip():
            return True

    pool = (
        auth.get("credential_pool")
        if isinstance(auth.get("credential_pool"), dict)
        else {}
    )
    entries = pool.get("openai-codex") if isinstance(pool, dict) else None
    if isinstance(entries, list):
        return any(
            isinstance(entry, dict)
            and str(
                entry.get("secret_fingerprint") or entry.get("access_token") or ""
            ).strip()
            for entry in entries
        )

    return False


class HermesAdapter(BaseAgentEngine):
    """Concrete implementation of BaseAgentEngine that proxies to Hermes Native API (Constitution §2)."""

    def __init__(self, base_url: str, api_key: str, db_path: str | None = None):
        settings = resolve_hermes_api_settings()
        self.base_url = (base_url or settings.base_url).rstrip("/")
        self.api_key = api_key or settings.api_key
        self.db_path = db_path
        self.headers = {"Content-Type": "application/json"}
        if self.api_key:
            self.headers["Authorization"] = f"Bearer {self.api_key}"
        self._active_clients = {}  # session_id -> httpx.AsyncClient

    def _candidate_base_urls(self) -> list[str]:
        """Return configured Hermes API URLs, preserving priority."""
        configured = [self.base_url]
        env_candidates = re.split(r"[,;]\s*", os.getenv("HERMES_API_CANDIDATES", ""))
        if os.getenv("HERMES_API_DISABLE_DEFAULT_CANDIDATES", "").strip().lower() in {
            "1",
            "true",
            "yes",
        }:
            default_candidates = []
        else:
            default_candidates = [
                "http://127.0.0.1:8642",
                "http://localhost:8642",
            ]

        candidates = []
        for url in configured + env_candidates + default_candidates:
            cleaned = (url or "").strip().rstrip("/")
            if cleaned and cleaned not in candidates:
                candidates.append(cleaned)
        return candidates

    def _llm_settings_from_config(self) -> dict[str, str] | None:
        config_path = hermes_config_path()
        config_exists = bool(config_path and Path(config_path).exists())
        config = _load_mapping_file(config_path)

        model = config.get("model") if isinstance(config.get("model"), dict) else {}
        providers = config.get("custom_providers")
        if not isinstance(providers, list):
            providers = []

        base_url = str(model.get("base_url") or "").strip()
        model_name = str(model.get("default") or "").strip()
        provider_name = str(model.get("provider") or "").strip()
        api_key = ""

        for provider in providers:
            if not isinstance(provider, dict):
                continue
            provider_url = str(provider.get("base_url") or "").strip()
            if not base_url and provider_url:
                base_url = provider_url
            if base_url and provider_url == base_url:
                api_key = str(provider.get("api_key") or "").strip()
                if not model_name:
                    model_name = str(provider.get("model") or "").strip()
                break

        env_base_url = os.getenv("LLM_API_URL", "").strip()
        env_health_url = os.getenv("LLM_HEALTH_URL", "").strip()
        env_api_key = os.getenv("LLM_API_KEY", "").strip()
        env_model = os.getenv("LLM_API_MODEL", "").strip()

        base_url = base_url or env_base_url
        api_key = api_key or env_api_key
        model_name = model_name or env_model

        if not (config_exists or base_url or env_health_url):
            return None

        return {
            "base_url": base_url,
            "health_url": env_health_url,
            "api_key": api_key,
            "model": model_name,
            "provider": provider_name,
            "config_path": config_path or "",
        }

    def _llm_probe_urls(self, base_url: str, health_url: str) -> list[str]:
        urls = []
        if health_url and not _is_placeholder(health_url):
            urls.append(health_url.rstrip("/"))

        cleaned = (base_url or "").strip().rstrip("/")
        if cleaned and not _is_placeholder(cleaned):
            if cleaned.endswith("/v1"):
                urls.append(f"{cleaned}/models")
                urls.append(f"{cleaned[:-3].rstrip('/')}/health")
            elif cleaned.endswith("/health"):
                urls.append(cleaned)
            else:
                urls.append(f"{cleaned}/health")
                urls.append(f"{cleaned}/v1/models")
        return _unique_urls(urls)

    async def check_llm_backend_health(self) -> dict:
        """Check the model provider configured for Hermes, not Hermes' facade."""
        start_time = time.perf_counter()
        settings = self._llm_settings_from_config()
        if settings is None:
            return {
                "state": "disconnected",
                "latencyMs": 0.0,
                "baseUrl": None,
                "error": "Hermes model base_url is not configured",
            }

        base_url = settings["base_url"]
        health_url = settings["health_url"]
        api_key = settings["api_key"]
        provider = settings["provider"].strip().lower()
        config_path = settings["config_path"]

        if provider == "openai-codex":
            if _openai_codex_auth_is_present(config_path):
                return {
                    "state": "connected",
                    "latencyMs": (time.perf_counter() - start_time) * 1000.0,
                    "baseUrl": base_url or "https://chatgpt.com/backend-api/codex",
                }
            return {
                "state": "disconnected",
                "latencyMs": (time.perf_counter() - start_time) * 1000.0,
                "baseUrl": base_url or "https://chatgpt.com/backend-api/codex",
                "error": "Hermes openai-codex credentials are not configured",
            }

        if _is_placeholder(base_url):
            return {
                "state": "disconnected",
                "latencyMs": 0.0,
                "baseUrl": base_url,
                "error": "LLM_API_URL is still a placeholder",
            }

        probe_urls = self._llm_probe_urls(base_url, health_url)
        if not probe_urls:
            return {
                "state": "disconnected",
                "latencyMs": 0.0,
                "baseUrl": base_url or None,
                "error": "Hermes model base_url is not configured",
            }

        headers = {"Accept": "application/json"}
        if (
            api_key
            and not _is_placeholder(api_key)
            and api_key.lower() not in {"not-needed", "none", "null"}
        ):
            headers["Authorization"] = f"Bearer {api_key}"

        last_error = None
        async with httpx.AsyncClient() as client:
            for url in probe_urls:
                try:
                    response = await client.get(url, headers=headers, timeout=2.0)
                    body_preview = response.text[:200].lower()
                    content_type = response.headers.get("content-type", "").lower()
                    is_html_shell = (
                        "text/html" in content_type
                        or "<!doctype html" in body_preview
                        or "<html" in body_preview
                    )
                    if 200 <= response.status_code < 300 and not is_html_shell:
                        return {
                            "state": "connected",
                            "latencyMs": (time.perf_counter() - start_time) * 1000.0,
                            "baseUrl": base_url,
                        }
                    if response.status_code == 405 and not is_html_shell:
                        return {
                            "state": "connected",
                            "latencyMs": (time.perf_counter() - start_time) * 1000.0,
                            "baseUrl": base_url,
                        }
                    if is_html_shell:
                        last_error = f"{url} returned HTML, not an LLM API"
                    elif response.status_code in {401, 403}:
                        last_error = f"{url} rejected the configured credentials with HTTP {response.status_code}"
                        break
                    else:
                        last_error = (
                            f"{url} HTTP {response.status_code}: {response.text[:200]}"
                        )
                except Exception as exc:
                    last_error = f"{url}: {exc}"

        return {
            "state": "disconnected",
            "latencyMs": (time.perf_counter() - start_time) * 1000.0,
            "baseUrl": base_url,
            "error": last_error or "LLM backend did not answer a health probe",
        }

    async def _request_with_fallback(
        self,
        method: str,
        path: str,
        *,
        timeout: float,
        json_body: dict | None = None,
    ) -> httpx.Response:
        """Try the configured Hermes API URL, then fallback candidates."""
        last_error: Exception | None = None
        async with httpx.AsyncClient() as client:
            for base_url in self._candidate_base_urls():
                try:
                    response = await client.request(
                        method,
                        f"{base_url}{path}",
                        json=json_body,
                        headers=self.headers,
                        timeout=timeout,
                    )
                    response.raise_for_status()
                    self.base_url = base_url
                    return response
                except Exception as exc:
                    last_error = exc
                    logger.debug(
                        "Hermes request failed",
                        method=method,
                        base_url=base_url,
                        path=path,
                        error=str(exc),
                    )

        if last_error:
            raise RuntimeError(_gateway_unavailable_message(last_error)) from last_error
        raise RuntimeError("No Hermes API candidates configured")

    async def check_health(self) -> dict:
        """Return {"state": "connected"|"disconnected", "latencyMs": float}."""
        import asyncio

        start_time = time.perf_counter()
        last_error = None
        for attempt in range(2):
            for base_url in self._candidate_base_urls():
                try:
                    async with httpx.AsyncClient() as client:
                        response = await client.get(
                            f"{base_url}/health", headers=self.headers, timeout=2.0
                        )
                        latency = (time.perf_counter() - start_time) * 1000.0
                        body_preview = response.text[:200].lower()
                        is_html_shell = (
                            "<!doctype html" in body_preview or "<html" in body_preview
                        )
                        if response.status_code == 200 and not is_html_shell:
                            self.base_url = base_url
                            return {
                                "state": "connected",
                                "latencyMs": latency,
                                "baseUrl": self.base_url,
                            }
                        if response.status_code == 200 and is_html_shell:
                            last_error = (
                                f"{base_url} returned HTML, not Hermes API health"
                            )
                        else:
                            last_error = f"{base_url} HTTP {response.status_code}: {response.text[:200]}"
                except Exception as e:
                    last_error = f"{base_url}: {e}"
                    logger.debug(
                        "Hermes health check attempt failed",
                        attempt=attempt + 1,
                        base_url=base_url,
                        error=str(e),
                    )
            if attempt == 0:
                await asyncio.sleep(0.5)
        return {
            "state": "disconnected",
            "latencyMs": 0.0,
            "baseUrl": self.base_url,
            "error": last_error,
        }

    def _to_epoch_ms(self, val) -> int:
        if not val:
            return 0
        if val < 10000000000:  # Seconds to milliseconds
            return int(val * 1000)
        return int(val)

    def _get_workspace_from_db(self, session_id: str) -> str | None:
        if not self.db_path or not os.path.exists(self.db_path):
            return None
        import sqlite3

        try:
            conn = sqlite3.connect(self.db_path)
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            cursor.execute(
                "SELECT local_path FROM engineering_workspaces WHERE session_id = ?",
                (session_id,),
            )
            row = cursor.fetchone()
            conn.close()
            if row:
                return row["local_path"]
        except Exception as e:
            logger.debug(
                "Failed to query workspace from database",
                session_id=session_id,
                error=str(e),
            )
        return None

    async def create_session(
        self, workspace: str | None = None, instructions: str | None = None
    ) -> AgentSessionInfo:
        """Create a new agent session."""
        payload = {}
        if workspace:
            payload["workspace"] = workspace
        if instructions:
            # Standard OpenAI system message import for native API
            payload["instructions"] = instructions

        response = await self._request_with_fallback(
            "POST",
            "/api/sessions",
            json_body=payload,
            timeout=10.0,
        )
        data = response.json()
        # Support both direct return or nested 'session' key if wrapper exists
        session = data.get("session", data)
        session_id = session.get("session_id", session.get("id"))
        if session_id is not None:
            session_id = str(session_id)
        return AgentSessionInfo(
            session_id=session_id,
            title=session.get("title") or "Untitled",
            created_at=self._to_epoch_ms(session.get("created_at", 0)),
            updated_at=self._to_epoch_ms(session.get("updated_at", 0)),
            message_count=session.get("message_count", 0),
            workspace=workspace or self._get_workspace_from_db(session_id),
        )

    async def list_sessions(self) -> list[AgentSessionInfo]:
        """List all sessions for this adapter's profile."""
        import asyncio

        for attempt in range(2):
            try:
                response = await self._request_with_fallback(
                    "GET",
                    "/api/sessions",
                    timeout=10.0,
                )
                data = response.json()
                sessions = (
                    data
                    if isinstance(data, list)
                    else (data.get("data") or data.get("sessions") or [])
                )

                result = []
                for s in sessions:
                    session_id = s.get("session_id", s.get("id"))
                    if not session_id:
                        continue
                    session_id = str(session_id)
                    result.append(
                        AgentSessionInfo(
                            session_id=session_id,
                            title=s.get("title") or "Untitled",
                            created_at=self._to_epoch_ms(s.get("created_at", 0)),
                            updated_at=self._to_epoch_ms(s.get("updated_at", 0)),
                            message_count=s.get("message_count", 0),
                            workspace=self._get_workspace_from_db(session_id),
                        )
                    )
                return result
            except Exception as e:
                logger.debug(
                    "Hermes list_sessions attempt %d failed: %s", attempt + 1, e
                )
                if attempt == 0:
                    await asyncio.sleep(0.5)
                else:
                    raise

    async def delete_session(self, session_id: str) -> bool:
        """Delete a session. Returns True if deleted."""
        try:
            response = await self._request_with_fallback(
                "DELETE",
                f"/api/sessions/{session_id}",
                timeout=10.0,
            )
            return response.status_code in (200, 204)
        except Exception:
            logger.exception("Failed to delete session %s", session_id)
        return False

    async def _build_messages(self, request: AgentChatRequest) -> list[dict]:
        """Fetch chat history and append the current user message to construct messages list."""
        history = await self.get_chat_history(request.session_id)
        messages = [{"role": "system", "content": WRIGHT_SYSTEM_HINT}]
        for msg in history:
            messages.append({"role": msg.role, "content": msg.content})

        # Determine the workspace path for the session and prefix the user message
        workspace_path = await self.get_session_workspace(request.session_id)
        message_content = request.message
        if workspace_path:
            message_content = f"[Workspace::v1: {workspace_path}] {message_content}"

        messages.append({"role": "user", "content": message_content})
        return messages

    async def stream_chat(
        self, request: AgentChatRequest
    ) -> AsyncIterator[AgentStreamEvent]:
        """Stream chat via Hermes native OpenAI-compatible API."""
        messages = await self._build_messages(request)
        session_id = request.session_id

        client = httpx.AsyncClient()
        self._active_clients[session_id] = client

        try:
            headers = {**self.headers, "X-Hermes-Session-Id": session_id}
            async with aconnect_sse(
                client,
                "POST",
                f"{self.base_url}/v1/chat/completions",
                json={
                    "model": "hermes",
                    "messages": messages,
                    "stream": True,
                    "session_id": session_id,
                },
                headers=headers,
                timeout=60.0,
            ) as event_source:
                event_source.response.raise_for_status()
                async for sse in event_source.aiter_sse():
                    event_type = sse.event
                    # hermes.tool.progress custom event
                    if event_type == "hermes.tool.progress":
                        try:
                            data = json.loads(sse.data)
                            yield AgentStreamEvent(type="progress", data=data)
                        except Exception:
                            logger.warn(
                                "Failed to parse hermes.tool.progress event data",
                                data=sse.data,
                            )
                    elif sse.data == "[DONE]":
                        yield AgentStreamEvent(type="stream_end", data={})
                    else:
                        try:
                            chunk = json.loads(sse.data)
                            choices = chunk.get("choices", [])
                            if not choices:
                                continue
                            delta = choices[0].get("delta", {})
                            if delta.get("content"):
                                yield AgentStreamEvent(
                                    type="token", data={"text": delta["content"]}
                                )
                            if delta.get("tool_calls"):
                                yield AgentStreamEvent(
                                    type="tool",
                                    data={"tool_calls": delta["tool_calls"]},
                                )
                        except Exception:
                            logger.warn(
                                "Failed to parse completion chunk data", data=sse.data
                            )
        except httpx.HTTPStatusError as exc:
            if exc.response.status_code in (502, 503):
                yield AgentStreamEvent(
                    type="error", data={"message": "LLM model unavailable"}
                )
            else:
                yield AgentStreamEvent(
                    type="error",
                    data={
                        "message": f"HTTP error {exc.response.status_code}: {exc.response.text}"
                    },
                )
        except Exception as exc:
            yield AgentStreamEvent(type="error", data={"message": str(exc)})
        finally:
            self._active_clients.pop(session_id, None)
            await client.aclose()

    async def get_session_workspace(self, session_id: str) -> str | None:
        """Retrieve the workspace path for a given session ID."""
        # Query local SQLite database first
        workspace = self._get_workspace_from_db(session_id)
        if workspace:
            return workspace

        # Fallback to native sessions API
        try:
            response = await self._request_with_fallback(
                "GET",
                f"/api/sessions/{session_id}",
                timeout=5.0,
            )
            data = response.json()
            return data.get("workspace")
        except Exception as e:
            logger.debug("Failed to query workspace for session from native API: %s", e)

        # Fallback to list
        try:
            sessions = await self.list_sessions()
            for s in sessions:
                if s.session_id == session_id:
                    return s.workspace
        except Exception:
            pass
        return None

    async def save_context(self, session_id: str, workspace_id: str) -> bool:
        """No-op for Hermes — context is persisted server-side automatically."""
        logger.debug(
            "save_context is a no-op for Hermes (session=%s, workspace=%s)",
            session_id,
            workspace_id,
        )
        return True

    async def load_context(self, session_id: str, workspace_id: str) -> dict | None:
        """No-op for Hermes — context is persisted server-side automatically."""
        logger.debug(
            "load_context is a no-op for Hermes (session=%s, workspace=%s)",
            session_id,
            workspace_id,
        )
        return None

    async def get_chat_history(self, session_id: str) -> list[AgentChatMessage]:
        """Retrieve chat history from Hermes Native API."""
        try:
            response = await self._request_with_fallback(
                "GET",
                f"/api/sessions/{session_id}/messages",
                timeout=10.0,
            )
            data = response.json()
            messages = (
                data
                if isinstance(data, list)
                else (data.get("data") or data.get("messages") or [])
            )

            result = []
            for idx, msg in enumerate(messages):
                role = msg.get("role", "assistant")
                if role == "system":
                    continue

                msg_id = msg.get("id", msg.get("message_id", ""))
                if msg_id is not None:
                    msg_id = str(msg_id)
                else:
                    msg_id = ""
                if not msg_id:
                    msg_id = f"msg-{session_id}-{idx}"

                content = msg.get("content", "")
                if isinstance(content, list):
                    parts = []
                    for item in content:
                        if isinstance(item, str):
                            parts.append(item)
                        elif isinstance(item, dict) and isinstance(
                            item.get("text"), str
                        ):
                            parts.append(item["text"])
                    content = "".join(parts)
                elif not isinstance(content, str):
                    content = str(content) if content is not None else ""

                timestamp = self._to_epoch_ms(
                    msg.get("timestamp", msg.get("created_at", 0))
                )

                result.append(
                    AgentChatMessage(
                        id=msg_id,
                        role=role,
                        content=content,
                        timestamp=timestamp,
                        trace_id=msg.get("trace_id"),
                    )
                )
            return result
        except Exception as e:
            logger.error(
                "Failed to fetch chat history for session %s: %s", session_id, e
            )
            return []

    async def get_commands(self) -> list[AgentCommand]:
        """Retrieve the available slash commands from Hermes."""
        try:
            response = await self._request_with_fallback(
                "GET",
                "/api/commands",
                timeout=5.0,
            )
            data = response.json()
            cmds = (
                data
                if isinstance(data, list)
                else (data.get("data") or data.get("commands") or [])
            )
            return [
                AgentCommand(name=c["name"], description=c.get("description", ""))
                for c in cmds
            ]
        except Exception as e:
            logger.debug(
                "Failed to fetch commands from Hermes API, falling back to local registry file: %s",
                e,
            )
            try:
                commands_path = os.path.join(
                    os.path.dirname(__file__), "hermes-slash-commands.json"
                )
                if os.path.exists(commands_path):
                    with open(commands_path, "r") as f:
                        data = json.load(f)
                        cmds = data.get("flat", []) if isinstance(data, dict) else data
                        return [
                            AgentCommand(
                                name=c["name"], description=c.get("description", "")
                            )
                            for c in cmds
                        ]
            except Exception as le:
                logger.error("Failed to load local commands fallback: %s", le)
            return []

    async def cancel_chat(self, session_id: str) -> bool:
        """Cancel an active response stream by aborting the client request."""
        client = self._active_clients.get(session_id)
        if client:
            try:
                await client.aclose()
                return True
            except Exception as e:
                logger.error("Error closing http client on cancellation", error=str(e))
        return False
