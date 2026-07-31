"""Pure proxy-boundary helpers shared by HTTP, WebSocket, and SSE paths."""

from __future__ import annotations

from urllib.parse import urljoin, urlsplit, urlunsplit

from workspace_service.surfaces.target_policy import ResolvedTargetPin


class ProxySecurityError(RuntimeError):
    pass


_HOP_BY_HOP = frozenset(
    {
        "connection",
        "keep-alive",
        "proxy-authenticate",
        "proxy-authorization",
        "te",
        "trailer",
        "transfer-encoding",
        "upgrade",
    }
)
_CONTROL_HEADERS = frozenset(
    {
        "authorization",
        "proxy-authorization",
        "x-csrf-token",
        "x-xsrf-token",
        "forwarded",
        "x-forwarded-for",
        "x-forwarded-host",
        "x-forwarded-port",
        "x-forwarded-proto",
        "x-real-ip",
    }
)
_INTERNAL_COOKIES = frozenset({"wright_surface", "wright_session", "wright_csrf"})


def _safe_pair(name: str, value: str) -> tuple[str, str]:
    if not name or any(character in name + value for character in "\r\n\0"):
        raise ProxySecurityError("Proxy header is invalid")
    return name, value


def _target_cookies(value: str) -> str:
    retained: list[str] = []
    for item in value.split(";"):
        pair = item.strip()
        if not pair or "=" not in pair:
            continue
        name = pair.split("=", 1)[0].strip().lower()
        if name in _INTERNAL_COOKIES or name.startswith("wright_"):
            continue
        retained.append(pair)
    return "; ".join(retained)


def filter_request_headers(
    headers: list[tuple[str, str]] | tuple[tuple[str, str], ...],
    *,
    pin: ResolvedTargetPin,
) -> list[tuple[str, str]]:
    """Remove control authority and derive upstream Host only from the pin."""
    connection_tokens: set[str] = set()
    for name, value in headers:
        if name.lower() == "connection":
            connection_tokens.update(
                token.strip().lower() for token in value.split(",") if token.strip()
            )
    output: list[tuple[str, str]] = []
    for raw_name, raw_value in headers:
        name, value = _safe_pair(raw_name, raw_value)
        lowered = name.lower()
        if (
            lowered == "host"
            or lowered in _HOP_BY_HOP
            or lowered in connection_tokens
            or lowered in _CONTROL_HEADERS
            or lowered.startswith("x-wright-")
        ):
            continue
        if lowered == "cookie":
            safe_cookie = _target_cookies(value)
            if safe_cookie:
                output.append(("Cookie", safe_cookie))
            continue
        output.append((name, value))
    output.append(("Host", pin.host_header))
    return output


def _host_only_cookie(value: str) -> str | None:
    segments = [segment.strip() for segment in value.split(";") if segment.strip()]
    if not segments or "=" not in segments[0]:
        raise ProxySecurityError("Target cookie is invalid")
    name = segments[0].split("=", 1)[0].strip().lower()
    if name in _INTERNAL_COOKIES or name.startswith("wright_"):
        return None
    retained = [segments[0]]
    retained.extend(
        segment for segment in segments[1:] if not segment.lower().startswith("domain=")
    )
    return "; ".join(retained)


def filter_response_headers(
    headers: list[tuple[str, str]] | tuple[tuple[str, str], ...],
) -> list[tuple[str, str]]:
    """Contain cookies while preserving upstream CSP and framing refusal."""
    connection_tokens: set[str] = set()
    for name, value in headers:
        if name.lower() == "connection":
            connection_tokens.update(
                token.strip().lower() for token in value.split(",") if token.strip()
            )
    output: list[tuple[str, str]] = []
    for raw_name, raw_value in headers:
        name, value = _safe_pair(raw_name, raw_value)
        lowered = name.lower()
        if lowered in _HOP_BY_HOP or lowered in connection_tokens:
            continue
        if lowered == "set-cookie":
            cookie = _host_only_cookie(value)
            if cookie is not None:
                output.append(("Set-Cookie", cookie))
            continue
        output.append((name, value))
    return output


def validate_redirect(location: str, *, pin: ResolvedTargetPin) -> str:
    if not location or any(character in location for character in "\r\n\\"):
        raise ProxySecurityError("redirect target is invalid")
    base = urlunsplit((pin.scheme, pin.host_header, pin.base_path or "/", "", ""))
    absolute = urlsplit(urljoin(base, location))
    if absolute.username is not None or absolute.password is not None:
        raise ProxySecurityError("redirect credentials are forbidden")
    port = absolute.port or (443 if absolute.scheme == "https" else 80)
    if (
        absolute.scheme != pin.scheme
        or absolute.hostname != pin.source_hostname
        or port != pin.port
    ):
        raise ProxySecurityError("redirect target differs from the pinned target")
    return urlunsplit(("", "", absolute.path or "/", absolute.query, absolute.fragment))


__all__ = [
    "ProxySecurityError",
    "filter_request_headers",
    "filter_response_headers",
    "validate_redirect",
]
