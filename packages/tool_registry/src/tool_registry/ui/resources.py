from __future__ import annotations

import asyncio
import base64
import hashlib
import json
import time
from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from typing import Any, Protocol

from ..gateway_models import GatewayError, GatewayErrorCode, GatewaySessionContext
from ..models import McpUiResourceMetadata


class McpUiResourceReader(Protocol):
    def connection_id(self, server_id: str) -> str: ...

    async def list_resources(self, server_id: str) -> Mapping[str, Any]: ...

    async def read_resource(
        self, server_id: str, uri: str
    ) -> Mapping[str, Any]: ...

    async def subscribe_resource(self, server_id: str, uri: str) -> None: ...


@dataclass(frozen=True, slots=True)
class McpUiBinding:
    gateway_session_id: str
    workspace_id: str
    server_id: str
    server_connection_id: str
    upstream_resource_uri: str
    content_hash: str
    source_version: str
    media_type: str
    content: str | bytes
    metadata: McpUiResourceMetadata
    subscribed: bool


@dataclass(frozen=True, slots=True)
class _CachedBinding:
    binding: McpUiBinding
    expires_at: float


class McpUiResourceStore:
    """Session/server-scoped, content-addressed projection of child UI resources."""

    def __init__(
        self,
        reader: McpUiResourceReader,
        *,
        cache_ttl: float = 300.0,
        maximum_content_bytes: int = 5 * 1024 * 1024,
    ) -> None:
        if cache_ttl <= 0 or maximum_content_bytes <= 0:
            raise ValueError("MCP UI resource cache limits must be positive")
        self.reader = reader
        self.cache_ttl = cache_ttl
        self.maximum_content_bytes = maximum_content_bytes
        self._cache: dict[tuple[str, str, str, str, str], _CachedBinding] = {}
        self._listing_meta: dict[tuple[str, str, str], dict[str, Mapping[str, Any]]] = {}
        self._subscriptions: set[tuple[str, str, str, str, str]] = set()
        self._locks: dict[tuple[str, str, str, str, str], asyncio.Lock] = {}
        set_invalidator = getattr(reader, "set_invalidator", None)
        if callable(set_invalidator):
            set_invalidator(self.invalidate)

    async def read(
        self,
        session: GatewaySessionContext,
        server_id: str,
        uri: str,
        *,
        subscribe: bool = True,
    ) -> McpUiBinding:
        self._validate_uri(uri)
        connection_id = self.reader.connection_id(server_id)
        if not connection_id:
            raise GatewayError(
                GatewayErrorCode.CHILD_UNAVAILABLE,
                "MCP server connection is unavailable",
            )
        key = (
            session.workspace_id,
            session.session_id,
            server_id,
            connection_id,
            uri,
        )
        lock = self._locks.setdefault(key, asyncio.Lock())
        async with lock:
            cached = self._cache.get(key)
            if cached is not None and cached.expires_at > time.monotonic():
                return cached.binding
            listing_metadata = await self._listing_metadata(
                session,
                server_id,
                connection_id,
                uri,
            )
            result = await self.reader.read_resource(server_id, uri)
            content_item = self._content_item(result, uri)
            media_type = str(
                content_item.get("mimeType")
                or content_item.get("mime_type")
                or "application/octet-stream"
            )
            content = self._content_value(content_item)
            content_bytes = (
                content.encode("utf-8") if isinstance(content, str) else content
            )
            if len(content_bytes) > self.maximum_content_bytes:
                raise GatewayError(
                    GatewayErrorCode.INVALID_OUTPUT,
                    "MCP UI resource exceeds the configured content limit",
                )
            raw_content_meta = content_item.get("_meta")
            content_meta = (
                dict(raw_content_meta) if isinstance(raw_content_meta, Mapping) else {}
            )
            metadata = McpUiResourceMetadata.merge(
                listing_metadata,
                content_meta,
            )
            digest = hashlib.sha256()
            digest.update(uri.encode("utf-8"))
            digest.update(b"\0")
            digest.update(media_type.encode("utf-8"))
            digest.update(b"\0")
            digest.update(content_bytes)
            digest.update(b"\0")
            digest.update(
                json.dumps(
                    metadata.upstream,
                    sort_keys=True,
                    separators=(",", ":"),
                    default=str,
                ).encode("utf-8")
            )
            content_hash = digest.hexdigest()
            subscription_key = key
            subscribed = subscription_key in self._subscriptions
            if subscribe and not subscribed:
                try:
                    await self.reader.subscribe_resource(server_id, uri)
                except (NotImplementedError, RuntimeError):
                    subscribed = False
                else:
                    self._subscriptions.add(subscription_key)
                    subscribed = True
            binding = McpUiBinding(
                gateway_session_id=session.session_id,
                workspace_id=session.workspace_id,
                server_id=server_id,
                server_connection_id=connection_id,
                upstream_resource_uri=uri,
                content_hash=content_hash,
                source_version=content_hash,
                media_type=media_type,
                content=content,
                metadata=metadata,
                subscribed=subscribed,
            )
            self._cache[key] = _CachedBinding(
                binding,
                time.monotonic() + self.cache_ttl,
            )
            return binding

    def invalidate(
        self,
        *,
        server_connection_id: str,
        uri: str | None = None,
    ) -> int:
        targets = [
            key
            for key in self._cache
            if key[3] == server_connection_id and (uri is None or key[4] == uri)
        ]
        for key in targets:
            self._cache.pop(key, None)
        listing_targets = [
            key for key in self._listing_meta if key[2] == server_connection_id
        ]
        for key in listing_targets:
            self._listing_meta.pop(key, None)
        return len(targets)

    def close_session(self, session: GatewaySessionContext) -> None:
        targets = [
            key
            for key in self._cache
            if key[0] == session.workspace_id and key[1] == session.session_id
        ]
        for key in targets:
            self._cache.pop(key, None)
            self._subscriptions.discard(key)
            self._locks.pop(key, None)
        listing_targets = [
            key
            for key in self._listing_meta
            if key[0] == session.workspace_id and key[1] == session.session_id
        ]
        for key in listing_targets:
            self._listing_meta.pop(key, None)

    async def _listing_metadata(
        self,
        session: GatewaySessionContext,
        server_id: str,
        connection_id: str,
        uri: str,
    ) -> Mapping[str, Any]:
        key = (session.workspace_id, session.session_id, connection_id)
        metadata = self._listing_meta.get(key)
        if metadata is None:
            try:
                result = await self.reader.list_resources(server_id)
            except (NotImplementedError, RuntimeError):
                result = {}
            resources = result.get("resources")
            metadata = {}
            if isinstance(resources, Sequence) and not isinstance(resources, (str, bytes)):
                for item in resources:
                    if not isinstance(item, Mapping) or not isinstance(item.get("uri"), str):
                        continue
                    raw = item.get("_meta")
                    metadata[str(item["uri"])] = (
                        dict(raw) if isinstance(raw, Mapping) else {}
                    )
            self._listing_meta[key] = metadata
        return metadata.get(uri, {})

    @staticmethod
    def _content_item(result: Mapping[str, Any], uri: str) -> Mapping[str, Any]:
        raw = result.get("contents")
        if not isinstance(raw, Sequence) or isinstance(raw, (str, bytes)):
            raise GatewayError(
                GatewayErrorCode.INVALID_OUTPUT,
                "MCP resource response omitted contents",
            )
        for item in raw:
            if isinstance(item, Mapping) and item.get("uri") == uri:
                return item
        raise GatewayError(
            GatewayErrorCode.INVALID_OUTPUT,
            "MCP resource response did not match the requested URI",
        )

    @staticmethod
    def _content_value(item: Mapping[str, Any]) -> str | bytes:
        if isinstance(item.get("text"), str):
            return str(item["text"])
        if isinstance(item.get("blob"), str):
            try:
                return base64.b64decode(str(item["blob"]), validate=True)
            except ValueError as exc:
                raise GatewayError(
                    GatewayErrorCode.INVALID_OUTPUT,
                    "MCP resource blob is not valid base64",
                ) from exc
        raise GatewayError(
            GatewayErrorCode.INVALID_OUTPUT,
            "MCP resource content omitted text or blob",
        )

    @staticmethod
    def _validate_uri(uri: str) -> None:
        if not uri.startswith("ui://"):
            raise GatewayError(
                GatewayErrorCode.INVALID_INPUT,
                "MCP UI resource URI must use ui://",
            )
