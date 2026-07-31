"""Data-plane-only bootstrap routes for isolated Workspace Surface origins."""

from __future__ import annotations

import base64
import hashlib
from typing import Annotated

from fastapi import APIRouter, Depends, Header, HTTPException, Response
from pydantic import BaseModel, ConfigDict, Field

from api.composition import surface_application
from workspace_service.surfaces.presentation_tokens import (
    PresentationTokenError,
    PresentationTokenService,
)


router = APIRouter()

_BOOTSTRAP_SCRIPT = """(() => {
  const token = location.hash.startsWith('#') ? location.hash.slice(1) : '';
  history.replaceState(null, '', location.pathname + location.search);
  if (!token) { document.body.textContent = 'Preview link is incomplete.'; return; }
  fetch('/__wright/bootstrap', {
    method: 'POST', credentials: 'same-origin',
    headers: {'Content-Type': 'application/json'}, body: JSON.stringify({token})
  }).then((response) => {
    if (!response.ok) throw new Error('bootstrap failed');
    location.replace('/');
  }).catch(() => { document.body.textContent = 'Preview link expired. Reopen it from Wright.'; });
})();"""
_SCRIPT_DIGEST = base64.b64encode(
    hashlib.sha256(_BOOTSTRAP_SCRIPT.encode("utf-8")).digest()
).decode("ascii")
_BOOTSTRAP_HTML = (
    "<!doctype html><html><head><meta charset='utf-8'>"
    "<meta name='referrer' content='no-referrer'><title>Opening preview</title>"
    "</head><body>Opening preview…<script>"
    + _BOOTSTRAP_SCRIPT
    + "</script></body></html>"
)


class BootstrapExchange(BaseModel):
    model_config = ConfigDict(extra="forbid")

    token: str = Field(min_length=32, max_length=2048)


def get_presentation_tokens() -> PresentationTokenService:
    return surface_application().presentation_tokens


def _translate(error: PresentationTokenError) -> HTTPException:
    return HTTPException(status_code=error.status_code, detail=error.code)


@router.get("/__wright/bootstrap")
def bootstrap_document(
    host: Annotated[str, Header(alias="Host")],
    tokens: Annotated[PresentationTokenService, Depends(get_presentation_tokens)],
) -> Response:
    try:
        tokens.require_bound_host(host)
    except PresentationTokenError as error:
        raise _translate(error) from error
    return Response(
        content=_BOOTSTRAP_HTML,
        media_type="text/html",
        headers={
            "Cache-Control": "no-store",
            "Content-Security-Policy": (
                "default-src 'none'; connect-src 'self'; base-uri 'none'; "
                f"form-action 'none'; script-src 'sha256-{_SCRIPT_DIGEST}'"
            ),
            "Referrer-Policy": "no-referrer",
            "X-Content-Type-Options": "nosniff",
        },
    )


@router.post("/__wright/bootstrap", status_code=204)
def exchange_bootstrap(
    body: BootstrapExchange,
    host: Annotated[str, Header(alias="Host")],
    tokens: Annotated[PresentationTokenService, Depends(get_presentation_tokens)],
) -> Response:
    try:
        session = tokens.exchange(host=host, token=body.token)
    except PresentationTokenError as error:
        raise _translate(error) from error
    remaining = max(1, int((session.expires_at - tokens.clock()).total_seconds()))
    response = Response(status_code=204, headers={"Cache-Control": "no-store"})
    response.set_cookie(
        "wright_surface",
        session.cookie_value,
        httponly=True,
        secure=tokens.preview.scheme == "https",
        samesite="strict",
        path="/",
        max_age=remaining,
    )
    return response
