"""One explicit model-only route probe; never starts a workflow or tool operation."""

from __future__ import annotations

import argparse
import asyncio
import json
import os
from pathlib import Path

from agent_adapters.report_generation import generate_workflow_response
from agent_adapters.workflow_model_routing import workflow_model_capabilities
from core.redaction import redact_mapping


async def qualify(*, provider, model, prompt):
    records = []
    report = {
        "status": "blocked",
        "scope": "one model-only execution route probe; not engineering readiness",
        "requested_provider": provider,
        "requested_model": model,
        "invocations": records,
    }

    async def observe(record):
        records.append(redact_mapping(record))

    try:
        if os.getenv("WRIGHT_WORKFLOW_MODEL_TRANSPORT") != "hermes-model-sdk":
            raise ValueError("Select the pilot SDK transport explicitly")
        profile = os.getenv("WRIGHT_HERMES_PROFILE", "").strip()
        if not profile or profile in {"wright", "default"}:
            raise ValueError("Select the isolated pilot profile explicitly")
        capability = await workflow_model_capabilities()
        route = capability["resolution"]
        report["resolved_route"] = route
        if (
            capability.get("available") is not True
            or route["adapter"] != "hermes-model-sdk"
            or route["provider"] != provider
            or route["model_reference"] != model
            or route["profile"] != profile
        ):
            raise ValueError("The resolved route differs from the requested pilot")
        result = await generate_workflow_response(
            prompt,
            "text",
            expected_resolution=route,
            invocation_observer=observe,
        )
        report["response"] = str(result)
        report["usage"] = getattr(result, "wright_usage", {})
        reported = report["usage"].get("model")
        report["upstream_reported_model"] = reported
        # Never equate an arbitrary reported model or revision with the requested
        # alias. Preserve it for review rather than silently accepting substitution.
        report["status"] = (
            "request_completed" if reported == model else "reported_model_needs_review"
        )
    except Exception as error:
        # Provider errors may contain tokens/URLs. Keep the safe class/code only;
        # the adapter's existing redacted invocation owner retains request evidence.
        report["error_type"] = type(error).__name__
        report["error_code"] = getattr(error, "code", None)
    return report


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--expected-provider", required=True)
    parser.add_argument("--expected-model", required=True)
    parser.add_argument("--prompt-file", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    prompt = args.prompt_file.read_text(encoding="utf-8")
    if not prompt.strip() or len(prompt.encode()) > 8192:
        parser.error("Use a nonsecret probe prompt of 1–8192 bytes")
    # Reserve output before any inference; a repeat cannot overwrite evidence.
    args.output.mkdir(parents=True, exist_ok=False)
    report = asyncio.run(
        qualify(
            provider=args.expected_provider, model=args.expected_model, prompt=prompt
        )
    )
    (args.output / "report.json").write_text(
        json.dumps(report, indent=2) + "\n", encoding="utf-8"
    )
    print(
        json.dumps(
            {"status": report["status"], "report": str(args.output / "report.json")}
        )
    )
    return 0 if report["status"] == "request_completed" else 1


if __name__ == "__main__":
    raise SystemExit(main())
