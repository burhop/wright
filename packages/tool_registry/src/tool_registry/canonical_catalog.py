from __future__ import annotations

import json
import ipaddress
from dataclasses import dataclass
from importlib.resources import files
from typing import Any
from urllib.parse import urlsplit

import httpx
import yaml
from jsonschema import Draft202012Validator

from .catalog_loader import catalog_entry_to_mcp_seed
from .catalog_evidence import CatalogEvidenceError, validate_catalog_evidence
from .catalog_models import CatalogEntry
from .mcp_catalog import tier_sort_key

CATALOG_MAX_ENVELOPE_BYTES = 5 * 1024 * 1024

CATALOG_PACKAGE = "tool_registry.catalog"
CATALOG_RESOURCE = "engineering-catalog.yaml"
SCHEMA_RESOURCE = "schema.json"

LEGACY_SERVER_IDS = {
    "aps-mcp-server-nodejs": "autodesk-aps-official",
    "aps-mcp-server-petr": "autodesk-aps-petrbroz",
    "autocad-mcp": "autocad-mcp-hvkshetry",
    "blender-mcp": "blender-mcp-ahujasid",
    "caid-mcp": "caid-opencascade-dreliq9",
    "creo-mcp": "creo-parametric-mcp",
    "creoson-mcp-bridge": "creopyson-creoson",
    "freecad-addon-robust": "freecad-robust-spkane",
    "freecad-mcp-contextform": "freecad-copilot-contextform",
    "freecad-mcp-nekanat": "freecad-core-nekanat",
    "freecad-mcp-sandraschi": "freecad-engineering-sandraschi",
    "fusion360-mcp-server": "fusion360-mcp-faust",
    "multicad-mcp": "multicad-mcp-ancode666",
    "openscad-mcp": "openscad-mcp-server",
    "revit-mcp": "revit-mcp-servers",
    "rhino-mcp": "rhino-mcp-mcneel",
    "sketchup-mcp": "sketchup-mcp-mhyrr",
    "solidworks-api-mcp": "solidworks-api-docs",
    "thingworx-mcp": "ptc-thingworx-mcp",
    "trikos529-openscad": "openscad-linter-trikos529",
    "web3d-mcp": "web3d-mcp-r3f",
    "webmcp-openscad": "webmcp-openscad-jherr",
    "wincc-unified-mcp": "siemens-wincc-unified",
    "zoo-mcp": "zoo-dev-cloud-cad",
}


class CatalogValidationError(RuntimeError):
    pass


class CatalogFetchError(RuntimeError):
    def __init__(self, code: str, message: str) -> None:
        self.code = code
        super().__init__(message)


@dataclass(frozen=True, slots=True)
class ApprovedCatalogChannel:
    name: str
    url: str
    timeout_seconds: float = 10.0
    max_bytes: int = CATALOG_MAX_ENVELOPE_BYTES
    allow_loopback_http: bool = False


def _schema() -> dict[str, Any]:
    return json.loads(
        files(CATALOG_PACKAGE).joinpath(SCHEMA_RESOURCE).read_text("utf-8")
    )


def _validate_catalog_document(document: Any) -> dict[str, Any]:
    if not isinstance(document, dict) or document.get("format_version") != 1:
        raise CatalogValidationError("Canonical catalog format_version must be 1")
    raw_servers = document.get("servers")
    if not isinstance(raw_servers, list):
        raise CatalogValidationError("Canonical catalog servers must be a list")

    validator = Draft202012Validator(_schema())
    entries: list[CatalogEntry] = []
    errors: list[str] = []
    for index, raw in enumerate(raw_servers):
        schema_errors = sorted(
            validator.iter_errors(raw), key=lambda error: tuple(error.absolute_path)
        )
        if schema_errors:
            errors.extend(
                f"servers/{index}: {error.message}" for error in schema_errors[:3]
            )
            continue
        entries.append(CatalogEntry.model_validate(raw))
    if errors:
        raise CatalogValidationError(
            "Canonical engineering catalog is invalid: " + "; ".join(errors[:5])
        )
    _validate_identity(entries)
    _validate_evidence(entries)
    return {
        "format_version": 1,
        "servers": [entry.model_dump(mode="json") for entry in entries],
    }


def load_catalog_document() -> dict[str, Any]:
    catalog_text = files(CATALOG_PACKAGE).joinpath(CATALOG_RESOURCE).read_text("utf-8")
    return load_catalog_document_from_text(catalog_text)


def load_catalog_document_from_text(catalog_text: str) -> dict[str, Any]:
    return _validate_catalog_document(yaml.safe_load(catalog_text))


def _is_loopback(host: str | None) -> bool:
    if not host:
        return False
    if host.lower() == "localhost":
        return True
    try:
        return ipaddress.ip_address(host).is_loopback
    except ValueError:
        return False


def fetch_catalog_envelope(
    channel: ApprovedCatalogChannel,
    *,
    transport: httpx.BaseTransport | None = None,
) -> dict[str, Any]:
    """Fetch one administrator-approved URL with no redirects or ambient auth."""
    parsed = urlsplit(channel.url)
    allowed_scheme = parsed.scheme == "https" or (
        parsed.scheme == "http"
        and channel.allow_loopback_http
        and _is_loopback(parsed.hostname)
    )
    if (
        not allowed_scheme
        or not parsed.hostname
        or parsed.username is not None
        or parsed.password is not None
        or parsed.fragment
    ):
        raise CatalogFetchError(
            "catalog_channel_unsafe",
            "Configured catalog channel URL is not permitted.",
        )
    try:
        with httpx.Client(
            follow_redirects=False,
            trust_env=False,
            timeout=channel.timeout_seconds,
            transport=transport,
            headers={
                "Accept": "application/json",
                "User-Agent": "Wright-Catalog-Updater/1",
            },
        ) as client:
            with client.stream("GET", channel.url) as response:
                if 300 <= response.status_code < 400:
                    raise CatalogFetchError(
                        "catalog_channel_redirect_rejected",
                        "Configured catalog channel returned a redirect.",
                    )
                if response.status_code != 200:
                    raise CatalogFetchError(
                        "catalog_channel_unavailable",
                        "Configured catalog channel could not be fetched.",
                    )
                length = response.headers.get("content-length")
                if length and int(length) > channel.max_bytes:
                    raise CatalogFetchError(
                        "catalog_envelope_too_large",
                        "Catalog update exceeds the configured size limit.",
                    )
                chunks: list[bytes] = []
                total = 0
                for chunk in response.iter_bytes():
                    total += len(chunk)
                    if total > channel.max_bytes:
                        raise CatalogFetchError(
                            "catalog_envelope_too_large",
                            "Catalog update exceeds the configured size limit.",
                        )
                    chunks.append(chunk)
    except CatalogFetchError:
        raise
    except (httpx.HTTPError, OSError, ValueError) as error:
        raise CatalogFetchError(
            "catalog_channel_unavailable",
            "Configured catalog channel could not be fetched.",
        ) from error
    from .catalog_signing import parse_json_strict

    return parse_json_strict(b"".join(chunks), max_bytes=channel.max_bytes)


def load_catalog_document_from_url(*args, **kwargs) -> dict[str, Any]:
    raise CatalogFetchError(
        "catalog_direct_url_disabled",
        "Direct catalog URL loading is disabled; use an approved signed channel.",
    )


def load_canonical_entries() -> list[CatalogEntry]:
    return [
        CatalogEntry.model_validate(entry)
        for entry in load_catalog_document()["servers"]
    ]


def load_canonical_entries_from_url(
    url: str, *, timeout_seconds: float = 10.0
) -> list[CatalogEntry]:
    raise CatalogFetchError(
        "catalog_direct_url_disabled",
        "Direct catalog URL loading is disabled; use an approved signed channel.",
    )


def load_engineering_catalog() -> list[dict[str, Any]]:
    return engineering_catalog_from_document(load_catalog_document())


def engineering_catalog_from_document(
    document: dict[str, Any],
) -> list[dict[str, Any]]:
    result: list[dict[str, Any]] = []
    validated = _validate_catalog_document(document)
    for raw_entry in validated["servers"]:
        entry = CatalogEntry.model_validate(raw_entry)
        seed = catalog_entry_to_mcp_seed(entry)
        canonical = entry.id
        seed["server_id"] = LEGACY_SERVER_IDS.get(canonical, canonical)
        seed["aliases"] = sorted({canonical, *entry.aliases} - {seed["server_id"]})
        if isinstance(seed.get("command"), list):
            seed["command"] = json.dumps(seed["command"])
        if isinstance(seed.get("env_vars"), list):
            seed["env_vars"] = json.dumps(
                [
                    item.model_dump(mode="json")
                    if hasattr(item, "model_dump")
                    else item
                    for item in seed["env_vars"]
                ]
            )
        seed["launch_env"] = json.dumps(seed.get("launch_env", {}))
        result.append(seed)
    result.sort(key=tier_sort_key)
    return result


def catalog_aliases() -> dict[str, str]:
    result: dict[str, str] = {}
    for entry in load_canonical_entries():
        canonical = LEGACY_SERVER_IDS.get(entry.id, entry.id)
        for alias in {entry.id, *entry.aliases} - {canonical}:
            result[alias] = canonical
    return result


def _validate_identity(entries: list[CatalogEntry]) -> None:
    identities: dict[str, str] = {}
    for entry in entries:
        for identity in [entry.id, *entry.aliases]:
            if identity in identities:
                raise CatalogValidationError(
                    f"Catalog identity '{identity}' is shared by "
                    f"'{identities[identity]}' and '{entry.id}'"
                )
            identities[identity] = entry.id


def _validate_evidence(entries: list[CatalogEntry]) -> None:
    for entry in entries:
        try:
            validate_catalog_evidence(entry)
        except CatalogEvidenceError as error:
            raise CatalogValidationError(str(error)) from error
        validation = entry.validation_result
        if validation.status == "passed" and not validation.environment:
            raise CatalogValidationError(
                f"Catalog entry '{entry.id}' claims passed validation "
                "without environment evidence"
            )
