"""Resolve and immutably pin authorized live-application targets."""

from __future__ import annotations

import socket
from dataclasses import dataclass
from typing import Protocol

from core.surfaces.network_values import (
    AddressClass,
    NetworkValueError,
    classify_address,
    normalize_ip_address,
    normalize_target_url,
)


class Resolver(Protocol):
    def resolve_all(self, hostname: str) -> tuple[str, ...]: ...


class SystemResolver:
    def resolve_all(self, hostname: str) -> tuple[str, ...]:
        answers: list[str] = []
        for _family, _kind, _protocol, _canonical, address in socket.getaddrinfo(
            hostname, None, type=socket.SOCK_STREAM
        ):
            normalized = normalize_ip_address(str(address[0]))
            if normalized not in answers:
                answers.append(normalized)
        return tuple(answers)


class TargetPolicyError(RuntimeError):
    def __init__(self, code: str, message: str) -> None:
        super().__init__(message)
        self.code = code


@dataclass(frozen=True, slots=True)
class ResolvedTargetPin:
    scheme: str
    numeric_address: str
    port: int
    source_hostname: str
    host_header: str
    server_name: str | None
    base_path: str
    resolved_answers: tuple[str, ...]
    ownership: str
    ownership_proof: str
    instance_id: str | None = None
    generation: int | None = None


_ALWAYS_DENIED = frozenset(
    {
        AddressClass.LINK_LOCAL,
        AddressClass.MULTICAST,
        AddressClass.UNSPECIFIED,
        AddressClass.RESERVED,
    }
)
_METADATA_ADDRESSES = frozenset(
    {
        "169.254.169.254",
        "169.254.170.2",
        "fd00:ec2::254",
    }
)
_OWNERSHIP_PROOFS = frozenset(
    {"shared-secret", "health-nonce", "process-attestation", "operator-approved"}
)


class TargetPolicy:
    def __init__(
        self,
        *,
        resolver: Resolver | None = None,
        allowed_attach_classes: set[AddressClass] | frozenset[AddressClass] = frozenset(
            {AddressClass.PUBLIC}
        ),
        control_plane_endpoints: set[tuple[str, int]] | frozenset[tuple[str, int]] = frozenset(),
    ) -> None:
        self.resolver = resolver or SystemResolver()
        self.allowed_attach_classes = frozenset(allowed_attach_classes)
        self.control_plane_endpoints = frozenset(
            (normalize_ip_address(address), port)
            for address, port in control_plane_endpoints
        )

    @staticmethod
    def _canonical_answers(answers: tuple[str, ...]) -> tuple[str, ...]:
        canonical: list[str] = []
        for raw in answers:
            try:
                value = normalize_ip_address(raw)
            except NetworkValueError as error:
                raise TargetPolicyError(
                    "SURFACE_TARGET_ADDRESS_DENIED",
                    "Target resolution returned an invalid address",
                ) from error
            if value not in canonical:
                canonical.append(value)
        if not canonical or len(canonical) > 32:
            raise TargetPolicyError(
                "SURFACE_TARGET_ADDRESS_DENIED",
                "Target resolution returned no bounded address set",
            )
        return tuple(canonical)

    def _validate_answers(self, answers: tuple[str, ...], *, port: int) -> None:
        for address in answers:
            address_class = classify_address(address)
            if (address, port) in self.control_plane_endpoints:
                raise TargetPolicyError(
                    "SURFACE_TARGET_CONTROL_PLANE_DENIED",
                    "Target resolves to a Wright control-plane endpoint",
                )
            if (
                address in _METADATA_ADDRESSES
                or address_class in _ALWAYS_DENIED
                or address_class not in self.allowed_attach_classes
            ):
                raise TargetPolicyError(
                    "SURFACE_TARGET_ADDRESS_DENIED",
                    "Target address class is denied by policy",
                )

    def pin_approved_attach(
        self,
        value: str,
        *,
        administrator_approved: bool,
        ownership_proof: str,
    ) -> ResolvedTargetPin:
        if not administrator_approved:
            raise TargetPolicyError(
                "SURFACE_TARGET_APPROVAL_REQUIRED",
                "Managed target attachment requires administrator approval",
            )
        if ownership_proof not in _OWNERSHIP_PROOFS:
            raise TargetPolicyError(
                "SURFACE_TARGET_APPROVAL_REQUIRED",
                "Managed target attachment requires supported ownership proof",
            )
        try:
            normalized = normalize_target_url(value)
        except NetworkValueError as error:
            raise TargetPolicyError(
                "SURFACE_TARGET_URL_REJECTED", "Managed target URL is rejected"
            ) from error
        raw_answers = (
            (normalized.hostname,)
            if normalized.is_ip_literal
            else self.resolver.resolve_all(normalized.hostname)
        )
        answers = self._canonical_answers(raw_answers)
        self._validate_answers(answers, port=normalized.port)
        return ResolvedTargetPin(
            scheme=normalized.scheme,
            numeric_address=answers[0],
            port=normalized.port,
            source_hostname=normalized.hostname,
            host_header=normalized.host_header,
            server_name=(
                normalized.hostname
                if normalized.scheme == "https" and not normalized.is_ip_literal
                else None
            ),
            base_path=normalized.base_path,
            resolved_answers=answers,
            ownership="attached_verified",
            ownership_proof=ownership_proof,
        )

    def pin_launched(
        self,
        *,
        scheme: str,
        address: str,
        port: int,
        instance_id: str,
        generation: int,
    ) -> ResolvedTargetPin:
        try:
            normalized_address = normalize_ip_address(address)
        except NetworkValueError as error:
            raise TargetPolicyError(
                "SURFACE_TARGET_ADDRESS_DENIED", "Launched target address is invalid"
            ) from error
        if scheme not in {"http", "https"} or not 1 <= port <= 65535:
            raise TargetPolicyError(
                "SURFACE_TARGET_URL_REJECTED", "Launched target endpoint is invalid"
            )
        if classify_address(normalized_address) is not AddressClass.LOOPBACK:
            raise TargetPolicyError(
                "SURFACE_TARGET_ADDRESS_DENIED",
                "Wright-launched targets must bind to loopback",
            )
        if (normalized_address, port) in self.control_plane_endpoints:
            raise TargetPolicyError(
                "SURFACE_TARGET_CONTROL_PLANE_DENIED",
                "Launched target collides with the Wright control plane",
            )
        if not instance_id or generation < 1:
            raise TargetPolicyError(
                "SURFACE_TARGET_URL_REJECTED", "Runtime identity is invalid"
            )
        host = (
            f"[{normalized_address}]"
            if ":" in normalized_address
            else normalized_address
        )
        default_port = 443 if scheme == "https" else 80
        host_header = host if port == default_port else f"{host}:{port}"
        return ResolvedTargetPin(
            scheme=scheme,
            numeric_address=normalized_address,
            port=port,
            source_hostname=normalized_address,
            host_header=host_header,
            server_name=None,
            base_path="/",
            resolved_answers=(normalized_address,),
            ownership="launched",
            ownership_proof="process-listener-identity",
            instance_id=instance_id,
            generation=generation,
        )

    def revalidate(self, pin: ResolvedTargetPin) -> ResolvedTargetPin:
        if pin.source_hostname == pin.numeric_address:
            return pin
        current = self._canonical_answers(
            self.resolver.resolve_all(pin.source_hostname)
        )
        if frozenset(current) != frozenset(pin.resolved_answers):
            raise TargetPolicyError(
                "SURFACE_TARGET_REBINDING",
                "Target DNS answers changed after authority was pinned",
            )
        self._validate_answers(current, port=pin.port)
        return pin


__all__ = [
    "ResolvedTargetPin",
    "Resolver",
    "SystemResolver",
    "TargetPolicy",
    "TargetPolicyError",
]
