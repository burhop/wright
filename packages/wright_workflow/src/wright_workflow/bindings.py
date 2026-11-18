"""Qualify tool identities without changing the meaning of recorded gateway digests."""

import hashlib
import json


def schema_digest(tool):
    material = {
        "server": tool.server_id,
        "name": tool.name,
        "input": dict(tool.input_schema),
        "output": tool.output_schema,
        "authority": tool.provenance.get("server_revision"),
        "approvals": sorted(tool.required_approvals),
    }
    if tool.upstream_meta.get("wright/operation"):
        material["operation_adapter"] = tool.upstream_meta["wright/operation"]
    if tool.upstream_meta.get("wright/approved-operation"):
        material["approved_operation_adapter"] = tool.upstream_meta[
            "wright/approved-operation"
        ]
    if tool.upstream_meta.get("wright/application"):
        material["application_adapter"] = tool.upstream_meta["wright/application"]
    if tool.upstream_meta.get("wright/terminalOperation"):
        material["terminal_operation"] = tool.upstream_meta["wright/terminalOperation"]
    return hashlib.sha256(
        json.dumps(
            material, sort_keys=True, separators=(",", ":"), default=dict
        ).encode()
    ).hexdigest()
