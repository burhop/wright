"""Run and review one real, visible customer attempt in a prepared guest."""

from __future__ import annotations

import argparse
import base64
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import re
import shutil
import subprocess
import sys
import uuid

from .agent import run_agent, redact_record
from .desktop import TOOLS, JOURNEY_TOOL, ACTIVITY_TOOL, VisibleSession, redact_evidence
from .journey import JourneyRecorder, project as project_journey, read_events
from .output_schemas import customer_schema, evaluator_schema
from .provision import load_config
from .reports import (
    OBSERVATION_SCOPES,
    audit_report,
    compare_calibration,
    load_observation_context,
    load_report,
    render_report,
)
from .storyboard import export_storyboard
from .vm import VMBackend, VMError, sha256

ASSETS = Path(__file__).parent / "assets"


def code_mode_helper(binary):
    """Use only the helper adjacent to the selected immutable native CLI."""
    selected = Path(binary).resolve(strict=True)
    helper = selected.parent / "codex-code-mode-host"
    if not helper.is_file() or helper.resolve() != helper:
        raise VMError(
            "Selected native Codex binary lacks its exact adjacent code-mode helper"
        )
    return helper


def model_command(config, owner, role, auth, binary):
    """Expose native CLI/helper binaries and read-only auth, without user state."""
    helper = code_mode_helper(binary)
    identity = "wright-beta-" + role + "-" + uuid.uuid4().hex[:12]
    command = [
        "docker",
        "run",
        "--rm",
        "--pull",
        "never",
        "-i",
        "--name",
        identity,
        "--user",
        f"{config['uid']}:{config['gid']}",
        "--label",
        f"wright.synthetic-beta.owner={owner}",
        "--label",
        f"wright.synthetic-beta.role={role}",
        "--read-only",
        "--cap-drop=ALL",
        "--security-opt=no-new-privileges",
        "--memory=1g",
        "--cpus=1",
        "--pids-limit=128",
        "--tmpfs",
        "/tmp:rw,nosuid,nodev,size=256m",
        "--tmpfs",
        f"/home/ubuntu/.codex:rw,nosuid,nodev,size=64m,mode=700,uid={config['uid']},gid={config['gid']}",
        "--mount",
        f"type=bind,src={auth},dst=/home/ubuntu/.codex/auth.json,readonly",
        "--mount",
        f"type=bind,src={binary},dst=/usr/local/bin/codex,readonly",
        "--mount",
        f"type=bind,src={helper},dst=/usr/local/bin/codex-code-mode-host,readonly",
        "--workdir",
        "/tmp",
        "--entrypoint",
        "/bin/sh",
        config["launcher_image"],
        "-c",
        'mkdir -p /tmp/customer && exec /usr/local/bin/codex -c cli_auth_credentials_store="file" -c features.shell_tool=false -c agents.enabled=false -c web_search="disabled" -c features.apps=false -c features.plugins=false app-server --stdio',
    ]
    return identity, command


def cleanup_model(identity, owner):
    result = subprocess.run(
        ["docker", "inspect", identity], capture_output=True, text=True, timeout=15
    )
    if result.returncode:
        if "No such object" not in result.stderr:
            raise VMError("Cannot verify model-container absence")
        return {"container": identity, "absent": True}
    record = json.loads(result.stdout)[0]
    labels = record.get("Config", {}).get("Labels", {})
    if labels.get("wright.synthetic-beta.owner") != owner:
        raise VMError("Refusing to stop a model container with unknown ownership")
    subprocess.run(
        ["docker", "stop", "--time", "5", record["Id"]],
        check=True,
        capture_output=True,
        timeout=15,
    )
    check = subprocess.run(
        ["docker", "inspect", record["Id"]], capture_output=True, text=True, timeout=15
    )
    if check.returncode == 0 or "No such object" not in check.stderr:
        raise VMError("Model container cleanup not confirmed")
    return {"container": identity, "absent": True}


def run_customer(
    lab_root,
    session_id,
    task_path,
    timeout,
    auth,
    binary,
    model,
    effort,
    *,
    observation_scope="first_contact",
    journey_plan=None,
    guest_session_id=None,
):
    config = load_config(lab_root)
    backend = VMBackend(Path(lab_root) / "machine")
    guest_id = guest_session_id or session_id
    guest_root, _ = backend._load(guest_id)
    root = guest_root
    if guest_id != session_id:
        if observation_scope == "first_contact":
            raise VMError("A repeat visit to an existing guest is not first contact")
        previous = json.loads((guest_root / "customer-session.json").read_text())
        if not previous.get("finished_at"):
            raise VMError("Preserve the unfinished customer before a prepared repeat")
        root = backend._session(session_id)
        # A separate record never adopts or overwrites a prior visit or VM.
        root.mkdir(exist_ok=False)
    if observation_scope not in OBSERVATION_SCOPES:
        raise VMError("Unsupported controller observation scope")
    limit = 3600 if observation_scope in {"first_contact", "prepared_retry"} else 900
    if not 0 < timeout <= limit:
        raise VMError(f"Customer attempt exceeds its {limit}-second observation scope")
    task_template = Path(task_path).read_text()
    instructions = (
        (ASSETS / "customer.md").read_text()
        + "\n"
        + (ASSETS / "journey-observation-v3.md").read_text()
    )
    if (root / "journey-plan.json").exists():
        journey = JourneyRecorder(root)
        if journey_plan and json.loads(Path(journey_plan).read_text()) != journey.plan:
            raise VMError("Requested journey plan differs from frozen clock")
    else:
        if observation_scope == "first_contact":
            raise VMError(
                "Start a whole-journey clock before launching the environment; "
                "first-contact observation cannot start with missing startup timing"
            )
        journey = JourneyRecorder.begin(
            root,
            json.loads(
                Path(journey_plan or ASSETS / "first-workflow-journey.json").read_text()
            ),
            boundary="customer_session_only",
        )
        if guest_id != session_id:
            journey.activity(
                "reviewing_deciding",
                "Prepared repeat begins on the retained signed-in guest; includes controller startup. Prior visit records remain separate.",
            )
    timing_state = project_journey(journey.plan, read_events(root))
    if observation_scope == "first_contact" and timing_state["boundary"] != "whole_journey":
        raise VMError("First-contact observation requires a whole-journey clock")
    if not timing_state["activity_marks"]:
        raise VMError("New customer observations require a continuous activity diary begun before launch")
    if timing_state["finished"] or any(
        s["status"] == "in_progress" for s in timing_state["steps"]
    ):
        raise VMError("Journey clock already ended or has an unfinished operator step")
    task = (
        task_template
        + f"\n\nYour opaque session_id for the final feedback is {session_id}."
        + "\n\nJourney plan:\n"
        + json.dumps(journey.plan)
    )
    identity, command = model_command(config, backend.owner, "customer", auth, binary)
    # Reserve report generation inside the same bounded visit. This deadline
    # controls only observer actions; it never cancels Wright/provider jobs.
    feedback_reserve = min(60, timeout // 4) if observation_scope == "prepared_retry" else 0
    action_budget = timeout - feedback_reserve
    action_limit = 600 if observation_scope == "prepared_retry" else 300
    visible = VisibleSession(
        backend, guest_id, action_budget, max_actions=action_limit,
        recording_id=session_id,
    )
    visible.journey = journey
    schema = customer_schema(session_id)
    (root / "customer-output-schema.json").write_text(
        json.dumps(schema, indent=2) + "\n"
    )
    manifest = {
        "schema_version": 1,
        "session_id": session_id,
        "guest_session_id": guest_id,
        "observation_scope": observation_scope,
        "action_budget_seconds": action_budget,
        "feedback_reserve_seconds": feedback_reserve,
        "action_limit": action_limit,
        "assistance": "none",
        "started_at": datetime.now(timezone.utc).isoformat(),
        "task_digest": hashlib.sha256(task_template.encode()).hexdigest(),
        "instructions_digest": hashlib.sha256(instructions.encode()).hexdigest(),
        "binary_sha256": sha256(Path(binary)),
        "code_mode_helper_sha256": sha256(code_mode_helper(binary)),
        "model_command": command,
        "model": model,
        "effort": effort,
        "output_schema_sha256": hashlib.sha256(
            json.dumps(schema, sort_keys=True, separators=(",", ":")).encode()
        ).hexdigest(),
        "context_isolation": "fresh unprivileged container; only read-only native CLI/adjacent code-mode helper/auth binds; no repository/config/history/AGENTS mount; guest controls are dynamic callbacks",
        "interaction_mode": "guest screenshots/mouse/keyboard; no DOM or private product APIs",
        "activity_diary_version": "continuous-customer-activity-v1",
        "tools_sha256": hashlib.sha256(json.dumps(TOOLS + [JOURNEY_TOOL, ACTIVITY_TOOL], sort_keys=True).encode()).hexdigest(),
        "controller_files_sha256": {
            name: sha256(ASSETS.parent / name)
            for name in ("cli.py", "desktop.py", "journey.py", "activity_diary.py", "agent.py")
        },
        "base_sha256": backend.state(guest_id)["base_sha256"],
        "journey_plan_sha256": sha256(root / "journey-plan.json"),
        "journey_clock_boundary": json.loads(
            (root / "journey-clock.jsonl").read_text().splitlines()[0]
        )["boundary"],
    }
    auth_before = sha256(Path(auth))
    try:
        journey.activity("reviewing_deciding", "AI customer starting to inspect the prepared desktop; includes model/controller startup")
        result = run_agent(
            command,
            instructions,
            task,
            TOOLS + [JOURNEY_TOOL, ACTIVITY_TOOL],
            visible,
            timeout,
            root / "customer-agent",
            model,
            effort,
            redact=lambda value: redact_evidence(redact_record(value)),
            output_schema=schema,
            passive_observer=visible.native_pause,
        )
        manifest["agent_status"] = result["status"]
        if result["status"] == "completed":
            # Preserve the exact final response; parsing never rewrites the feedback.
            final = result["final_text"]
            destination = root / "report.json"
            destination.write_text(final)
            try:
                report = load_report(destination)
                if report.get("session_id") != session_id:
                    raise VMError(
                        "Customer report session differs from its observed guest"
                    )
                (root / "report.md").write_text(render_report(report))
                manifest["report_status"] = "valid-unreviewed"
            except (ValueError, VMError) as error:
                manifest["report_status"] = "invalid-retained"
                manifest["report_error"] = str(error)
        else:
            manifest["report_status"] = "missing-agent-failure"
    finally:
        visible.cancel()
        try:
            journey.finish()
        except (ValueError, OSError) as error:
            # Recording failures must never prevent model-container cleanup.
            manifest["journey_clock_error"] = str(redact_evidence(str(error)))
        try:
            manifest["cleanup"] = cleanup_model(identity, backend.owner)
        except (VMError, OSError, subprocess.SubprocessError) as error:
            manifest["cleanup"] = {
                "container": identity,
                "absent": False,
                "error": str(redact_evidence(str(error))),
            }
            raise
        finally:
            try:
                manifest["original_auth_unchanged"] = auth_before == sha256(Path(auth))
            except OSError:
                manifest["original_auth_unchanged"] = False
            manifest["finished_at"] = datetime.now(timezone.utc).isoformat()
            (root / "customer-session.json").write_text(
                json.dumps(manifest, indent=2) + "\n"
            )
    return manifest


def archive_latest_review(root):
    """Preserve the original latest review before another attempt can replace it."""
    root = Path(root)
    latest = root / "verification.json"
    if not latest.exists():
        return None
    if latest.is_symlink():
        raise VMError("Latest verification cannot be a symlink")
    verification = json.loads(latest.read_text())
    # The model's reported identity is data, not a path authority. Older replies
    # sometimes appended a descriptive suffix to the supplied reviewer ID.
    candidates = []
    for directory in root.iterdir():
        if not re.fullmatch(r"review-[0-9a-f]{12}", directory.name):
            continue
        raw = directory / "final.txt"
        if (
            directory.resolve() != directory
            or not directory.is_dir()
            or raw.is_symlink()
            or not raw.is_file()
        ):
            continue
        try:
            same_response = json.loads(raw.read_text()) == verification
        except ValueError:
            same_response = False
        if same_response:
            candidates.append(directory)
    if len(candidates) != 1:
        raise VMError(
            "Cannot uniquely map latest verification to its retained original reviewer response"
        )
    attempt = candidates[0]
    identity = attempt.name
    archived = []
    for name in ("verification.json", "audit.json"):
        source = root / name
        if source.is_symlink() or not source.is_file():
            raise VMError(f"Latest reviewer evidence missing or unsafe: {name}")
        target = attempt / name
        content = source.read_bytes()
        if target.exists() or target.is_symlink():
            if target.is_symlink() or target.read_bytes() != content:
                raise VMError(f"Refusing to overwrite original review evidence: {name}")
        else:
            with target.open("xb") as stream:
                stream.write(content)
        archived.append(name)
    return {"evaluator_session_id": identity, "archived": archived}


def evaluate(lab_root, session_id, auth, binary, receipts=None, target=None):
    config = load_config(lab_root)
    backend = VMBackend(Path(lab_root) / "machine")
    root, _ = backend._load(session_id)
    report = load_report(root / "report.json")
    if report["session_id"] != session_id:
        raise VMError("Customer report session differs from its observed guest")
    observation = load_observation_context(root, session_id)
    observation_scope = observation["observation_scope"]
    events = [
        json.loads(line) for line in (root / "events.jsonl").read_text().splitlines()
    ]
    # Validate actual capture paths/digests before any reviewer sees them.
    audit_report(report, root, **observation)
    by_id = {event["id"]: event for event in events}
    archive_latest_review(root)
    evaluator_id = "review-" + uuid.uuid4().hex[:12]
    attempt = root / evaluator_id
    request = {
        "session_id": session_id,
        "observation_scope": observation_scope,
        "assistance": observation["assistance"],
        "evaluator_session_id": evaluator_id,
        "events_sha256": sha256(root / "events.jsonl"),
        "customer_report": report,
        "events": events,
        "allowed_event_ids": list(by_id),
        "evidence_refs_format": "Array of exact known event IDs only; capture paths and receipt-field references are not valid IDs. File/receipt details belong in reason.",
        "resulting_state_receipts": json.loads(Path(receipts).read_text())
        if receipts
        else None,
        "registered_target": json.loads(Path(target).read_text()) if target else None,
        "required_verification_shape": {
            "schema_version": 1,
            "session_id": session_id,
            "evaluator_session_id": evaluator_id,
            "events_sha256": sha256(root / "events.jsonl"),
            "stages": [
                {"id": stage["id"], "status": "not_reached", "evidence_refs": []}
                for stage in report["stages"]
            ],
            "findings": [
                {
                    "finding_id": "customer finding ID",
                    "disposition": "supported|unsupported|uncertain",
                    "evidence_refs": [],
                    "reason": "specific evidence or missing proof",
                }
            ],
        },
    }
    schema = evaluator_schema(
        report,
        list(by_id),
        evaluator_id,
        request["events_sha256"],
        request["registered_target"],
        observation_scope=observation_scope,
    )
    schema_digest = hashlib.sha256(
        json.dumps(schema, sort_keys=True, separators=(",", ":")).encode()
    ).hexdigest()
    (root / f"{evaluator_id}-output-schema.json").write_text(
        json.dumps(schema, indent=2) + "\n"
    )
    tools = [
        {
            "type": "function",
            "name": "view_evidence",
            "description": "View the actual retained screenshot for an event from this completed session. No live guest changes or other files.",
            "inputSchema": {
                "type": "object",
                "properties": {"event_id": {"type": "string"}},
                "required": ["event_id"],
                "additionalProperties": False,
            },
        }
    ]

    def view(name, arguments):
        if name != "view_evidence" or set(arguments) != {"event_id"}:
            raise VMError("Evaluator has only session-scoped recorded evidence access")
        event = by_id.get(arguments["event_id"])
        if not event:
            raise VMError("Unknown evidence event")
        value = {"text": json.dumps(event)}
        if event["captures"]:
            capture = event["captures"][0]
            path = root / capture["path"]
            if (
                path.resolve() != path
                or not path.is_relative_to(root)
                or sha256(path) != capture["sha256"]
            ):
                raise VMError("Recorded capture identity changed")
            value["image_url"] = (
                "data:image/png;base64," + base64.b64encode(path.read_bytes()).decode()
            )
        return value

    identity, command = model_command(config, backend.owner, "evaluator", auth, binary)
    (root / f"{evaluator_id}-configuration.json").write_text(
        json.dumps(
            {
                "binary_sha256": sha256(Path(binary)),
                "code_mode_helper_sha256": sha256(code_mode_helper(binary)),
                "model_command": command,
                "requested_model": "gpt-6.1-sol",
                "requested_effort": "high",
                "output_schema_sha256": schema_digest,
            },
            indent=2,
        )
        + "\n"
    )
    try:
        result = run_agent(
            command,
            (
                ASSETS
                / (
                    "evaluator-v5.md"
                    if observation_scope == "calibration_checkpoint_v2"
                    else "evaluator.md"
                )
            ).read_text(),
            "Independently review this completed synthetic beta attempt and return one JSON verification object. Inspect the screens that bear on its consequential claims.\n"
            + json.dumps(request),
            tools,
            view,
            600,
            root / evaluator_id,
            "gpt-6.1-sol",
            "high",
            redact=lambda value: redact_evidence(redact_record(value)),
            output_schema=schema,
        )
        if result["status"] == "completed":
            # Retain the raw response before parsing, audit, cleanup or latest-pointer changes.
            (attempt / "verification.json").write_text(result["final_text"])
    finally:
        cleanup = cleanup_model(identity, backend.owner)
        (root / f"{evaluator_id}-cleanup.json").write_text(
            json.dumps(cleanup, indent=2) + "\n"
        )
    if result["status"] != "completed":
        raise VMError("Independent reviewer failed; its attempt is retained")
    try:
        verification = json.loads(result["final_text"])
        if (
            not isinstance(verification, dict)
            or verification.get("session_id") != session_id
            or verification.get("evaluator_session_id") != evaluator_id
            or verification.get("events_sha256") != request["events_sha256"]
        ):
            raise VMError(
                "Review subject/provenance differs from the exact controller-supplied identities"
            )
        audited = audit_report(report, root, verification=verification, **observation)
    except (ValueError, OSError, VMError) as error:
        (attempt / "audit-error.json").write_text(
            json.dumps(
                {
                    "error": str(redact_evidence(str(error))),
                    "scope": "review response retained unchanged; no reference correction",
                },
                indent=2,
            )
            + "\n"
        )
        raise
    (attempt / "audit.json").write_text(json.dumps(audited, indent=2) + "\n")
    (root / "verification.json").write_bytes(
        (attempt / "verification.json").read_bytes()
    )
    (root / "audit.json").write_bytes((attempt / "audit.json").read_bytes())
    (root / "report.md").write_text(render_report(report, audited))
    return audited


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--lab-root", type=Path, required=True)
    parser.add_argument(
        "--auth", type=Path, default=Path("/home/burhop/.codex/auth.json")
    )
    parser.add_argument(
        "--binary", type=Path, default=Path(shutil.which("codex") or "codex").resolve()
    )
    commands = parser.add_subparsers(dest="command", required=True)
    customer = commands.add_parser("run")
    customer.add_argument("--session", required=True)
    customer.add_argument("--task", type=Path, required=True)
    customer.add_argument(
        "--journey-plan",
        type=Path,
        help="Scenario-specific steps and optional targets; defaults to first workflow A–J",
    )
    customer.add_argument("--timeout", type=int, default=3600)
    customer.add_argument(
        "--observation-scope",
        choices=sorted(OBSERVATION_SCOPES),
        default="first_contact",
    )
    customer.add_argument("--model", default="gpt-6.1-sol")
    customer.add_argument(
        "--effort", default="medium", choices=["low", "medium", "high"]
    )
    reviewer = commands.add_parser("review")
    reviewer.add_argument("--session", required=True)
    reviewer.add_argument("--receipts", type=Path)
    reviewer.add_argument("--target", type=Path)
    audit = commands.add_parser("audit")
    audit.add_argument("--session", required=True)
    storyboard = commands.add_parser("storyboard")
    storyboard.add_argument("--session", required=True)
    storyboard.add_argument("--output", type=Path, required=True)
    compare = commands.add_parser("compare")
    compare.add_argument("--protocol", type=Path, required=True)
    compare.add_argument("--sessions", type=Path, required=True)
    args = parser.parse_args(argv)
    if args.command == "run":
        result = run_customer(
            args.lab_root,
            args.session,
            args.task,
            args.timeout,
            args.auth.resolve(),
            args.binary.resolve(),
            args.model,
            args.effort,
            observation_scope=args.observation_scope,
            journey_plan=args.journey_plan,
        )
    elif args.command == "review":
        result = evaluate(
            args.lab_root,
            args.session,
            args.auth.resolve(),
            args.binary.resolve(),
            args.receipts,
            args.target,
        )
    elif args.command == "audit":
        backend = VMBackend(args.lab_root / "machine")
        root, _ = backend._load(args.session)
        result = audit_report(
            load_report(root / "report.json"),
            root,
            verification=json.loads((root / "verification.json").read_text()),
            **load_observation_context(root, args.session),
        )
    elif args.command == "storyboard":
        backend = VMBackend(args.lab_root / "machine")
        root, _ = backend._load(args.session)
        result = export_storyboard(root, args.output)
    else:
        result = compare_calibration(
            json.loads(args.protocol.read_text()), json.loads(args.sessions.read_text())
        )
    print(json.dumps(result, indent=2))
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except (VMError, ValueError, OSError) as error:
        print(f"Synthetic beta operation incomplete: {error}", file=sys.stderr)
        raise SystemExit(1)
