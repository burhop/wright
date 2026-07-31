"""Explicit execution-scoped transport for Wright display envelopes."""

from __future__ import annotations

import json
import os
import uuid
from collections.abc import Callable, Iterator
from contextlib import contextmanager
from contextvars import ContextVar
from typing import Any
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

from .models import (
    DisplayConfigurationError,
    DisplayContractError,
    DisplayHandle,
    DisplayRepresentation,
    DisplayTransportError,
)


Transport = Callable[
    [str, str, dict[str, str], dict[str, Any]], tuple[int, dict[str, Any] | None]
]


def _http_transport(
    method: str,
    url: str,
    headers: dict[str, str],
    payload: dict[str, Any],
) -> tuple[int, dict[str, Any] | None]:
    request = Request(
        url,
        data=json.dumps(payload, allow_nan=False).encode("utf-8"),
        headers=headers,
        method=method,
    )
    try:
        with urlopen(request, timeout=30) as response:  # noqa: S310 - explicit endpoint
            data = response.read()
            return response.status, json.loads(data) if data else None
    except HTTPError as error:
        data = error.read()
        try:
            body = json.loads(data) if data else None
        except json.JSONDecodeError:
            body = {"message": "Wright returned a non-JSON error response."}
        return error.code, body
    except (OSError, URLError) as error:
        raise DisplayTransportError(
            "Wright could not be reached at the configured display endpoint. "
            "Run this file through Wright or verify WRIGHT_DISPLAY_ENDPOINT."
        ) from error


class DisplayClient:
    def __init__(
        self,
        *,
        endpoint: str,
        token: str,
        workspace_id: str,
        contract_version: int = 1,
        transport: Transport | None = None,
    ) -> None:
        if not endpoint.strip() or not token.strip() or not workspace_id.strip():
            raise DisplayConfigurationError(
                "endpoint, execution token, and workspace ID are required"
            )
        if contract_version != 1:
            raise DisplayContractError(
                f"Unsupported display contract {contract_version}; Wright SDK supports 1."
            )
        self.endpoint = endpoint.strip()
        self.token = token.strip()
        self.workspace_id = workspace_id.strip()
        self.contract_version = contract_version
        self.transport = transport or _http_transport
        self._revisions: dict[str, int] = {}

    def send(
        self,
        representations: tuple[DisplayRepresentation, ...],
        *,
        title: str | None,
        description: str,
        display_id: str | None,
        durability: str,
    ) -> DisplayHandle:
        logical_id = display_id or f"display-{uuid.uuid4().hex}"
        revision = self._revisions.get(logical_id, 0) + 1
        idempotency_key = f"display-{uuid.uuid4().hex}"
        payload = {
            "schemaVersion": self.contract_version,
            "displayId": logical_id,
            "revision": revision,
            "idempotencyKey": idempotency_key,
            **({"title": title} if title else {}),
            "durability": durability,
            "accessibility": {"description": description},
            "representations": [item.as_dict() for item in representations],
        }
        headers = {
            "Authorization": f"Bearer {self.token}",
            "Content-Type": "application/vnd.wright.display+json",
            "X-Wright-Workspace-ID": self.workspace_id,
            "X-Wright-Display-Contract": str(self.contract_version),
            "Idempotency-Key": idempotency_key,
        }
        status, body = self.transport("POST", self.endpoint, headers, payload)
        if status not in {200, 201} or not isinstance(body, dict):
            detail = body.get("message") if isinstance(body, dict) else None
            raise DisplayTransportError(
                str(detail)
                if detail
                else f"Wright rejected the display request with HTTP {status}."
            )
        response_schema = body.get("schemaVersion", 1)
        if response_schema != self.contract_version:
            raise DisplayContractError(
                f"Wright returned display contract {response_schema}; expected 1."
            )
        source = body.get("source") if isinstance(body.get("source"), dict) else {}
        returned_display_id = body.get("displayId", source.get("displayId"))
        artifact_revision = source.get("revision", body.get("revision"))
        surface_id = body.get("surfaceId")
        if (
            returned_display_id != logical_id
            or not isinstance(surface_id, str)
            or not isinstance(artifact_revision, int)
            or artifact_revision < 1
        ):
            raise DisplayContractError(
                "Wright returned malformed display identity or revision metadata."
            )
        self._revisions[logical_id] = artifact_revision
        return DisplayHandle(
            surface_id=surface_id,
            display_id=logical_id,
            revision=artifact_revision,
            title=title,
            _client=self,
            _description=description,
            _durability=durability,
        )


_ACTIVE_CLIENT: ContextVar[DisplayClient | None] = ContextVar(
    "wright_display_client", default=None
)


def _client_from_environment() -> DisplayClient:
    endpoint = os.getenv("WRIGHT_DISPLAY_ENDPOINT", "")
    token = os.getenv("WRIGHT_DISPLAY_TOKEN", "")
    workspace_id = os.getenv("WRIGHT_DISPLAY_WORKSPACE_ID", "")
    contract = os.getenv("WRIGHT_DISPLAY_CONTRACT", "1")
    if not endpoint or not token or not workspace_id:
        raise DisplayConfigurationError(
            "No Wright display execution is configured. Run the Python file "
            "through Wright, or explicitly set WRIGHT_DISPLAY_ENDPOINT, "
            "WRIGHT_DISPLAY_TOKEN, and WRIGHT_DISPLAY_WORKSPACE_ID for development."
        )
    try:
        version = int(contract)
    except ValueError as error:
        raise DisplayConfigurationError(
            "WRIGHT_DISPLAY_CONTRACT must be an integer."
        ) from error
    return DisplayClient(
        endpoint=endpoint,
        token=token,
        workspace_id=workspace_id,
        contract_version=version,
    )


def get_display_client() -> DisplayClient:
    return _ACTIVE_CLIENT.get() or _client_from_environment()


@contextmanager
def use_display_client(client: DisplayClient) -> Iterator[DisplayClient]:
    token = _ACTIVE_CLIENT.set(client)
    try:
        yield client
    finally:
        _ACTIVE_CLIENT.reset(token)
