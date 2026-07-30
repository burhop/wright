"""Security boundary for user-requested HTTP health probes."""

from __future__ import annotations

import asyncio
from dataclasses import dataclass
import ipaddress
import re
import socket
import time
from collections.abc import Awaitable, Callable, Iterable, Sequence
from urllib.parse import urljoin

import httpx
import structlog


logger = structlog.get_logger(__name__)

MAX_URL_LENGTH = 2048
MAX_DNS_ANSWERS = 8
MAX_REDIRECTS = 3
REQUEST_TIMEOUT_SECONDS = 5.0
_REDIRECT_STATUSES = {301, 302, 303, 307, 308}
_CONTROL_ESCAPE = re.compile(r"%(?:0[0-9a-f]|1[0-9a-f]|7f)", re.IGNORECASE)
_NUMERIC_HOST = re.compile(r"(?:[0-9]+(?:\.[0-9]*)*|0x[0-9a-f]+)", re.IGNORECASE)
_RFC1918 = (
    ipaddress.ip_network("10.0.0.0/8"),
    ipaddress.ip_network("172.16.0.0/12"),
    ipaddress.ip_network("192.168.0.0/16"),
)
_IPV6_ULA = ipaddress.ip_network("fc00::/7")
_CGNAT = ipaddress.ip_network("100.64.0.0/10")
_DOCUMENTATION = (
    ipaddress.ip_network("192.0.2.0/24"),
    ipaddress.ip_network("198.51.100.0/24"),
    ipaddress.ip_network("203.0.113.0/24"),
    ipaddress.ip_network("2001:db8::/32"),
)
_IPV6_TRANSITION = (
    ipaddress.ip_network("64:ff9b::/96"),
    ipaddress.ip_network("64:ff9b:1::/48"),
    ipaddress.ip_network("2002::/16"),
    ipaddress.ip_network("2001::/32"),
)

Resolver = Callable[[str, int], Awaitable[Sequence[str]]]


class HealthProbePolicyError(ValueError):
    """Raised when a target cannot be contacted under the outbound policy."""


@dataclass(frozen=True)
class HealthProbeResult:
    status: str
    latency_ms: float
    error: str | None = None


@dataclass(frozen=True)
class _LogicalTarget:
    url: httpx.URL
    host: str
    port: int
    origin: tuple[str, str, int]


def _authority(raw_url: str) -> str:
    match = re.match(r"^[A-Za-z][A-Za-z0-9+.-]*://([^/?#]*)", raw_url)
    if not match:
        raise HealthProbePolicyError("absolute URL required")
    authority = match.group(1)
    if not authority or "@" in authority or "%" in authority:
        raise HealthProbePolicyError("ambiguous authority")
    return authority


def _parse_target(raw_url: str) -> _LogicalTarget:
    if not raw_url or raw_url != raw_url.strip() or len(raw_url) > MAX_URL_LENGTH:
        raise HealthProbePolicyError("invalid URL length")
    if "\\" in raw_url or any(
        ord(char) <= 0x20 or ord(char) == 0x7F for char in raw_url
    ):
        raise HealthProbePolicyError("invalid URL character")
    if _CONTROL_ESCAPE.search(raw_url):
        raise HealthProbePolicyError("encoded control character")

    authority = _authority(raw_url)
    try:
        url = httpx.URL(raw_url)
        port = url.port
    except (httpx.InvalidURL, ValueError) as exc:
        raise HealthProbePolicyError("invalid URL") from exc

    scheme = url.scheme.lower()
    if (
        scheme not in {"http", "https"}
        or not url.host
        or (port is not None and not 1 <= port <= 65535)
    ):
        raise HealthProbePolicyError("unsupported URL")
    if port is None:
        port = 443 if scheme == "https" else 80
    if url.fragment:
        raise HealthProbePolicyError("fragments are not permitted")

    host = url.host.rstrip(".").casefold()
    if not host:
        raise HealthProbePolicyError("hostname is required")
    if ":" in host and not authority.startswith("["):
        raise HealthProbePolicyError("IPv6 literals must be bracketed")

    try:
        address = ipaddress.ip_address(host)
    except ValueError:
        if _NUMERIC_HOST.fullmatch(host):
            raise HealthProbePolicyError("ambiguous numeric hostname")
        try:
            host = host.encode("idna").decode("ascii").casefold()
        except UnicodeError as exc:
            raise HealthProbePolicyError("invalid hostname") from exc
    else:
        if isinstance(address, ipaddress.IPv4Address) and str(address) != host:
            raise HealthProbePolicyError("non-canonical IPv4 literal")
        host = address.compressed.casefold()

    normalized = url.copy_with(host=host, fragment=None)
    return _LogicalTarget(
        url=normalized,
        host=host,
        port=port,
        origin=(scheme, host, port),
    )


def _trusted_origins(values: Iterable[str]) -> set[tuple[str, str, int]]:
    origins: set[tuple[str, str, int]] = set()
    for value in values:
        try:
            origins.add(_parse_target(value).origin)
        except HealthProbePolicyError:
            continue
    return origins


def _address_class(address: ipaddress.IPv4Address | ipaddress.IPv6Address) -> str:
    if isinstance(address, ipaddress.IPv6Address):
        if address.ipv4_mapped is not None:
            raise HealthProbePolicyError("mapped IPv6 is prohibited")
        if any(address in network for network in _IPV6_TRANSITION):
            raise HealthProbePolicyError("transition IPv6 is prohibited")
    if address.is_loopback:
        return "loopback"
    if address.is_unspecified or address.is_link_local:
        raise HealthProbePolicyError("local infrastructure address is prohibited")
    if address.is_multicast or address.is_reserved:
        raise HealthProbePolicyError("non-routable address is prohibited")
    if any(address in network for network in _DOCUMENTATION):
        raise HealthProbePolicyError("documentation address is prohibited")
    if isinstance(address, ipaddress.IPv4Address) and address in _CGNAT:
        raise HealthProbePolicyError("shared address space is prohibited")
    if isinstance(address, ipaddress.IPv4Address) and any(
        address in network for network in _RFC1918
    ):
        return "private"
    if isinstance(address, ipaddress.IPv6Address) and address in _IPV6_ULA:
        return "private"
    if address.is_global:
        return "global"
    raise HealthProbePolicyError("non-routable address is prohibited")


async def _default_resolver(host: str, port: int) -> Sequence[str]:
    try:
        return (ipaddress.ip_address(host).compressed,)
    except ValueError:
        pass

    if host == "localhost":
        return ("127.0.0.1", "::1")

    loop = asyncio.get_running_loop()
    records = await loop.getaddrinfo(
        host,
        port,
        type=socket.SOCK_STREAM,
        proto=socket.IPPROTO_TCP,
    )
    return tuple(record[4][0] for record in records)


async def _resolve_target(
    target: _LogicalTarget,
    *,
    resolver: Resolver,
    trusted_origins: set[tuple[str, str, int]],
) -> tuple[str, ...]:
    try:
        raw_addresses = await resolver(target.host, target.port)
    except (OSError, socket.gaierror) as exc:
        raise ConnectionError("resolution failed") from exc

    addresses: list[str] = []
    for raw_address in raw_addresses:
        try:
            address = ipaddress.ip_address(raw_address)
        except ValueError as exc:
            raise HealthProbePolicyError(
                "resolver returned an invalid address"
            ) from exc
        canonical = address.compressed
        if canonical not in addresses:
            addresses.append(canonical)
    if not addresses or len(addresses) > MAX_DNS_ANSWERS:
        raise HealthProbePolicyError("invalid DNS answer count")

    classes = {_address_class(ipaddress.ip_address(value)) for value in addresses}
    if "private" in classes and target.origin not in trusted_origins:
        raise HealthProbePolicyError("private origin is not configured")
    if target.host == "localhost" and classes != {"loopback"}:
        raise HealthProbePolicyError("localhost did not resolve to loopback")
    if target.host != "localhost" and "loopback" in classes:
        try:
            literal = ipaddress.ip_address(target.host)
        except ValueError:
            if target.origin not in trusted_origins:
                raise HealthProbePolicyError("loopback alias is not configured")
        else:
            if not literal.is_loopback:
                raise HealthProbePolicyError("unexpected loopback result")
    return tuple(addresses)


def _host_header(target: _LogicalTarget) -> str:
    host = f"[{target.host}]" if ":" in target.host else target.host
    default_port = 443 if target.url.scheme == "https" else 80
    return host if target.port == default_port else f"{host}:{target.port}"


def _pinned_url(target: _LogicalTarget, address: str) -> httpx.URL:
    return target.url.copy_with(host=ipaddress.ip_address(address).compressed)


def _health_fallback(url: httpx.URL) -> httpx.URL | None:
    path = url.path or "/"
    if path.rstrip("/").endswith("/health"):
        return None
    base = path.rstrip("/")
    return url.copy_with(path=f"{base}/health" if base else "/health")


async def _request_target(
    client: httpx.AsyncClient,
    target: _LogicalTarget,
    addresses: Sequence[str],
) -> httpx.Response:
    last_error: Exception | None = None
    for address in addresses:
        extensions = (
            {"sni_hostname": target.host} if target.url.scheme == "https" else {}
        )
        request = client.build_request(
            "GET",
            _pinned_url(target, address),
            headers={"Host": _host_header(target), "Connection": "close"},
            timeout=REQUEST_TIMEOUT_SECONDS,
            extensions=extensions,
        )
        try:
            return await client.send(request, stream=True)
        except (httpx.HTTPError, OSError) as exc:
            last_error = exc
    raise ConnectionError("all validated addresses failed") from last_error


async def _probe_candidate(
    raw_url: str,
    *,
    resolver: Resolver,
    trusted_origins: set[tuple[str, str, int]],
    client: httpx.AsyncClient,
) -> tuple[bool, str | None]:
    current = _parse_target(raw_url)
    original_host = current.host
    original_scheme = current.url.scheme
    visited: set[str] = set()

    for redirect_count in range(MAX_REDIRECTS + 1):
        logical_url = str(current.url)
        if logical_url in visited:
            raise HealthProbePolicyError("redirect loop")
        visited.add(logical_url)
        addresses = await _resolve_target(
            current,
            resolver=resolver,
            trusted_origins=trusted_origins,
        )
        response = await _request_target(client, current, addresses)
        try:
            if response.status_code == 200:
                return True, None
            if response.status_code not in _REDIRECT_STATUSES:
                return False, f"HTTP {response.status_code}"
            location = response.headers.get("location")
            if not location or redirect_count == MAX_REDIRECTS:
                raise HealthProbePolicyError("redirect limit exceeded")
            redirected = _parse_target(urljoin(logical_url, location))
            if redirected.host != original_host:
                raise HealthProbePolicyError("cross-host redirect")
            if original_scheme == "https" and redirected.url.scheme != "https":
                raise HealthProbePolicyError("HTTPS downgrade")
            current = redirected
        finally:
            await response.aclose()
    raise HealthProbePolicyError("redirect limit exceeded")


async def probe_health(
    url: str,
    *,
    trusted_local_origins: Iterable[str] = (),
    resolver: Resolver | None = None,
    transport: httpx.AsyncBaseTransport | None = None,
) -> HealthProbeResult:
    """Probe a validated HTTP endpoint without exposing an arbitrary fetch primitive."""

    started = time.perf_counter()
    try:
        initial = _parse_target(url)
        trusted = _trusted_origins(trusted_local_origins)
        candidates = [initial.url]
        fallback = _health_fallback(initial.url)
        if fallback is not None:
            candidates.append(fallback)

        last_error = "Endpoint could not be reached"
        async with httpx.AsyncClient(
            transport=transport,
            trust_env=False,
            follow_redirects=False,
            timeout=REQUEST_TIMEOUT_SECONDS,
            limits=httpx.Limits(max_keepalive_connections=0),
        ) as client:
            for candidate in candidates:
                try:
                    healthy, error = await _probe_candidate(
                        str(candidate),
                        resolver=resolver or _default_resolver,
                        trusted_origins=trusted,
                        client=client,
                    )
                except HealthProbePolicyError:
                    raise
                except Exception as exc:
                    logger.warning(
                        "health_probe_request_failed",
                        error_type=type(exc).__name__,
                        error=str(exc),
                    )
                    last_error = "Endpoint could not be reached"
                    continue
                if healthy:
                    return HealthProbeResult(
                        status="healthy",
                        latency_ms=(time.perf_counter() - started) * 1000.0,
                    )
                last_error = error or "Endpoint could not be reached"
        return HealthProbeResult(
            status="unhealthy",
            latency_ms=(time.perf_counter() - started) * 1000.0,
            error=last_error,
        )
    except HealthProbePolicyError as exc:
        logger.info("health_probe_target_rejected", reason=str(exc))
        return HealthProbeResult(
            status="unhealthy",
            latency_ms=(time.perf_counter() - started) * 1000.0,
            error="URL is not permitted",
        )
