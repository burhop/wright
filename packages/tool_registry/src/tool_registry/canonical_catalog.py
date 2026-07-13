from __future__ import annotations

import json
from importlib.resources import files
from typing import Any

import yaml
from jsonschema import Draft202012Validator

from .catalog_loader import catalog_entry_to_mcp_seed
from .catalog_models import CatalogEntry
from .mcp_catalog import tier_sort_key

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


def load_catalog_document() -> dict[str, Any]:
    catalog_text = files(CATALOG_PACKAGE).joinpath(CATALOG_RESOURCE).read_text("utf-8")
    document = yaml.safe_load(catalog_text)
    if not isinstance(document, dict) or document.get("format_version") != 1:
        raise CatalogValidationError("Canonical catalog format_version must be 1")
    raw_servers = document.get("servers")
    if not isinstance(raw_servers, list):
        raise CatalogValidationError("Canonical catalog servers must be a list")
    schema = json.loads(
        files(CATALOG_PACKAGE).joinpath(SCHEMA_RESOURCE).read_text("utf-8")
    )
    validator = Draft202012Validator(schema)
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


def load_canonical_entries() -> list[CatalogEntry]:
    return [
        CatalogEntry.model_validate(entry)
        for entry in load_catalog_document()["servers"]
    ]


def load_engineering_catalog() -> list[dict[str, Any]]:
    result: list[dict[str, Any]] = []
    for entry in load_canonical_entries():
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
        validation = entry.validation_result
        if validation.status == "passed" and not validation.environment:
            raise CatalogValidationError(
                f"Catalog entry '{entry.id}' claims passed validation "
                "without environment evidence"
            )
