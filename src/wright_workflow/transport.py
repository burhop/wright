"""Caller-configured MCP sessions shared by readiness and dispatch."""

from contextlib import AsyncExitStack
from datetime import timedelta

from jsonschema import Draft202012Validator, FormatChecker
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client
from referencing import Registry

from .bindings import qualify
from .source import _invalid


def validate_arguments(step, schema, arguments):
    try:
        Draft202012Validator.check_schema(schema)
        validator = Draft202012Validator(
            schema, registry=Registry(), format_checker=FormatChecker()
        )
        validator.validate(arguments)
    except Exception as error:
        raise _invalid(
            f"{step.title}: arguments do not match the qualified tool schema.",
            str(error),
            block_id=step.id,
        ) from error


class Sessions(AsyncExitStack):
    def __init__(self, bindings, root):
        super().__init__()
        self.bindings = bindings
        self.root = root
        self.opened = {}

    async def resolve(self, step):
        server = self.bindings.get(step.server_id)
        if server is None:
            raise _invalid(
                f"{step.title}: the configured MCP server {step.server_id} is unavailable.",
                "Supply its reviewed local binding.",
                block_id=step.id,
            )
        server.verify_build()
        if step.server_id not in self.opened:
            streams = await self.enter_async_context(
                stdio_client(
                    StdioServerParameters(
                        command=server.command, args=list(server.args), cwd=self.root
                    )
                )
            )
            session = await self.enter_async_context(
                ClientSession(*streams, read_timeout_seconds=timedelta(seconds=30))
            )
            initialized = await session.initialize()
            self.opened[step.server_id] = session, initialized.serverInfo
        session, info = self.opened[step.server_id]
        available = {}
        cursor = None
        seen = set()
        while True:
            page = await session.list_tools(cursor=cursor)
            for tool in page.tools:
                if tool.name in available:
                    raise _invalid(f"{step.title}: duplicate upstream tool identity.")
                available[tool.name] = tool
            cursor = page.nextCursor
            if not cursor:
                break
            if cursor in seen or len(seen) >= 128:
                raise _invalid(f"{step.title}: incomplete or repeated tool listing.")
            seen.add(cursor)
        return qualify(step, server, info, available)

    async def call(self, step, tool, arguments):
        session, _ = self.opened[step.server_id]
        return await session.call_tool(
            tool.binding.tool,
            arguments,
            read_timeout_seconds=timedelta(seconds=step.timeout),
        )
