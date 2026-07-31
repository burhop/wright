from __future__ import annotations

from dataclasses import FrozenInstanceError

import pytest

from core.surfaces.network_values import (
    AddressClass,
    NetworkValueError,
    classify_address,
    normalize_target_url,
)
from workspace_service.surfaces.target_policy import (
    ResolvedTargetPin,
    TargetPolicy,
    TargetPolicyError,
)


pytestmark = pytest.mark.workspace_surfaces


class FakeResolver:
    def __init__(self, answers: dict[str, list[str]]) -> None:
        self.answers = answers

    def resolve_all(self, hostname: str) -> tuple[str, ...]:
        return tuple(self.answers.get(hostname, ()))


def test_url_normalization_rejects_credentials_schemes_fragments_and_alt_ip() -> None:
    normalized = normalize_target_url("https://App.Example.test:8443/base/")
    assert normalized.scheme == "https"
    assert normalized.hostname == "app.example.test"
    assert normalized.port == 8443
    assert normalized.base_path == "/base"

    for raw in (
        "file:///etc/passwd",
        "ftp://example.test/app",
        "https://user:secret@example.test/app",
        "https://example.test/app#secret",
        "http://127.1/app",
        "http://2130706433/app",
        "http://0x7f000001/app",
        "http://0177.0.0.1/app",
        "http://[fe80::1%25eth0]/app",
    ):
        with pytest.raises(NetworkValueError):
            normalize_target_url(raw)


def test_address_classification_normalizes_ipv4_mapped_ipv6() -> None:
    assert classify_address("127.0.0.1") is AddressClass.LOOPBACK
    assert classify_address("::1") is AddressClass.LOOPBACK
    assert classify_address("::ffff:127.0.0.1") is AddressClass.LOOPBACK
    assert classify_address("10.20.30.40") is AddressClass.PRIVATE
    assert classify_address("169.254.169.254") is AddressClass.LINK_LOCAL
    assert classify_address("0.0.0.0") is AddressClass.UNSPECIFIED
    assert classify_address("224.0.0.1") is AddressClass.MULTICAST
    assert classify_address("93.184.216.34") is AddressClass.PUBLIC


def test_attach_requires_administrator_approval_and_validates_every_answer() -> None:
    resolver = FakeResolver(
        {
            "app.example.test": ["93.184.216.34", "2606:2800:220:1:248:1893:25c8:1946"],
            "mixed.example.test": ["93.184.216.34", "::ffff:127.0.0.1"],
        }
    )
    policy = TargetPolicy(resolver=resolver)
    with pytest.raises(TargetPolicyError) as unapproved:
        policy.pin_approved_attach(
            "https://app.example.test/",
            administrator_approved=False,
            ownership_proof="operator-approved",
        )
    assert unapproved.value.code == "SURFACE_TARGET_APPROVAL_REQUIRED"

    pin = policy.pin_approved_attach(
        "https://app.example.test/",
        administrator_approved=True,
        ownership_proof="operator-approved",
    )
    assert pin.resolved_answers == (
        "93.184.216.34",
        "2606:2800:220:1:248:1893:25c8:1946",
    )
    with pytest.raises(TargetPolicyError) as mixed:
        policy.pin_approved_attach(
            "https://mixed.example.test/",
            administrator_approved=True,
            ownership_proof="operator-approved",
        )
    assert mixed.value.code == "SURFACE_TARGET_ADDRESS_DENIED"


def test_private_metadata_and_control_plane_targets_fail_closed() -> None:
    resolver = FakeResolver(
        {
            "private.example.test": ["10.0.0.8"],
            "metadata.example.test": ["169.254.169.254"],
            "control.example.test": ["127.0.0.1"],
        }
    )
    policy = TargetPolicy(
        resolver=resolver,
        allowed_attach_classes={AddressClass.PUBLIC, AddressClass.LOOPBACK},
        control_plane_endpoints={("127.0.0.1", 8000)},
    )
    with pytest.raises(TargetPolicyError) as private:
        policy.pin_approved_attach(
            "http://private.example.test:9000/",
            administrator_approved=True,
            ownership_proof="operator-approved",
        )
    assert private.value.code == "SURFACE_TARGET_ADDRESS_DENIED"
    with pytest.raises(TargetPolicyError) as metadata:
        policy.pin_approved_attach(
            "http://metadata.example.test/",
            administrator_approved=True,
            ownership_proof="operator-approved",
        )
    assert metadata.value.code == "SURFACE_TARGET_ADDRESS_DENIED"
    with pytest.raises(TargetPolicyError) as control:
        policy.pin_approved_attach(
            "http://control.example.test:8000/",
            administrator_approved=True,
            ownership_proof="operator-approved",
        )
    assert control.value.code == "SURFACE_TARGET_CONTROL_PLANE_DENIED"


def test_pin_derives_host_and_sni_once_and_is_immutable() -> None:
    policy = TargetPolicy(
        resolver=FakeResolver({"app.example.test": ["93.184.216.34"]})
    )
    pin = policy.pin_approved_attach(
        "https://App.Example.test:8443/base/",
        administrator_approved=True,
        ownership_proof="health-nonce",
    )
    assert pin.numeric_address == "93.184.216.34"
    assert pin.port == 8443
    assert pin.host_header == "app.example.test:8443"
    assert pin.server_name == "app.example.test"
    assert pin.base_path == "/base"
    assert pin.ownership_proof == "health-nonce"
    with pytest.raises(FrozenInstanceError):
        pin.port = 443  # type: ignore[misc]


def test_revalidation_rejects_any_dns_answer_change_without_mutating_pin() -> None:
    resolver = FakeResolver({"app.example.test": ["93.184.216.34"]})
    policy = TargetPolicy(resolver=resolver)
    pin = policy.pin_approved_attach(
        "https://app.example.test/",
        administrator_approved=True,
        ownership_proof="operator-approved",
    )
    resolver.answers["app.example.test"] = ["93.184.216.35"]
    with pytest.raises(TargetPolicyError) as rebound:
        policy.revalidate(pin)
    assert rebound.value.code == "SURFACE_TARGET_REBINDING"
    assert pin.numeric_address == "93.184.216.34"


def test_launched_targets_are_numeric_loopback_only() -> None:
    policy = TargetPolicy(resolver=FakeResolver({}))
    pin = policy.pin_launched(
        scheme="http",
        address="127.0.0.1",
        port=49152,
        instance_id="instance-1",
        generation=2,
    )
    assert isinstance(pin, ResolvedTargetPin)
    assert pin.host_header == "127.0.0.1:49152"
    assert pin.server_name is None
    with pytest.raises(TargetPolicyError) as public:
        policy.pin_launched(
            scheme="http",
            address="93.184.216.34",
            port=49152,
            instance_id="instance-1",
            generation=2,
        )
    assert public.value.code == "SURFACE_TARGET_ADDRESS_DENIED"
