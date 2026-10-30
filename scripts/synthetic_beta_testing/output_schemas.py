"""Structural output constraints; evidence and subject authority stay in audits."""

from __future__ import annotations

from .reports import IMPACTS, OUTCOMES, STAGES, STATUSES


def _object(properties):
    return {
        "type": "object",
        "properties": properties,
        "required": list(properties),
        "additionalProperties": False,
    }


def _text():
    return {"type": "string"}


def _exact(value):
    return {"type": "string", "enum": [value]}


def _array(items, **limits):
    return {"type": "array", "items": items, **limits}


def _stages():
    return _array(
        _object(
            {
                "id": {"type": "string", "enum": list(STAGES)},
                "status": {"type": "string", "enum": sorted(STATUSES)},
                "evidence_refs": {"$ref": "#/$defs/evidence_refs"},
            }
        ),
        minItems=len(STAGES),
        maxItems=len(STAGES),
    )


def customer_schema(session_id: str) -> dict:
    """Customer event IDs are generated during the attempt; audit checks existence."""
    if not isinstance(session_id, str) or not session_id:
        raise ValueError("customer schema requires an exact session identity")
    note = _object(
        {"text": _text(), "evidence_refs": {"$ref": "#/$defs/evidence_refs"}}
    )
    finding = _object(
        {
            "id": _text(),
            "stage": _text(),
            "impact": {"type": "string", "enum": sorted(IMPACTS)},
            **{
                key: _text()
                for key in (
                    "observation",
                    "expected",
                    "consequence",
                    "interpretation",
                    "suggestion",
                )
            },
            "evidence_refs": {"$ref": "#/$defs/evidence_refs"},
        }
    )
    schema = _object(
        {
            "schema_version": {"type": "integer", "enum": [1]},
            "session_id": _exact(session_id),
            "outcome": {"type": "string", "enum": sorted(OUTCOMES)},
            **{
                key: _text()
                for key in ("expectation", "task", "accomplishment", "stopping_reason")
            },
            "positives": _array(note),
            "uncertainties": _array(note),
            "help": _array(note),
            "stages": _stages(),
            "friction": _array(finding),
            "priorities": _array(
                _object({"finding_id": _text(), "recommendation": _text()}), maxItems=3
            ),
        }
    )
    schema["$defs"] = {
        "evidence_refs": _array({"type": "string", "pattern": "^e[0-9]{5}$"})
    }
    return schema


def evaluator_schema(
    report: dict,
    event_ids: list[str],
    evaluator_id: str,
    events_sha256: str,
    target: dict | None = None,
    *,
    observation_scope: str = "first_contact",
) -> dict:
    """Bind the response to existing subjects; no model result can grant authority."""
    if len(set(event_ids)) != len(event_ids) or any(
        not isinstance(value, str) or not value for value in event_ids
    ):
        raise ValueError("evaluator schema requires unique known event identities")
    if (
        not isinstance(evaluator_id, str)
        or not evaluator_id
        or not isinstance(events_sha256, str)
        or not events_sha256
    ):
        raise ValueError("evaluator schema requires exact evaluator/digest identities")
    issue_key = None
    if target is not None:
        if (
            not isinstance(target, dict)
            or not isinstance(target.get("issue_key"), str)
            or not target["issue_key"]
        ):
            raise ValueError("registered target requires an exact issue_key")
        issue_key = target["issue_key"]
    nullable_issue = (
        {"type": ["string", "null"], "enum": [issue_key, None]}
        if issue_key
        else {"type": "null"}
    )
    finding_ids = [item["id"] for item in report["friction"]]
    finding_id = {"type": "string", "enum": finding_ids} if finding_ids else _text()
    finding = _object(
        {
            "finding_id": finding_id,
            "disposition": {
                "type": "string",
                "enum": ["supported", "unsupported", "uncertain"],
            },
            "evidence_refs": {"$ref": "#/$defs/evidence_refs"},
            "reason": _text(),
            "issue_key": nullable_issue,
        }
    )
    target_observation = (
        _object(
            {
                "issue_key": _exact(issue_key),
                "present": {"type": "boolean"},
                "progressed": {"type": "boolean"},
                "evidence_refs": {"$ref": "#/$defs/evidence_refs"},
            }
        )
        if issue_key
        else {"type": "null"}
    )
    schema = _object(
        {
            "schema_version": {"type": "integer", "enum": [1]},
            "session_id": _exact(report["session_id"]),
            "evaluator_session_id": _exact(evaluator_id),
            "events_sha256": _exact(events_sha256),
            "stages": _stages(),
            "findings": _array(
                finding, minItems=len(finding_ids), maxItems=len(finding_ids)
            ),
            **({"target_observation": target_observation} if issue_key else {}),
        }
    )
    refs = (
        _array({"type": "string", "enum": list(event_ids)})
        if event_ids
        else _array(_text(), maxItems=0)
    )
    schema["$defs"] = {"evidence_refs": refs}
    if observation_scope == "calibration_checkpoint_v2":
        schema["properties"]["checkpoint_accomplishment"] = _object(
            {
                "claim_disposition": {
                    "type": "string",
                    "enum": ["supported", "unsupported", "uncertain"],
                },
                "final_state_reached": {"type": "boolean"},
                "evidence_refs": {"$ref": "#/$defs/evidence_refs"},
                "reason": _text(),
            }
        )
        schema["required"].append("checkpoint_accomplishment")
    return schema
