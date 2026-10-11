"""Fixed Hermes SDK worker: tool-free authoring or provider-side image output.

Executed by the qualified installed Hermes Python with a trusted runtime root.
Credentials remain inside its official resolver/client and never enter stdout.
"""

from __future__ import annotations

import contextlib
import hashlib
import json
import os
from pathlib import Path
import sys


class WorkflowSdkConfigurationChangedError(ValueError):
    pass


def initialize_sdk_profile():
    """Use the installed CLI's profile and credential loaders before SDK imports.

    The parent process keeps its environment. The confined child must resolve
    the same named profile used by setup instead of reading the root defaults.
    No project directory dotenv or agent/CLI entry point is loaded here.
    """
    from hermes_cli.profiles import resolve_profile_env

    profile = (
        os.getenv("WRIGHT_HERMES_PROFILE") or os.getenv("HERMES_PROFILE") or "wright"
    ).strip() or "wright"
    os.environ["HERMES_HOME"] = resolve_profile_env(profile)
    from hermes_cli.env_loader import load_hermes_dotenv

    load_hermes_dotenv(hermes_home=os.environ["HERMES_HOME"])


def invoke(request: dict, runtime_root: Path, *, sdk_observer=None) -> dict:
    image_request = request.get("operation") in {"probe-image", "generate-image"}
    allowed = {"operation", "messages", "expected_resolution"}
    if request.get("operation") == "generate-workflow":
        allowed.add("timeout_seconds")
    if image_request:
        allowed.add("output_format")
    if set(request) - allowed:
        raise ValueError("Unsupported invocation fields")
    if request.get("operation") not in {
        "probe",
        "generate",
        "probe-image",
        "generate-image",
        "generate-workflow",
    }:
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
    sdk_files = [
        "hermes_cli/runtime_provider.py",
        "agent/auxiliary_client.py",
        "hermes_cli/profiles.py",
        "hermes_cli/env_loader.py",
        "hermes_constants.py",
    ]
    if image_request or mode == "codex_responses":
        sdk_files.extend(["agent/codex_runtime.py", "agent/codex_responses_adapter.py"])
    for name in sdk_files:
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
        if request["operation"] == "generate-workflow":
            raise WorkflowSdkConfigurationChangedError(
                "The frozen SDK configuration changed"
            )
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
        if image_request:
            # Fixed provider-side image tool only. No AIAgent, MCP, shell or executor.
            if __package__:
                from .hermes_image import image_capabilities, generate_native_image
            else:
                from hermes_image import image_capabilities, generate_native_image

            return (
                image_capabilities(client, public)
                if request["operation"] == "probe-image"
                else generate_native_image(
                    client, public, request, sdk_observer=sdk_observer
                )
            )
        messages = request.get("messages")
        workflow_request = request["operation"] == "generate-workflow"
        timeout_seconds = request.get("timeout_seconds", 120)
        if type(timeout_seconds) is not int or not 30 <= timeout_seconds <= 600:
            raise ValueError("Invalid model request timeout")
        if (
            not isinstance(messages, list)
            or len(messages) != 2
            or [item.get("role") for item in messages if isinstance(item, dict)]
            != ["system", "user"]
            or any(
                set(item) != {"role", "content"}
                or not (
                    isinstance(item["content"], str)
                    or (
                        workflow_request
                        and item.get("role") == "user"
                        and isinstance(item["content"], list)
                    )
                )
                for item in messages
            )
        ):
            raise ValueError(
                "Confined authoring requires prepared system instructions and one self-contained user turn"
            )
        if workflow_request and isinstance(messages[1]["content"], list):
            parts = messages[1]["content"]
            if not parts or len(parts) > 512:
                raise ValueError("Invalid workflow content parts")
            for part in parts:
                if not isinstance(part, dict):
                    raise ValueError("Invalid workflow content part")
                if part.get("type") == "text":
                    if set(part) != {"type", "text"} or not isinstance(
                        part["text"], str
                    ):
                        raise ValueError("Invalid workflow text part")
                elif part.get("type") == "image_url":
                    image = part.get("image_url")
                    if (
                        set(part) != {"type", "image_url"}
                        or not isinstance(image, dict)
                        or set(image) != {"url"}
                        or not isinstance(image["url"], str)
                        or not image["url"].startswith("data:image/")
                    ):
                        raise ValueError(
                            "Workflow images must be inline input artifacts"
                        )
                else:
                    raise ValueError("Unsupported workflow content part")
        if len(json.dumps(messages).encode()) > (
            16_777_216 if workflow_request else 2_097_152
        ):
            raise ValueError("Authoring input exceeds its fixed bound")
        sdk_payload = dict(
            model=model,
            messages=messages,
            tools=[],
            tool_choice="none",
            stream=False,
            timeout=timeout_seconds,
            max_tokens=32768,
        )
        if sdk_observer is not None:
            sdk_observer(sdk_payload, public)
        response = client.chat.completions.create(**sdk_payload)
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
            **(
                {"usage": response.usage.model_dump(mode="json")}
                if workflow_request
                and callable(
                    getattr(getattr(response, "usage", None), "model_dump", None)
                )
                else {}
            ),
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
    if isinstance(error, WorkflowSdkConfigurationChangedError):
        return "WORKFLOW_MODEL_CHANGED"
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
    evidence_path = Path(sys.argv[2]) if len(sys.argv) == 3 else None
    invocations = []

    def persist_evidence():
        if evidence_path is None:
            return
        encoded = json.dumps(
            {
                "schema_version": "wright.scoped-sdk-evidence/1",
                "invocations": invocations,
            }
        ).encode()
        if len(encoded) > 2_097_152:
            raise ValueError("SDK invocation evidence exceeds its bound")
        temporary = evidence_path.with_suffix(".tmp")
        temporary.write_bytes(encoded)
        os.replace(temporary, evidence_path)

    def capture_sdk(payload, resolution):
        from hermes_sdk_evidence import sdk_invocation_evidence

        invocations.append(sdk_invocation_evidence(payload, resolution))
        persist_evidence()

    try:
        raw = sys.stdin.buffer.read(16_800_001)
        if len(raw) > 16_800_000:
            raise ValueError("Invocation exceeds its fixed bound")
        request = json.loads(raw)
        if not isinstance(request, dict):
            raise ValueError("Invocation must be a JSON object")
        if (
            request.get("operation") not in {"probe-image", "generate-image"}
            and request.get("operation") != "generate-workflow"
            and len(raw) > 2_200_000
        ):
            raise ValueError("Authoring invocation exceeds its fixed bound")
        # Upstream SDK logging does not enter the structured result channel.
        with contextlib.redirect_stdout(sys.stderr):
            # The qualified worker is launched with -I; permit only our bundled adapter.
            sys.path.insert(0, str(Path(__file__).resolve().parent))
            initialize_sdk_profile()
            result = invoke(request, root, sdk_observer=capture_sdk)
            for invocation in invocations:
                invocation["upstream_reported_model"] = result.get("response_model")
            persist_evidence()
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
