import httpx
import pytest

from agent_adapters.health_probe import HealthProbeResult, probe_health


def _resolver(*addresses: str):
    calls: list[tuple[str, int]] = []

    async def resolve(host: str, port: int):
        calls.append((host, port))
        return tuple(addresses)

    resolve.calls = calls
    return resolve


@pytest.mark.asyncio
async def test_probe_pins_global_dns_address_and_preserves_host_and_sni():
    resolver = _resolver("8.8.8.8")
    requests: list[httpx.Request] = []

    async def handle(request: httpx.Request) -> httpx.Response:
        requests.append(request)
        return httpx.Response(200, request=request)

    result = await probe_health(
        "https://llm.example.test:9443/v1",
        resolver=resolver,
        transport=httpx.MockTransport(handle),
    )

    assert result == HealthProbeResult(status="healthy", latency_ms=result.latency_ms)
    assert resolver.calls == [("llm.example.test", 9443)]
    assert requests[0].url.host == "8.8.8.8"
    assert requests[0].headers["host"] == "llm.example.test:9443"
    assert requests[0].extensions["sni_hostname"] == "llm.example.test"


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "url",
    [
        "file:///etc/passwd",
        "gopher://127.0.0.1/",
        "//127.0.0.1:8642/health",
        "http://user:pass@127.0.0.1/",
        "http://@127.0.0.1/",
        "http://127.0.0.1/path#fragment",
        "http://127.0.0.1\\@evil.test/",
        "http://127.0.0.1/%0d%0aHeader:value",
        "http://127.0.0.1:0/",
        "http://127.0.0.1:65536/",
        "http://[fe80::1%25eth0]/",
        "http://127.1/",
        "http://2130706433/",
        "http://0177.0.0.1/",
        "http://0x7f000001/",
    ],
)
async def test_probe_rejects_ambiguous_urls_without_network(url: str):
    calls = 0

    async def handle(request: httpx.Request) -> httpx.Response:
        nonlocal calls
        calls += 1
        raise AssertionError(f"network request was not expected: {request.url}")

    result = await probe_health(url, transport=httpx.MockTransport(handle))

    assert result.status == "unhealthy"
    assert result.error == "URL is not permitted"
    assert calls == 0


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "address",
    [
        "0.0.0.0",
        "169.254.169.254",
        "224.0.0.1",
        "100.100.100.200",
        "192.0.2.10",
        "::",
        "fe80::1",
        "ff02::1",
        "::ffff:127.0.0.1",
        "64:ff9b::7f00:1",
        "2002:7f00:1::",
        "2001::1",
    ],
)
async def test_probe_rejects_prohibited_address_classes(address: str):
    result = await probe_health(
        "https://llm.example.test/health",
        resolver=_resolver(address),
        transport=httpx.MockTransport(
            lambda request: (_ for _ in ()).throw(
                AssertionError(f"network request was not expected: {request.url}")
            )
        ),
    )

    assert result.status == "unhealthy"
    assert result.error == "URL is not permitted"


@pytest.mark.asyncio
async def test_probe_rejects_mixed_safe_and_prohibited_dns_answers():
    result = await probe_health(
        "https://llm.example.test/health",
        resolver=_resolver("8.8.8.8", "169.254.169.254"),
        transport=httpx.MockTransport(
            lambda request: (_ for _ in ()).throw(AssertionError(request.url))
        ),
    )

    assert result.status == "unhealthy"
    assert result.error == "URL is not permitted"


@pytest.mark.asyncio
@pytest.mark.parametrize(
    ("url", "trusted_origins"),
    [
        ("http://127.0.0.1:8642/health", ()),
        ("http://localhost:8642/health", ()),
        ("http://[::1]:8642/health", ()),
        ("http://192.168.1.20:11434/v1", ("http://192.168.1.20:11434",)),
        ("http://[fd00::20]:11434/v1", ("http://[fd00::20]:11434",)),
    ],
)
async def test_probe_allows_loopback_and_exact_configured_local_origins(
    url: str, trusted_origins: tuple[str, ...]
):
    requests: list[httpx.Request] = []

    async def handle(request: httpx.Request) -> httpx.Response:
        requests.append(request)
        return httpx.Response(200, request=request)

    result = await probe_health(
        url,
        trusted_local_origins=trusted_origins,
        transport=httpx.MockTransport(handle),
    )

    assert result.status == "healthy"
    assert len(requests) == 1


@pytest.mark.asyncio
async def test_probe_rejects_unconfigured_private_origin():
    result = await probe_health(
        "http://192.168.1.20:11434/v1",
        transport=httpx.MockTransport(
            lambda request: (_ for _ in ()).throw(AssertionError(request.url))
        ),
    )

    assert result.status == "unhealthy"
    assert result.error == "URL is not permitted"


@pytest.mark.asyncio
async def test_probe_revalidates_relative_redirect_and_rejects_cross_host():
    requests: list[httpx.Request] = []

    async def safe_redirect(request: httpx.Request) -> httpx.Response:
        requests.append(request)
        if len(requests) == 1:
            return httpx.Response(302, headers={"Location": "/ready"}, request=request)
        return httpx.Response(200, request=request)

    safe_result = await probe_health(
        "https://llm.example.test/",
        resolver=_resolver("8.8.8.8"),
        transport=httpx.MockTransport(safe_redirect),
    )
    assert safe_result.status == "healthy"
    assert len(requests) == 2

    async def unsafe_redirect(request: httpx.Request) -> httpx.Response:
        return httpx.Response(
            302,
            headers={"Location": "http://169.254.169.254/latest/meta-data"},
            request=request,
        )

    unsafe_result = await probe_health(
        "https://llm.example.test/",
        resolver=_resolver("8.8.8.8"),
        transport=httpx.MockTransport(unsafe_redirect),
    )
    assert unsafe_result.status == "unhealthy"
    assert unsafe_result.error == "URL is not permitted"


@pytest.mark.asyncio
async def test_probe_uses_safe_structural_health_fallback():
    paths: list[str] = []

    async def handle(request: httpx.Request) -> httpx.Response:
        paths.append(request.url.path)
        status = 200 if request.url.path == "/v1/health" else 404
        return httpx.Response(status, request=request)

    result = await probe_health(
        "http://127.0.0.1:11434/v1?model=local",
        transport=httpx.MockTransport(handle),
    )

    assert result.status == "healthy"
    assert paths == ["/v1", "/v1/health"]


@pytest.mark.asyncio
async def test_probe_sanitizes_network_exception_and_response_body():
    secret = r"D:\private\token.txt?credential=super-secret"

    async def fail(request: httpx.Request) -> httpx.Response:
        raise httpx.ConnectError(secret, request=request)

    result = await probe_health(
        "http://127.0.0.1:8642/",
        transport=httpx.MockTransport(fail),
    )

    assert result.status == "unhealthy"
    assert result.error == "Endpoint could not be reached"
    assert secret not in result.error


@pytest.mark.asyncio
async def test_probe_rejects_excessive_dns_answers():
    addresses = tuple(f"8.8.8.{index}" for index in range(1, 10))
    result = await probe_health(
        "https://llm.example.test/",
        resolver=_resolver(*addresses),
        transport=httpx.MockTransport(
            lambda request: (_ for _ in ()).throw(AssertionError(request.url))
        ),
    )

    assert result.status == "unhealthy"
    assert result.error == "URL is not permitted"
