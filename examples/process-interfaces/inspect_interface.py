"""Read scoped authoring availability or an existing job through Wright's API."""

import argparse
import json
import os
import re
from urllib.parse import urlsplit

import httpx

from agent_adapters.base import AgentInvocationCapabilities
from core.process_interactions import ProcessRef, Reason
from core.process_interfaces import AuthoringJob

IDENTIFIER = re.compile(r"[a-zA-Z0-9][a-zA-Z0-9._:-]{0,159}\Z")
MAX_RESPONSE_BYTES = 1_048_576


def api_origin(value):
    parsed = urlsplit(value)
    if (
        parsed.scheme not in {"http", "https"}
        or not parsed.hostname
        or parsed.username is not None
        or parsed.password is not None
        or parsed.path not in {"", "/"}
        or parsed.query
        or parsed.fragment
    ):
        raise argparse.ArgumentTypeError(
            "Use the Wright API origin without credentials or a path."
        )
    return value.rstrip("/")


def identifier(value):
    if not IDENTIFIER.fullmatch(value):
        raise argparse.ArgumentTypeError("Use a bounded Wright identifier.")
    return value


def inspect(client, process, session_id, job_id=None):
    query = {
        "session_id": session_id,
        "path": process.source_path,
        "expected_storage_digest": process.source_digest,
    }
    endpoint = (
        f"authoring-jobs/{identifier(job_id)}" if job_id else "authoring-capabilities"
    )
    with client.stream(
        "GET", "/api/workspace/process-interfaces/" + endpoint, params=query
    ) as response:
        response.raise_for_status()
        data = bytearray()
        for chunk in response.iter_bytes():
            data.extend(chunk)
            if len(data) > MAX_RESPONSE_BYTES:
                raise ValueError("Wright's response exceeded the example's read bound.")
    value = json.loads(data)
    if job_id:
        job = AuthoringJob.model_validate(value["job"])
        if job.process != process or job.job_id != job_id:
            raise ValueError(
                "The returned job does not match the requested process and job."
            )
        return {
            "operation": "job-status",
            "job_id": job.job_id,
            "state": job.state,
            "revision_id": job.revision_id,
            "adapter": job.role_resolution.adapter,
            "model": job.role_resolution.model_reference,
            "diagnostic_codes": [reason.code for reason in job.diagnostics],
        }
    actual = ProcessRef.model_validate(value["process"])
    if actual != process or value["role"] != "process-ui-author/1":
        raise ValueError(
            "The returned authoring scope does not match the requested process."
        )
    model = AgentInvocationCapabilities(**value["model"])
    if type(value["available"]) is not bool:
        raise ValueError("Invalid authoring availability response.")
    compiler = value["compiler"]
    if compiler is not None and not isinstance(compiler, dict):
        raise ValueError("Invalid compiler availability response.")
    reason = (
        Reason.model_validate(value["compiler_reason"])
        if value.get("compiler_reason") is not None
        else None
    )
    if value["available"] and (not model.available or compiler is None):
        raise ValueError(
            "Authoring availability contradicts its required capabilities."
        )
    return {
        "operation": "authoring-capabilities",
        "available": value["available"],
        "role": value["role"],
        "adapter": model.adapter,
        "model": model.model_reference,
        "compiler_available": compiler is not None,
        "compiler_reason_code": reason.code if reason else None,
    }


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--api", required=True, type=api_origin)
    parser.add_argument("--workspace-id", required=True, type=identifier)
    parser.add_argument("--session", required=True, type=identifier)
    parser.add_argument("--source", required=True)
    parser.add_argument("--digest", required=True)
    parser.add_argument(
        "--job",
        type=identifier,
        help="Read one existing job instead of authoring availability.",
    )
    args = parser.parse_args(argv)
    token = os.environ.get("WRIGHT_API_TOKEN")
    if not token:
        parser.error(
            "Configure WRIGHT_API_TOKEN in the authenticated operator environment."
        )
    try:
        process = ProcessRef(
            workspace_id=args.workspace_id,
            source_path=args.source,
            source_digest=args.digest,
        )
        with httpx.Client(
            base_url=args.api,
            headers={"Authorization": "Bearer " + token},
            timeout=60,
            follow_redirects=False,
        ) as client:
            result = inspect(client, process, args.session, args.job)
        print(json.dumps(result, indent=2))
        return 0
    except httpx.HTTPStatusError as error:
        print(
            json.dumps(
                {
                    "error": "WRIGHT_READ_REJECTED",
                    "http_status": error.response.status_code,
                }
            )
        )
    except httpx.RequestError:
        print(json.dumps({"error": "WRIGHT_READ_UNAVAILABLE"}))
    except (ValueError, KeyError, TypeError):
        print(json.dumps({"error": "WRIGHT_RESPONSE_INVALID"}))
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
