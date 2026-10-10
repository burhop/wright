"""Qualify and lock an HTTP model route using the existing Hermes API."""

import hashlib
import os

import httpx

from core.process_validation import canonical_digest
from core.workflow_model_routing import WorkflowTextResolution
from .hermes_config import resolve_hermes_api_settings


class ModelRouteChangedError(ValueError):
    """A safe frozen-route diagnostic, distinct from model response parsing."""


def _profile():
    return (
        os.getenv("WRIGHT_HERMES_PROFILE") or os.getenv("HERMES_PROFILE") or "wright"
    ).strip() or "wright"


def _headers(settings):
    return {"Authorization": f"Bearer {settings.api_key}"} if settings.api_key else {}


async def workflow_model_capabilities():
    settings = resolve_hermes_api_settings()
    try:
        async with httpx.AsyncClient(timeout=15) as client:
            response = await client.get(
                settings.base_url.rstrip("/") + "/api/model/options",
                params={
                    "profile": _profile(),
                    "explicit_only": "true",
                    "include_unconfigured": "false",
                    "refresh": "false",
                },
                headers=_headers(settings),
            )
            response.raise_for_status()
            data = response.json()
        # Hermes and Wright's normalized facade have distinct public shapes.
        native = (data.get("provider"), data.get("model"))
        normalized = (data.get("current_provider"), data.get("current_model"))
        if any(value is not None for value in native):
            provider, model = native
            if any(value is not None for value in normalized) and normalized != native:
                raise ValueError("Conflicting model selections")
        else:
            provider, model = normalized
        if (
            not isinstance(provider, str)
            or provider in {"auto", "moa", "acp"}
            or not isinstance(model, str)
        ):
            raise ValueError()
        public = {
            "adapter": "hermes-http",
            "provider": provider,
            "model_reference": model,
            "profile": _profile(),
            "endpoint_digest": hashlib.sha256(
                settings.base_url.rstrip("/").encode()
            ).hexdigest(),
        }
        resolution = WorkflowTextResolution.model_validate(
            {**public, "configuration_digest": canonical_digest(public)}
        )
        return {"available": True, "resolution": resolution.model_dump(mode="json")}
    except (httpx.HTTPError, ValueError, KeyError, TypeError) as exc:
        raise ValueError(
            "The configured model gateway cannot confirm its provider and model. Check Model Setup before starting."
        ) from exc


async def lock_workflow_model(client, settings, expected_resolution, session_id):
    """No completion request is allowed until exact session lock confirmation."""
    expected = WorkflowTextResolution.model_validate(expected_resolution)
    if (
        expected.endpoint_digest
        != hashlib.sha256(settings.base_url.rstrip("/").encode()).hexdigest()
        or expected.profile != _profile()
    ):
        raise ModelRouteChangedError(
            "The frozen model adapter endpoint/profile changed. Restore the run's configuration or start an explicitly revised run."
        )
    created = await client.post(
        settings.base_url.rstrip("/") + "/api/sessions",
        headers=_headers(settings),
        json={
            "id": session_id,
            "source": "api_server",
            "provider": expected.provider,
            "model": expected.model_reference,
            "require_model_lock": True,
        },
    )
    created.raise_for_status()
    created_receipt = created.json()
    session = (
        created_receipt.get("session") if isinstance(created_receipt, dict) else None
    )
    if (
        created.status_code != 201
        or created_receipt.get("object") != "hermes.session"
        or not isinstance(session, dict)
        or session.get("id") != session_id
        or session.get("model") != expected.model_reference
    ):
        raise ModelRouteChangedError(
            "The gateway did not confirm a new private model session; no model request was submitted."
        )
    response = await client.post(
        settings.base_url.rstrip("/") + f"/api/sessions/{session_id}/model",
        headers=_headers(settings),
        json={
            "provider": expected.provider,
            "model": expected.model_reference,
            "require_model_lock": True,
        },
    )
    response.raise_for_status()
    receipt = response.json()
    runtime = receipt.get("runtime") if isinstance(receipt, dict) else None
    if (
        not isinstance(runtime, dict)
        or receipt.get("object") != "hermes.session.model_lock"
        or receipt.get("session_id") != session_id
        or runtime.get("model_lock") != "accepted"
        or runtime.get("provider") != expected.provider
        or runtime.get("model") != expected.model_reference
    ):
        raise ModelRouteChangedError(
            "The model gateway did not confirm the frozen provider/model lock; no model request was submitted."
        )
    return {
        "adapter": expected.adapter,
        "provider": runtime["provider"],
        "model_reference": runtime["model"],
        "configuration_digest": expected.configuration_digest,
        "model_lock": "accepted",
        "session_id": session_id,
        "session_created": True,
    }
