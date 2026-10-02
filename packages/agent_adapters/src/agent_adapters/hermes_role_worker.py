"""Fixed inference-only Hermes SDK worker; never construct AIAgent or execute tools.

Executed by the qualified installed Hermes Python with a trusted runtime root.
Credentials remain inside its official resolver/client and never enter stdout.
"""

from __future__ import annotations

import contextlib
import hashlib
import json
from pathlib import Path
import sys


def invoke(request: dict, runtime_root: Path) -> dict:
    if set(request) - {"operation", "messages", "expected_resolution"}:
        raise ValueError("Unsupported invocation fields")
    if request.get("operation") not in {"probe", "generate"}:
        raise ValueError("Unsupported invocation operation")
    from hermes_cli.runtime_provider import _get_model_config, resolve_runtime_provider
    from agent.auxiliary_client import resolve_provider_client

    config = _get_model_config()
    model = config.get("default")
    if not isinstance(model, str) or not model.strip() or len(model) > 160:
        raise ValueError("Configure an explicit default model in Hermes")
    runtime = resolve_runtime_provider(target_model=model)
    provider = runtime.get("provider")
    mode = runtime.get("api_mode") or "chat_completions"
    if not isinstance(provider, str) or provider in {"auto", "moa", "acp", "codex-cli"}:
        raise ValueError(
            "The configured provider is not qualified for model-only invocation"
        )
    if mode not in {"chat_completions", "codex_responses", "anthropic_messages"}:
        raise ValueError(
            "The configured API mode is not qualified for model-only invocation"
        )
    public = {
        "provider": provider,
        "model_reference": model,
        "api_mode": mode,
        "endpoint_digest": hashlib.sha256(
            str(runtime.get("base_url", "")).encode()
        ).hexdigest(),
    }
    sdk_hashes = {}
    for name in ("hermes_cli/runtime_provider.py", "agent/auxiliary_client.py"):
        sdk_hashes[name] = hashlib.sha256(
            (runtime_root / name).read_bytes()
        ).hexdigest()
    public["sdk_digest"] = hashlib.sha256(
        json.dumps(sdk_hashes, sort_keys=True).encode()
    ).hexdigest()
    public["configuration_digest"] = hashlib.sha256(
        json.dumps(public, sort_keys=True).encode()
    ).hexdigest()
    expected = request.get("expected_resolution")
    if expected is not None and expected != public:
        raise ValueError(
            "The inherited model configuration changed; resolve a new authoring job"
        )
    client, resolved_model = resolve_provider_client(
        provider,
        model=model,
        explicit_base_url=runtime.get("base_url"),
        explicit_api_key=runtime.get("api_key"),
        api_mode=mode,
        main_runtime=runtime,
    )
    if client is None:
        raise ValueError(
            "The default model could not be resolved without changing the model"
        )
    try:
        if resolved_model != model:
            raise ValueError("The model resolver changed the prepared default model")
        if request["operation"] == "probe":
            return {"ok": True, "resolution": public}
        messages = request.get("messages")
        if (
            not isinstance(messages, list)
            or len(messages) != 2
            or [item.get("role") for item in messages if isinstance(item, dict)]
            != ["system", "user"]
            or any(
                set(item) != {"role", "content"} or not isinstance(item["content"], str)
                for item in messages
            )
        ):
            raise ValueError(
                "Confined authoring requires prepared system instructions and one self-contained user turn"
            )
        if len(json.dumps(messages).encode()) > 2_097_152:
            raise ValueError("Authoring input exceeds its fixed bound")
        response = client.chat.completions.create(
            model=model,
            messages=messages,
            tools=[],
            tool_choice="none",
            stream=False,
            timeout=120,
            max_tokens=32768,
        )
        message = response.choices[0].message
        if getattr(message, "tool_calls", None):
            raise ValueError("The model returned a tool request; no tool was executed")
        text = message.content
        if (
            not isinstance(text, str)
            or not text.strip()
            or len(text.encode()) > 1_048_576
        ):
            raise ValueError("The model returned empty or oversized interface source")
        response_model = getattr(response, "model", None)
        if response_model is not None and (
            not isinstance(response_model, str)
            or not response_model.strip()
            or len(response_model) > 160
        ):
            raise ValueError("The provider returned an invalid public model identity")
        return {
            "ok": True,
            "resolution": public,
            "text": text,
            "response_model": response_model,
            "effective_instructions_digest": hashlib.sha256(
                messages[0]["content"].encode()
            ).hexdigest(),
        }
    finally:
        close = getattr(client, "close", None)
        if callable(close):
            close()


def failure_code(error):
    """Fixed categories only; SDK exception text can contain credentials."""
    name = type(error).__name__
    if isinstance(error, TimeoutError) or name in {
        "APITimeoutError",
        "TimeoutException",
    }:
        return "SCOPED_MODEL_TIMEOUT"
    if name in {"AuthenticationError", "PermissionDeniedError"}:
        return "SCOPED_MODEL_AUTH_REQUIRED"
    if name == "RateLimitError":
        return "SCOPED_MODEL_RATE_LIMITED"
    return "SCOPED_INVOCATION_UNAVAILABLE"


def main():
    root = Path(sys.argv[1]).resolve()
    sys.path.insert(0, str(root))
    try:
        raw = sys.stdin.buffer.read(2_200_001)
        if len(raw) > 2_200_000:
            raise ValueError("Invocation exceeds its fixed bound")
        request = json.loads(raw)
        if not isinstance(request, dict):
            raise ValueError("Invocation must be a JSON object")
        # Upstream SDK logging does not enter the structured result channel.
        with contextlib.redirect_stdout(sys.stderr):
            result = invoke(request, root)
    except Exception as error:
        # Auth/SDK exceptions can contain transport secrets; never forward them.
        result = {
            "ok": False,
            "code": failure_code(error),
            "reason": "The confined Hermes model invocation failed. Check its local provider credentials, default model and qualified SDK installation.",
        }
    sys.stdout.write(json.dumps(result))


if __name__ == "__main__":
    main()
