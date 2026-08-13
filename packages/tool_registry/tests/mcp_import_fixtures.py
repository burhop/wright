CLAUDE_MULTI_SERVER = {
    "mcpServers": {
        "local": {
            "command": "uvx",
            "args": ["safe-mcp"],
            "env": {"API_TOKEN": "secret-value"},
        },
        "remote": {"type": "http", "url": "https://example.invalid/mcp"},
    }
}

VSCODE_WITH_INPUT = {
    "inputs": [{"id": "token", "type": "promptString", "password": True}],
    "servers": {
        "remote": {
            "type": "http",
            "url": "https://example.invalid/mcp",
            "headers": {"Authorization": "Bearer ${input:token}"},
        }
    },
}

PLAIN_LOCAL = {"name": "local", "command": "python", "args": ["server.py"]}

ADVERSARIAL_LOCAL = {
    "name": "adversarial",
    "command": "python; Remove-Item -Recurse C:/unsafe",
    "args": ["$(whoami)", "`hostname`"],
    "env": {"PASSWORD": "do-not-persist"},
}

OVERSIZED_DOCUMENT = (
    '{"mcpServers": {'
    + ('"server": {"command": "uvx", "args": ["server"]},' * 6000)
    + '"last": {"command": "uvx"}}}'
)
