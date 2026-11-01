"""Preserve customer feedback and independently audit its recorded support.

All functions are stdlib-only. An audit establishes record consistency, not that
an evaluator is truthful or that a screen establishes an engineering result.
The controller must produce evaluator records in a separate, restricted session.
Neither customer prose nor an event saying "success" grants a completed stage.
"""

from __future__ import annotations

import hashlib
import html
import json
from datetime import datetime
from pathlib import Path, PurePosixPath
from typing import Any

STAGES = (
    "install_wright",
    "create_workspace",
    "install_mcp",
    "call_mcp",
    "inspect_result",
    "reopen_workspace",
)
OUTCOMES = {
    "independent_completion",
    "completion_with_help",
    "partial_progress",
    "justified_stop",
    "lab_failure",
}
STATUSES = {"completed", "failed", "not_reached", "abandoned"}
IMPACTS = {
    "blocked_progress",
    "caused_rework",
    "required_help",
    "caused_uncertainty",
    "minor_friction",
}
CONTEXT_KEYS = {
    "baseline_digest",
    "task_digest",
    "model",
    "effort",
    "help_policy_digest",
    "inputs_digest",
    "checkpoint_digest",
    "instructions_digest",
}
OBSERVATION_SCOPES = {
    "first_contact",
    "prepared_retry",
    "calibration_checkpoint",
    "calibration_checkpoint_v2",
}
ASSISTANCE = {"none", "external"}


class ReportError(ValueError):
    """Malformed feedback, evidence, or comparison input."""


def _text(value: Any, where: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise ReportError(f"{where}: expected nonempty text")
    return value


def _list(value: Any, where: str) -> list:
    if not isinstance(value, list):
        raise ReportError(f"{where}: expected array")
    return value


def _object(value: Any, where: str) -> dict:
    if not isinstance(value, dict):
        raise ReportError(f"{where}: expected object")
    return value


def _time(value: Any, where: str) -> datetime:
    try:
        parsed = datetime.fromisoformat(_text(value, where).replace("Z", "+00:00"))
        if parsed.tzinfo is None:
            raise ValueError("timezone absent")
        return parsed
    except ValueError as exc:
        raise ReportError(f"{where}: expected timezone-aware ISO timestamp") from exc


def _refs(value: Any, where: str) -> list[str]:
    refs = _list(value, where)
    for ref in refs:
        _text(ref, where)
    if len(set(refs)) != len(refs):
        raise ReportError(f"{where}: duplicate event reference")
    return refs


def _stages(value: Any, where: str, *, complete: bool = True) -> dict[str, dict]:
    result = {}
    for item in _list(value, where):
        _object(item, where)
        stage = _text(item.get("id"), f"{where}.id")
        if stage not in STAGES or stage in result:
            raise ReportError(f"{where}: unknown or repeated stage {stage}")
        if item.get("status") not in STATUSES:
            raise ReportError(f"{where}.{stage}: invalid status")
        _refs(item.get("evidence_refs"), f"{where}.{stage}.evidence_refs")
        result[stage] = item
    if complete and set(result) != set(STAGES):
        raise ReportError(f"{where}: all six journey stages must be accounted for")
    return result


def validate_report(report: dict) -> dict:
    """Validate shape without modifying the original customer account."""
    _object(report, "report")
    if report.get("schema_version") != 1:
        raise ReportError("report.schema_version: expected 1")
    for key in (
        "session_id",
        "expectation",
        "task",
        "accomplishment",
        "stopping_reason",
    ):
        _text(report.get(key), f"report.{key}")
    if report.get("outcome") not in OUTCOMES:
        raise ReportError("report.outcome: invalid outcome")
    _stages(report.get("stages"), "report.stages")
    for key in ("positives", "uncertainties", "help"):
        for item in _list(report.get(key), f"report.{key}"):
            _object(item, key)
            _text(item.get("text"), f"{key}.text")
            _refs(item.get("evidence_refs"), f"{key}.evidence_refs")
    findings = set()
    for item in _list(report.get("friction"), "report.friction"):
        _object(item, "friction")
        identity = _text(item.get("id"), "friction.id")
        if identity in findings:
            raise ReportError(f"duplicate finding {identity}")
        findings.add(identity)
        for key in (
            "stage",
            "observation",
            "expected",
            "consequence",
            "interpretation",
            "suggestion",
        ):
            _text(item.get(key), f"friction.{key}")
        if item.get("impact") not in IMPACTS:
            raise ReportError("friction.impact: invalid impact")
        _refs(item.get("evidence_refs"), "friction.evidence_refs")
    priorities = _list(report.get("priorities"), "report.priorities")
    if len(priorities) > 3:
        raise ReportError("at most three supported priorities")
    seen = set()
    for item in priorities:
        _object(item, "priority")
        if item.get("finding_id") not in findings or item["finding_id"] in seen:
            raise ReportError("priority must reference a unique existing finding")
        seen.add(item["finding_id"])
        _text(item.get("recommendation"), "priority.recommendation")
    return report


def load_report(path: str | Path) -> dict:
    return validate_report(json.loads(Path(path).read_text(encoding="utf-8")))


def load_observation_context(session_root: str | Path, session_id: str) -> dict:
    """Read controller metadata, never a customer claim or task interpretation."""
    path = Path(session_root) / "customer-session.json"
    if path.is_symlink():
        raise ReportError("controller session manifest cannot be a symlink")
    if not path.exists():
        return {"observation_scope": "first_contact", "assistance": "none"}
    manifest = _object(json.loads(path.read_text()), "controller session manifest")
    if manifest.get("schema_version") != 1 or manifest.get("session_id") != session_id:
        raise ReportError("controller observation scope belongs to another session")
    scope = manifest.get("observation_scope", "first_contact")
    if not isinstance(scope, str) or scope not in OBSERVATION_SCOPES:
        raise ReportError("unsupported controller observation scope")
    assistance = manifest.get("assistance", "none")
    if not isinstance(assistance, str) or assistance not in ASSISTANCE:
        raise ReportError("unsupported controller assistance classification")
    return {"observation_scope": scope, "assistance": assistance}


def load_observation_scope(session_root: str | Path, session_id: str) -> str:
    return load_observation_context(session_root, session_id)["observation_scope"]


def _capture(root: Path, item: dict) -> str:
    _object(item, "capture")
    name = _text(item.get("path"), "capture.path")
    relative = PurePosixPath(name)
    if (
        relative.is_absolute()
        or ".." in relative.parts
        or "\\" in name
        or ":" in name
        or name in {".", ""}
    ):
        raise ReportError(f"unsafe capture path: {name}")
    path = root / name
    # Reject symlinks even when they currently point inside the session root.
    current = root
    for part in relative.parts:
        current = current / part
        if current.is_symlink():
            raise ReportError(f"symlink capture path: {name}")
    if not path.resolve().is_relative_to(root) or not path.is_file():
        raise ReportError(f"capture missing or out of scope: {name}")
    digest = hashlib.sha256(path.read_bytes()).hexdigest()
    if item.get("sha256") != digest:
        raise ReportError(f"capture digest mismatch: {name}")
    return name


def audit_report(
    report: dict,
    session_root: str | Path,
    *,
    verification: dict | None = None,
    observation_scope: str = "first_contact",
    assistance: str = "none",
) -> dict:
    """Cross-check feedback against files and a separate evaluator's findings.

    Return an audit without rewriting feedback. Missing evaluator support is
    explicit uncertainty; false completion claims make the audit rejected.
    """
    validate_report(report)
    if observation_scope not in OBSERVATION_SCOPES:
        raise ReportError("unsupported controller observation scope")
    if assistance not in ASSISTANCE:
        raise ReportError("unsupported controller assistance classification")
    root = Path(session_root).resolve(strict=True)
    issues: list[str] = []
    rejected: list[str] = []
    blockers: list[str] = []

    def reject(message: str, *, blocking: bool = True):
        rejected.append(message)
        if blocking:
            blockers.append(message)

    events: dict[str, dict] = {}
    events_path = root / "events.jsonl"
    if events_path.is_symlink():
        raise ReportError("events.jsonl must not be a symlink")
    event_bytes = events_path.read_bytes()
    event_digest = hashlib.sha256(event_bytes).hexdigest()
    previous_time = None
    for index, line in enumerate(event_bytes.decode("utf-8").splitlines(), 1):
        if not line.strip():
            continue
        event = _object(json.loads(line), f"event {index}")
        identity = _text(event.get("id"), "event.id")
        if identity in events:
            raise ReportError(f"duplicate event {identity}")
        if event.get("session_id") != report["session_id"]:
            raise ReportError("event belongs to another session")
        instant = _time(event.get("time"), "event.time")
        if previous_time is not None and instant < previous_time:
            raise ReportError("events are not in chronological order")
        previous_time = instant
        action = event.get("action")
        if isinstance(action, dict):
            _text(action.get("tool"), "event.action.tool")
            if action["tool"] == "desktop":
                _text(action.get("action"), "event.action.action")
            elif action["tool"] == "feedback_note":
                _text(action.get("text"), "event.action.text")
                _refs(action.get("evidence_refs"), "event.action.evidence_refs")
            elif action["tool"] in {"journey_step", "activity_note"}:
                # Existing timing hooks record observations, not product actions.
                # They cannot supply the captures required to verify a claim.
                _refs(action.get("evidence_refs", []), "event.action.evidence_refs")
                if event.get("captures") != []:
                    raise ReportError("timing observations cannot supply captures")
            else:
                raise ReportError(
                    "event.action.tool: unsupported recorded customer tool"
                )
        else:
            _text(action, "event.action")
        _text(event.get("observed_result"), "event.observed_result")
        captures = _list(event.get("captures"), "event.captures")
        for capture in captures:
            _capture(root, capture)
        events[identity] = event

    def supported_refs(
        refs: list[str], label: str, *, require: bool = True, blocking: bool = True
    ) -> bool:
        if require and not refs:
            reject(f"{label}: no evidence references", blocking=blocking)
            return False
        missing = set(refs) - events.keys()
        if missing:
            reject(
                f"{label}: unknown event references {sorted(missing)}",
                blocking=blocking,
            )
            return False
        # An unsupported textual success event alone is insufficient evidence.
        if require and not any(events[ref]["captures"] for ref in refs):
            reject(f"{label}: no retained capture or artifact", blocking=blocking)
            return False
        return True

    report_stages = _stages(report["stages"], "report.stages")
    for key in ("positives", "uncertainties", "help"):
        for index, item in enumerate(report[key]):
            supported_refs(item["evidence_refs"], f"{key}[{index}]", require=False)
    evaluator_findings: dict[str, dict] = {}
    evaluator_stages: dict[str, dict] = {}
    qualified_verification = False
    if verification is not None:
        _object(verification, "verification")
        if (
            verification.get("schema_version") != 1
            or verification.get("session_id") != report["session_id"]
            or not verification.get("evaluator_session_id")
            or verification["evaluator_session_id"] == report["session_id"]
            or verification.get("events_sha256") != event_digest
        ):
            reject(
                "verification identity or event digest does not match independent evaluation"
            )
        else:
            qualified_verification = True
            evaluator_stages = _stages(
                verification.get("stages"), "verification.stages"
            )
            customer_finding_ids = {item["id"] for item in report["friction"]}
            for item in _list(verification.get("findings"), "verification.findings"):
                _object(item, "verification finding")
                identity = _text(item.get("finding_id"), "verification.finding_id")
                if identity not in customer_finding_ids:
                    raise ReportError(
                        "evaluator finding references unknown customer finding"
                    )
                if identity in evaluator_findings:
                    raise ReportError("duplicate evaluator finding")
                if item.get("disposition") not in {
                    "supported",
                    "unsupported",
                    "uncertain",
                }:
                    raise ReportError("invalid finding disposition")
                _text(item.get("reason"), "verification.reason")
                _refs(item.get("evidence_refs"), "verification.evidence_refs")
                if item.get("issue_key") is not None:
                    _text(item["issue_key"], "verification.issue_key")
                evaluator_findings[identity] = item
    if not qualified_verification:
        issues.append("independent evaluator verification missing or invalid")
        blockers.append("independent evaluator verification missing or invalid")

    stage_audits = []
    for stage, item in report_stages.items():
        refs_ok = supported_refs(
            item["evidence_refs"],
            stage,
            require=item["status"] in {"completed", "failed"},
        )
        actual = evaluator_stages.get(stage)
        confirmed = False
        if actual:
            actual_refs = supported_refs(
                actual["evidence_refs"],
                f"evaluator:{stage}",
                require=actual["status"] in {"completed", "failed"},
            )
            confirmed = bool(actual_refs and actual["status"] == item["status"])
        if item["status"] == "completed" and not (refs_ok and confirmed):
            reject(f"{stage}: unsupported completion claim")
        elif actual is not None and actual["status"] != item["status"]:
            reject(f"{stage}: reported outcome conflicts with evaluator evidence")
        elif item["status"] == "failed" and not confirmed:
            issues.append(f"{stage}: failure not independently verified")
            blockers.append(f"{stage}: failure not independently verified")
        stage_audits.append(
            {
                "id": stage,
                "reported": item["status"],
                "verified": actual["status"] if actual else "unverified",
                "confirmed": confirmed,
            }
        )

    finding_audits = []
    for item in report["friction"]:
        high_impact = item["impact"] != "minor_friction"
        refs_ok = supported_refs(
            item["evidence_refs"], f"finding:{item['id']}", blocking=high_impact
        )
        evaluator = evaluator_findings.get(item["id"])
        disposition = "uncertain"
        if evaluator:
            evaluator_refs = supported_refs(
                evaluator["evidence_refs"],
                f"evaluator: finding {item['id']}",
                blocking=high_impact,
            )
            disposition = (
                evaluator["disposition"]
                if refs_ok and evaluator_refs
                else "unsupported"
            )
        if disposition == "unsupported":
            reject(
                f"finding:{item['id']}: independent evaluator rejected claim",
                blocking=high_impact,
            )
        elif disposition == "uncertain":
            issues.append(f"finding:{item['id']}: not independently supported")
            if high_impact:
                blockers.append(
                    f"finding:{item['id']}: high-impact claim not independently supported"
                )
        finding_audits.append(
            {
                "id": item["id"],
                "impact": item["impact"],
                # Private answer-key mapping belongs to the independent evaluator.
                # The customer's original optional tag is retained only as a hint.
                "issue_key": evaluator.get("issue_key") if evaluator else None,
                "customer_issue_hint": item.get("issue_key"),
                "disposition": disposition,
            }
        )

    if report["outcome"] in {"independent_completion", "completion_with_help"}:
        if observation_scope == "first_contact" and not all(
            stage["reported"] == "completed" and stage["confirmed"]
            for stage in stage_audits
        ):
            reject(
                "overall completion does not have six independently completed stages"
            )
        if report["outcome"] == "independent_completion" and assistance == "external":
            reject(
                "independent completion conflicts with controller-recorded external assistance"
            )

    target = None
    if (
        qualified_verification
        and verification
        and verification.get("target_observation") is not None
    ):
        target = _object(verification["target_observation"], "target_observation")
        _text(target.get("issue_key"), "target_observation.issue_key")
        if (
            type(target.get("present")) is not bool
            or type(target.get("progressed")) is not bool
        ):
            raise ReportError("target_observation present/progressed must be booleans")
        refs = _refs(target.get("evidence_refs"), "target_observation.evidence_refs")
        if not supported_refs(refs, "target_observation"):
            target = None
    if (
        observation_scope == "calibration_checkpoint"
        and report["outcome"] in {"independent_completion", "completion_with_help"}
        and (target is None or not target["progressed"])
    ):
        reject("checkpoint completion lacks independently evidenced target progress")
    accomplishment = None
    if observation_scope == "calibration_checkpoint_v2":
        if (
            not qualified_verification
            or not verification
            or verification.get("checkpoint_accomplishment") is None
        ):
            reject(
                "checkpoint v2 lacks separate independent accomplishment verification"
            )
        else:
            accomplishment = _object(
                verification["checkpoint_accomplishment"], "checkpoint_accomplishment"
            )
            if accomplishment.get("claim_disposition") not in {
                "supported",
                "unsupported",
                "uncertain",
            }:
                raise ReportError(
                    "checkpoint_accomplishment.claim_disposition is invalid"
                )
            if type(accomplishment.get("final_state_reached")) is not bool:
                raise ReportError(
                    "checkpoint_accomplishment.final_state_reached must be boolean"
                )
            _text(accomplishment.get("reason"), "checkpoint_accomplishment.reason")
            accomplishment_refs = _refs(
                accomplishment.get("evidence_refs"),
                "checkpoint_accomplishment.evidence_refs",
            )
            if not supported_refs(accomplishment_refs, "checkpoint_accomplishment"):
                accomplishment = None
            elif accomplishment["claim_disposition"] != "supported":
                reject("checkpoint factual account is not independently supported")
            elif (
                report["outcome"] in {"independent_completion", "completion_with_help"}
                and not accomplishment["final_state_reached"]
            ):
                reject(
                    "checkpoint completion lacks independently observed final task state"
                )
    result = {
        "schema_version": 1,
        "session_id": report["session_id"],
        "observation_scope": observation_scope,
        "assistance": assistance,
        "events_sha256": event_digest,
        "event_count": len(events),
        "disposition": "rejected"
        if rejected
        else "uncertain"
        if issues
        else "supported",
        "rejected_claims": rejected,
        "uncertainties": issues,
        "calibration_blockers": blockers,
        "stages": stage_audits,
        "findings": finding_audits,
        "target_observation": target,
        "scope": "record integrity and separate evaluator support; no human-equivalence or engineering acceptance claim",
    }
    # Preserve the exact v1 serialized audit shape; v2 is explicitly selected.
    if observation_scope == "calibration_checkpoint_v2":
        result["checkpoint_accomplishment"] = accomplishment
    return result


def render_report(report: dict, audit: dict | None = None) -> str:
    """Render original account as Markdown; HTML is escaped, never executed."""
    validate_report(report)

    def safe(value: Any) -> str:
        escaped = html.escape(str(value), quote=False).replace("\\", "\\\\")
        for character in "[]()!*_`#":
            escaped = escaped.replace(character, "\\" + character)
        return escaped.replace("\n", "\n> ")

    lines = [
        "# Synthetic customer beta report",
        "",
        f"Session: {safe(report['session_id'])}",
        "",
        "Synthetic feedback; no inference about human satisfaction or populations.",
        "",
    ]
    for title, key in (
        ("Expected", "expectation"),
        ("Task", "task"),
        ("Accomplished", "accomplishment"),
        ("Stopping reason", "stopping_reason"),
    ):
        lines.extend([f"## {title}", "", f"> {safe(report[key])}", ""])
    lines.extend(
        [f"Reported outcome: `{safe(report['outcome'])}`", "", "## Journey stages", ""]
    )
    for stage in report["stages"]:
        lines.append(
            f"- {safe(stage['id'])}: {safe(stage['status'])}; evidence {safe(', '.join(stage['evidence_refs']) or 'none')}"
        )
    for title, key in (
        ("What worked", "positives"),
        ("Remaining uncertainty", "uncertainties"),
        ("Help and workarounds", "help"),
    ):
        lines.extend(["", f"## {title}", ""])
        for item in report[key]:
            lines.append(
                f"- {safe(item['text'])} (events: {safe(', '.join(item['evidence_refs']) or 'none')})"
            )
        if not report[key]:
            lines.append("None reported.")
    lines.extend(["", "## Friction findings", ""])
    for finding in report["friction"]:
        lines.extend(
            [
                f"### {safe(finding['id'])} — {safe(finding['stage'])}",
                "",
                f"Impact: {safe(finding['impact'])}",
                "",
            ]
        )
        for key in (
            "observation",
            "expected",
            "consequence",
            "interpretation",
            "suggestion",
        ):
            lines.extend([f"{key.title()}: {safe(finding[key])}", ""])
        lines.extend(
            [f"Evidence events: {safe(', '.join(finding['evidence_refs']))}", ""]
        )
    lines.extend(["## Prioritized improvements", ""])
    for index, priority in enumerate(report["priorities"], 1):
        lines.append(
            f"{index}. {safe(priority['recommendation'])} (finding {safe(priority['finding_id'])})"
        )
    if not report["priorities"]:
        lines.append("No supported improvement proposed by the customer.")
    if audit is not None:
        if audit.get("session_id") != report["session_id"]:
            raise ReportError("cannot attach another session's audit")
        lines.extend(
            [
                "",
                "## Separate evidence audit",
                "",
                f"Disposition: **{safe(audit['disposition'])}**",
                "",
            ]
        )
        for message in audit.get("rejected_claims", []) + audit.get(
            "uncertainties", []
        ):
            lines.append(f"- {safe(message)}")
        lines.extend(["", safe(audit.get("scope", ""))])
        if "checkpoint_accomplishment" in audit:
            lines.extend(
                [
                    "",
                    "Checkpoint accomplishment (separate from target detection/progression):",
                    "",
                    safe(
                        json.dumps(
                            audit["checkpoint_accomplishment"], ensure_ascii=False
                        )
                    ),
                ]
            )
    return "\n".join(lines) + "\n"


def compare_calibration(protocol: dict, sessions: list[dict]) -> dict:
    """Re-audit a preregistered two-by-two comparison; never trust pass flags.

    Sessions contain root/report/verification plus frozen identities. This is a
    private evaluator interface; protocol variants and answer key never belong
    in the customer context. Missing/failed sessions yield incomplete evidence.
    """
    _object(protocol, "protocol")
    protocol_id = _text(protocol.get("protocol_id"), "protocol_id")
    registered = _time(protocol.get("preregistered_at"), "preregistered_at")
    target = _text(protocol.get("target_issue"), "target_issue")
    if "observation_scope" in protocol and (
        not isinstance(protocol["observation_scope"], str)
        or protocol["observation_scope"] not in OBSERVATION_SCOPES
    ):
        raise ReportError("protocol declares an invalid observation scope")
    context = _object(protocol.get("context"), "context")
    if set(context) != CONTEXT_KEYS or any(
        not isinstance(value, str) or not value for value in context.values()
    ):
        raise ReportError("protocol context must freeze all eight comparison inputs")
    variants = {}
    for variant in _list(protocol.get("variants"), "variants"):
        identity = _text(variant.get("id"), "variant.id")
        if identity in variants or type(variant.get("has_obstacle")) is not bool:
            raise ReportError("invalid or repeated variant")
        digest = _text(variant.get("candidate_sha256"), "variant.candidate_sha256")
        if len(digest) != 64 or any(c not in "0123456789abcdef" for c in digest):
            raise ReportError("variant requires exact candidate SHA256")
        variants[identity] = variant
    if len(variants) != 2 or {item["has_obstacle"] for item in variants.values()} != {
        True,
        False,
    }:
        raise ReportError("exactly one obstacle variant and one correction required")
    if len({item["candidate_sha256"] for item in variants.values()}) != 2:
        raise ReportError("variants must have distinct frozen identities")
    reasons, records = [], []
    counts = dict.fromkeys(variants, 0)
    session_ids, reset_ids = set(), set()
    for session in _list(sessions, "sessions"):
        identity = session.get("session_id")
        reset_id = session.get("reset_id")
        if (
            not identity
            or identity in session_ids
            or not reset_id
            or reset_id in reset_ids
        ):
            reasons.append("sessions must have unique session and reset identities")
        session_ids.add(identity)
        reset_ids.add(reset_id)
        variant = variants.get(session.get("variant_id"))
        if variant is None:
            reasons.append(f"{identity}: unknown variant")
            continue
        counts[variant["id"]] += 1
        if (
            session.get("protocol_id") != protocol_id
            or session.get("context") != context
            or session.get("candidate_sha256") != variant["candidate_sha256"]
        ):
            reasons.append(f"{identity}: frozen scope/context mismatch")
        if session.get("status") != "completed":
            reasons.append(f"{identity}: missing or failed observation")
            continue
        if (
            session.get("customer_context_isolated") is not True
            or session.get("variant_blinded") is not True
        ):
            reasons.append(f"{identity}: isolation/blinding evidence not confirmed")
        if _time(session.get("started_at"), "session.started_at") <= registered:
            reasons.append(f"{identity}: session predates preregistration")
        try:
            report = session["report"]
            if report.get("session_id") != identity:
                raise ReportError("session/report identity mismatch")
            if report.get("outcome") == "lab_failure":
                reasons.append(
                    f"{identity}: lab failure is not a qualified calibration observation"
                )
                continue
            observation = load_observation_context(session["root"], identity)
            observation_scope = observation["observation_scope"]
            if (
                "observation_scope" in protocol
                and protocol["observation_scope"] != observation_scope
            ):
                raise ReportError(
                    "controller observation scope differs from preregistered protocol"
                )
            if observation["assistance"] == "external":
                reasons.append(
                    f"{identity}: external intervention prevents an unassisted calibration observation"
                )
            if session.get("observation_scope", observation_scope) != observation_scope:
                raise ReportError(
                    "comparison observation scope differs from controller manifest"
                )
            audit = audit_report(
                report,
                session["root"],
                verification=session.get("verification"),
                **observation,
            )
        except (ValueError, OSError, KeyError) as exc:
            reasons.append(f"{identity}: invalid session evidence: {exc}")
            continue
        observed = audit["target_observation"]
        passed = not audit["calibration_blockers"]
        if not observed or observed["issue_key"] != target:
            passed = False
        elif variant["has_obstacle"]:
            passed = (
                passed
                and observed["present"]
                and any(
                    finding["issue_key"] == target
                    and finding["disposition"] == "supported"
                    for finding in audit["findings"]
                )
            )
        else:
            passed = passed and not observed["present"] and observed["progressed"]
            passed = passed and not any(
                finding["issue_key"] == target for finding in audit["findings"]
            )
        records.append(
            {
                "session_id": identity,
                "variant_id": variant["id"],
                "passed": bool(passed),
                "audit": audit,
            }
        )
        if not passed:
            reasons.append(f"{identity}: target detection/progression rule not met")
    if len(sessions) != 4 or any(count != 2 for count in counts.values()):
        reasons.append(
            "comparison requires exactly two sessions per variant, four total"
        )
    complete = (
        len(records) == 4
        and len(sessions) == 4
        and all(count == 2 for count in counts.values())
    )
    return {
        "schema_version": 1,
        "protocol_id": protocol_id,
        "disposition": "pass" if not reasons else "fail" if complete else "incomplete",
        "reasons": reasons,
        "counts": counts,
        "sessions": records,
        "scope": "one calibrated obstacle; no statistical usability rate or human-equivalence claim",
    }
