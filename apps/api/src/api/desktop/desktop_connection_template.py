"""Public connection draft projection. Never reads credential values or mutates."""

import shlex
from urllib.parse import urlsplit

from core.redaction import REDACTED, SECRET_KEY_RE, redact_command, redact_text


def replacement_template(server):
    """Prepare a fresh named connection; existing authority is never transferred."""
    # Only reviewed imports declare these literal launch settings public. A
    # legacy/catalog row may contain private overrides; never guess its values.
    if server.deployment_mode != "user-reviewed-import":
        return None
    env = []
    headers = []
    if isinstance(server.env_vars, list):
        for item in server.env_vars:
            (headers if item.target == "http_header" else env).append(item.name)
    elif isinstance(server.env_vars, dict):
        # Old dictionary entries may contain plaintext; copy names only.
        env = list(server.env_vars)
    public = {}
    for key, value in server.launch_env.items():
        if key not in env:
            env.append(key)
        if not SECRET_KEY_RE.search(key) and redact_text(value) == value:
            public[key] = value
    if len(env) > 32 or len(headers) > 32:
        return None
    result = {"name": "", "environmentFields": env, "publicCandidates": public}
    if server.type == "stdio":
        try:
            parts = (
                shlex.split(server.command)
                if isinstance(server.command, str)
                else list(server.command or [])
            )
        except ValueError:
            return None
        if (
            not parts
            or headers
            or REDACTED in " ".join(parts)
            or redact_command(parts) != " ".join(parts)
        ):
            return None
        return {
            **result,
            "type": "stdio",
            "command": parts[0],
            "arguments": parts[1:],
            "url": "",
        }
    if server.type == "sse" and isinstance(server.command, str):
        parsed = urlsplit(server.command)
        if (
            parsed.scheme != "https"
            or not parsed.hostname
            or parsed.username
            or parsed.password
            or parsed.query
            or parsed.fragment
            or env
        ):
            return None
        return {
            **result,
            "type": "https",
            "command": "",
            "arguments": [],
            "url": server.command,
            **({"headerFields": headers} if headers else {}),
        }
    return None
