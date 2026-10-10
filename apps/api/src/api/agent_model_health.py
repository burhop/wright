"""Distinguish absent local mirrors from the connected agent's model selection."""

from fastapi import HTTPException


async def reconcile_agent_model_configuration(health: dict) -> dict:
    """Catalog configuration is evidence of selection, never a provider probe.

    A workspace-only Hermes config can legitimately omit the gateway's model
    profile. Preserve every actual provider/authentication failure; only the
    missing-local-config case is reconciled against the authenticated gateway.
    """
    if health.get("state") != "disconnected" or health.get("error") != (
        "Hermes model base_url is not configured"
    ):
        return health
    from .routers.agent import _hermes_json_request, _hermes_profile

    try:
        payload = await _hermes_json_request(
            "GET",
            "/api/model/options",
            params={
                "profile": _hermes_profile(),
                "explicit_only": "true",
                "include_unconfigured": "false",
                "refresh": "false",
            },
        )
    except HTTPException as error:
        return {
            **health,
            "error": (
                "The agent model configuration could not be checked through "
                f"Hermes (HTTP {error.status_code}). Check the agent connection."
            ),
        }
    provider = payload.get("provider")
    model = payload.get("model")
    rows = payload.get("providers")
    configured = (
        isinstance(provider, str)
        and isinstance(model, str)
        and bool(provider.strip())
        and bool(model.strip())
        and isinstance(rows, list)
        and any(
            isinstance(row, dict)
            and row.get("slug") == provider
            and isinstance(row.get("models"), list)
            and model in row["models"]
            for row in rows
        )
    )
    if not configured:
        return {
            **health,
            "error": "No selected agent model was confirmed by Hermes. Configure the agent model before using chat.",
        }
    return {
        **health,
        "state": "unknown",
        "error": (
            "An agent model is configured in Hermes. Its provider connection "
            "has not been checked; workflow model readiness is assessed separately."
        ),
    }
