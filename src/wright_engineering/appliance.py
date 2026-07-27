from __future__ import annotations

import json
import os
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen


class ApplianceError(RuntimeError):
    """Stable public error for appliance diagnostics."""


def appliance_status(
    api_url: str, token_env: str = "WRIGHT_API_TOKEN"
) -> dict[str, object]:
    token = os.environ.get(token_env)
    headers = {"Authorization": f"Bearer {token}"} if token else {}
    request = Request(f"{api_url.rstrip('/')}/api/health", headers=headers)
    try:
        with urlopen(request, timeout=5) as response:  # noqa: S310 - operator supplied URL
            payload = json.loads(response.read())
    except (HTTPError, URLError, TimeoutError, json.JSONDecodeError) as exc:
        raise ApplianceError(
            f"appliance status unavailable: {type(exc).__name__}"
        ) from exc
    if not isinstance(payload, dict):
        raise ApplianceError("appliance returned an invalid health document")
    return payload


def config_diagnostic(api_url: str, token_env: str) -> dict[str, str]:
    return {
        "api_url": api_url,
        "token_env": token_env,
        "token_status": "set" if os.environ.get(token_env) else "not set",
    }
