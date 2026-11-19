"""Bind native run-path tokens only in explicitly templated fields."""

from .source import _invalid

VERSION = "wright.run-path/1"
TOKEN = "{{wright.run_id}}"
ATTEMPT_TOKEN = "{{wright.producer_attempt}}"
RESERVED = "{{wright."


def _map(value, run_id, *, allow_attempt=False):
    if isinstance(value, str):
        result = value.replace(TOKEN, run_id)
        inspected = result.replace(ATTEMPT_TOKEN, "") if allow_attempt else result
        if RESERVED in inspected:
            raise _invalid("A run-path template contains an unsupported Wright token.")
        return result
    if isinstance(value, dict):
        if any(RESERVED in str(key) for key in value):
            raise _invalid("Run-path templates cannot change object keys.")
        return {
            key: _map(item, run_id, allow_attempt=allow_attempt)
            for key, item in value.items()
        }
    if isinstance(value, (tuple, list)):
        items = [_map(item, run_id, allow_attempt=allow_attempt) for item in value]
        return tuple(items) if isinstance(value, tuple) else items
    return value


def _contains(value):
    if isinstance(value, str):
        return RESERVED in value
    if isinstance(value, dict):
        return any(_contains(key) or _contains(item) for key, item in value.items())
    if isinstance(value, (tuple, list)):
        return any(_contains(item) for item in value)
    return False


def _root(path, run_id, *, allow_attempt=False):
    from .arguments import _safe_path

    parts = path.split("/")
    if parts.count(TOKEN) != 1 or TOKEN not in parts[:-1]:
        raise _invalid(
            "A run-scoped output needs one run-id directory component before its filename."
        )
    resolved = _safe_path(_map(path, run_id, allow_attempt=allow_attempt))
    return resolved, "/".join(parts[: parts.index(TOKEN)] + [run_id])


def bind_template(settings, run_id):
    version = settings.get("run_path_template", "")
    if not version:
        if _contains(settings):
            raise _invalid("A Wright run token needs an explicit run-path declaration.")
        return settings
    if version != VERSION:
        raise _invalid(
            "This runner requires a qualified handler for this run-path version."
        )
    allowed = {
        "mcp_arguments",
        "mcp_file_dependencies",
        "expected_files",
        "expected_file_ports",
        "output_filename",
    }
    result = {}
    for name, value in settings.items():
        if name not in allowed and _contains(value):
            raise _invalid(
                "A run token cannot change provider identity or execution authority."
            )
        result[name] = _map(value, run_id) if name in allowed else value
    for path in settings.get("expected_files", "").splitlines():
        if path.strip():
            _root(path.strip(), run_id)
    if settings.get("save_output") and settings.get("output_filename"):
        _root(settings["output_filename"], run_id)
    return result
