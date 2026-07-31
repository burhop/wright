"""Pure, side-effect-free URL and IP normalization for surface targets."""

from __future__ import annotations

import ipaddress
import re
from dataclasses import dataclass
from enum import StrEnum
from urllib.parse import unquote, urlsplit


_DNS_LABEL = re.compile(r"^[a-z0-9](?:[a-z0-9-]{0,61}[a-z0-9])?$")
_ALTERNATE_NUMERIC = re.compile(
    r"^(?:0x[0-9a-f]+|[0-9]+|[0-9.]+|(?:0x[0-9a-f]+|[0-9]+)(?:\.(?:0x[0-9a-f]+|[0-9]+)){1,3})$",
    re.IGNORECASE,
)


class NetworkValueError(ValueError):
    """A target value is ambiguous or unsafe to normalize."""


class AddressClass(StrEnum):
    PUBLIC = "public"
    PRIVATE = "private"
    LOOPBACK = "loopback"
    LINK_LOCAL = "link_local"
    MULTICAST = "multicast"
    UNSPECIFIED = "unspecified"
    RESERVED = "reserved"


@dataclass(frozen=True, slots=True)
class NormalizedTargetUrl:
    scheme: str
    hostname: str
    port: int
    base_path: str
    is_ip_literal: bool

    @property
    def host_header(self) -> str:
        host = f"[{self.hostname}]" if ":" in self.hostname else self.hostname
        default_port = 443 if self.scheme == "https" else 80
        return host if self.port == default_port else f"{host}:{self.port}"


def normalize_ip_address(value: str) -> str:
    try:
        address = ipaddress.ip_address(value)
    except ValueError as error:
        raise NetworkValueError("Target address is not a canonical IP address") from error
    if isinstance(address, ipaddress.IPv6Address) and address.ipv4_mapped:
        address = address.ipv4_mapped
    return address.compressed.lower()


def classify_address(value: str) -> AddressClass:
    address = ipaddress.ip_address(normalize_ip_address(value))
    if address.is_unspecified:
        return AddressClass.UNSPECIFIED
    if address.is_loopback:
        return AddressClass.LOOPBACK
    if address.is_multicast:
        return AddressClass.MULTICAST
    if address.is_link_local:
        return AddressClass.LINK_LOCAL
    if address.is_private:
        return AddressClass.PRIVATE
    if not address.is_global:
        return AddressClass.RESERVED
    return AddressClass.PUBLIC


def _normalize_hostname(value: str) -> tuple[str, bool]:
    if "%" in value:
        raise NetworkValueError("Target hostname contains unsupported escaping")
    try:
        return normalize_ip_address(value), True
    except NetworkValueError:
        pass
    if ":" in value or _ALTERNATE_NUMERIC.fullmatch(value):
        raise NetworkValueError("Target hostname uses ambiguous numeric notation")
    candidate = value.removesuffix(".")
    try:
        candidate = candidate.encode("idna").decode("ascii").lower()
    except UnicodeError as error:
        raise NetworkValueError("Target hostname is not valid IDNA") from error
    if len(candidate) > 253 or not candidate:
        raise NetworkValueError("Target hostname length is invalid")
    if any(not _DNS_LABEL.fullmatch(label) for label in candidate.split(".")):
        raise NetworkValueError("Target hostname syntax is invalid")
    return candidate, False


def normalize_target_url(value: str) -> NormalizedTargetUrl:
    if not value or any(ord(character) <= 32 or ord(character) == 127 for character in value):
        raise NetworkValueError("Target URL contains whitespace or control characters")
    if "\\" in value:
        raise NetworkValueError("Target URL contains an ambiguous backslash")
    try:
        parsed = urlsplit(value)
        port = parsed.port
    except ValueError as error:
        raise NetworkValueError("Target URL authority is malformed") from error
    scheme = parsed.scheme.lower()
    if scheme not in {"http", "https"}:
        raise NetworkValueError("Target URL must use HTTP(S)")
    if parsed.username is not None or parsed.password is not None:
        raise NetworkValueError("Target URL must not contain credentials")
    if parsed.fragment:
        raise NetworkValueError("Target URL must not contain a fragment")
    if parsed.query:
        raise NetworkValueError("Target URL must not contain a fixed query")
    if not parsed.hostname:
        raise NetworkValueError("Target URL hostname is required")
    hostname, is_ip_literal = _normalize_hostname(parsed.hostname)
    effective_port = port if port is not None else (443 if scheme == "https" else 80)
    if not 1 <= effective_port <= 65535:
        raise NetworkValueError("Target URL port is out of range")
    decoded_path = unquote(parsed.path or "/")
    if "\x00" in decoded_path or any(
        segment == ".." for segment in decoded_path.split("/")
    ):
        raise NetworkValueError("Target URL base path is ambiguous")
    base_path = "/" + decoded_path.strip("/") if decoded_path.strip("/") else "/"
    return NormalizedTargetUrl(
        scheme=scheme,
        hostname=hostname,
        port=effective_port,
        base_path=base_path,
        is_ip_literal=is_ip_literal,
    )


__all__ = [
    "AddressClass",
    "NetworkValueError",
    "NormalizedTargetUrl",
    "classify_address",
    "normalize_ip_address",
    "normalize_target_url",
]
