"""Read-only catalog projection for the existing workspace-bound MCP gateway."""

from urllib.parse import urlencode

from starlette.concurrency import run_in_threadpool

from tool_registry.capability_views import CapabilityFilters
from tool_registry.gateway_management import GatewayManagementToolSpec

from api.services.mcp_services import McpApiService


def capability_discovery_tools(engine):
    # Same active catalog, curation, cached observation and user-state owner as
    # the library REST endpoint. These methods neither probe nor launch tools.
    service = McpApiService(engine, app_state=None)

    async def search(session, arguments):
        scope = arguments.get("scope", "curated")
        page = await run_in_threadpool(
            service.list_capabilities,
            filters=CapabilityFilters(
                search=arguments.get("search") or None,
                curation=frozenset(
                    {"curated", "follow_up"} if scope == "candidates" else {"curated"}
                ),
                protocols=frozenset({"mcp", "webmcp"}),
                domains=frozenset(arguments.get("domains", [])),
            ),
            limit=arguments.get("limit", 6),
            cursor=arguments.get("cursor"),
        )
        capabilities = []
        for view in page.capabilities:
            capabilities.append(
                {
                    "capability_id": view.capability_id,
                    "canonical_id": view.canonical_id,
                    "name": view.name,
                    "description": view.description,
                    "capability_summary": view.capability_summary,
                    "domains": view.domains,
                    "integration_kind": view.integration_kind,
                    "transport": view.transport,
                    "locality": view.locality,
                    "installability_tier": view.installability_tier,
                    "risk_level": view.risk_level,
                    "curation": view.curation.model_dump(mode="json"),
                    "compatibility": view.compatibility.model_dump(mode="json"),
                    "requirements": view.requirements,
                    "installed": view.user_state.installed,
                    "server_id": view.user_state.server_id,
                    "active": view.user_state.active,
                    "explicit_disabled": view.user_state.explicit_disabled,
                    # Never expose another workspace's membership or credentials.
                    "enabled_in_this_workspace": any(
                        item.get("workspace_id") == session.workspace_id
                        for item in view.user_state.enabled_workspaces
                    ),
                    "setup_path": "/tool-registry?"
                    + urlencode({"curation": "all", "search": view.capability_id}),
                }
            )
        return {
            "workspace_id": session.workspace_id,
            "snapshot": page.snapshot.model_dump(mode="json"),
            "scope": scope,
            "capabilities": capabilities,
            "total": page.total,
            "next_cursor": page.next_cursor,
        }

    return [
        (
            GatewayManagementToolSpec(
                name="wright__search_engineering_capabilities",
                description=(
                    "Search Wright's current engineering MCP/WebMCP catalog by a "
                    "short literal keyword, provider name or exact ID, optionally "
                    "filtered by domain. Returns setup links, current qualification, "
                    "cached computer compatibility and installation state. The "
                    "curated scope includes currently recommended records; the "
                    "explicit candidates scope also includes unqualified follow-up "
                    "records. Neither scope establishes availability. Read-only: "
                    "no computer probes, endpoint calls, installs or approvals."
                ),
                input_schema={
                    "type": "object",
                    "properties": {
                        "search": {"type": "string", "maxLength": 120},
                        "domains": {
                            "type": "array",
                            "maxItems": 8,
                            "uniqueItems": True,
                            "items": {
                                "type": "string",
                                "minLength": 1,
                                "maxLength": 80,
                            },
                        },
                        "scope": {"enum": ["curated", "candidates"]},
                        "limit": {"type": "integer", "minimum": 1, "maximum": 12},
                        "cursor": {"type": "string", "minLength": 1, "maxLength": 8192},
                    },
                    "additionalProperties": False,
                },
                output_schema={"type": "object"},
            ),
            search,
        )
    ]
