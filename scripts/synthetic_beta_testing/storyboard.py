"""Deterministic presentation of an existing customer report and audited evidence."""

from __future__ import annotations

import hashlib
import html
import json
from pathlib import Path

from .reports import ReportError, audit_report, load_observation_context, load_report

PNG_SIGNATURE = b"\x89PNG\r\n\x1a\n"


def export_storyboard(session_root: str | Path, output_dir: str | Path) -> dict:
    """Export five HTML frames without altering customer feedback or judgments.

    Requires the saved independent audit to match a fresh integrity check. Only
    session-recorded, hash-validated PNG captures can become presentation assets.
    This creates a presentation, never another manually maintained status owner.
    """
    root = Path(session_root).resolve(strict=True)
    output = Path(output_dir).absolute()
    if output.resolve() != output:
        raise ReportError("storyboard output cannot contain symlinks")
    if output.exists():
        raise ReportError("storyboard output must be fresh; preserve earlier exports")
    sources = {}
    for name in ("report.json", "events.jsonl", "verification.json", "audit.json"):
        path = root / name
        if path.is_symlink() or not path.is_file():
            raise ReportError(f"storyboard requires original session file: {name}")
        sources[name] = hashlib.sha256(path.read_bytes()).hexdigest()
    report = load_report(root / "report.json")
    observation = load_observation_context(root, report["session_id"])
    controller_manifest = root / "customer-session.json"
    if controller_manifest.exists():
        sources["customer-session.json"] = hashlib.sha256(
            controller_manifest.read_bytes()
        ).hexdigest()
    verification = json.loads((root / "verification.json").read_text())
    audited = audit_report(report, root, verification=verification, **observation)
    saved_audit = json.loads((root / "audit.json").read_text())
    if saved_audit != audited:
        raise ReportError(
            "saved audit is stale or differs from current session evidence"
        )
    events = [
        json.loads(line)
        for line in (root / "events.jsonl").read_text().splitlines()
        if line.strip()
    ]
    by_id = {event["id"]: event for event in events}
    selected = {}

    def escape(value):
        return html.escape(str(value), quote=True)

    def paragraphs(items):
        return (
            "".join(f"<p>{escape(item['text'])}</p>" for item in items)
            or "<p>None reported.</p>"
        )

    def capture_for(refs):
        for identity in refs:
            event = by_id.get(identity)
            if not event:
                continue
            for capture in event["captures"]:
                name = capture["path"]
                path = root / name
                data = path.read_bytes()
                # audit_report already checked every path and hash. Recheck the
                # selected bytes before copying so selection cannot bypass it.
                if (
                    not path.resolve().is_relative_to(root)
                    or path.is_symlink()
                    or hashlib.sha256(data).hexdigest() != capture["sha256"]
                ):
                    raise ReportError("selected storyboard capture identity changed")
                if not data.startswith(PNG_SIGNATURE):
                    continue
                if name not in selected:
                    if len(selected) >= 6:
                        return ""
                    selected[name] = {
                        "path": f"assets/capture-{len(selected) + 1}.png",
                        "sha256": capture["sha256"],
                        "bytes": data,
                    }
                target = selected[name]["path"]
                return f'<figure><img src="{escape(target)}" alt="Retained screen for event {escape(identity)}"><figcaption>Event {escape(identity)} · {escape(event["time"])} · source {escape(name)}</figcaption></figure>'
        return "<p class=uncertain>No retained PNG selected for this frame.</p>"

    def frame(number, title, body, refs=()):
        return f'<section class="frame" id="frame-{number}"><header><span>Wright synthetic beta · {escape(report["session_id"])}</span><span>{number}/5</span></header><h1>{escape(title)}</h1><div class="content"><div>{body}</div><div>{capture_for(refs)}</div></div><footer>Synthetic customer account and separate evidence audit. No human-population or engineering-acceptance claim.</footer></section>'

    first_refs = [event["id"] for event in events]
    progress_refs = [
        ref
        for stage in report["stages"]
        if stage["status"] == "completed"
        for ref in stage["evidence_refs"]
    ] or list(reversed(first_refs))
    friction_refs = [
        ref for finding in report["friction"] for ref in finding["evidence_refs"]
    ]
    stages = (
        "<ul>"
        + "".join(
            f"<li>{escape(stage['id'])}: reported {escape(stage['reported'])}; independently {escape(stage['verified'])}</li>"
            for stage in audited["stages"]
        )
        + "</ul>"
    )
    friction = ""
    for finding in report["friction"][:3]:
        friction += f"<article><h2>{escape(finding['id'])} · {escape(finding['stage'])} · {escape(finding['impact'])}</h2>"
        for key in (
            "observation",
            "expected",
            "consequence",
            "interpretation",
            "suggestion",
        ):
            friction += (
                f"<p><strong>{escape(key.title())}:</strong> {escape(finding[key])}</p>"
            )
        friction += (
            f"<p>Evidence: {escape(', '.join(finding['evidence_refs']))}</p></article>"
        )
    if len(report["friction"]) > 3:
        friction += "<p>Showing the first three findings; the original report retains all findings.</p>"
    priorities = (
        "<ol>"
        + "".join(
            f"<li>{escape(item['recommendation'])} (customer finding {escape(item['finding_id'])})</li>"
            for item in report["priorities"]
        )
        + "</ol>"
    )
    limits = "".join(
        f"<li>{escape(message)}</li>"
        for message in audited["rejected_claims"] + audited["uncertainties"]
    )
    accomplishment_summary = ""
    if "checkpoint_accomplishment" in audited:
        accomplishment = audited["checkpoint_accomplishment"]
        accomplishment_summary = (
            "<h2>Separate checkpoint accomplishment</h2><p>"
            + escape(json.dumps(accomplishment, ensure_ascii=False))
            + "</p>"
        )
    frames = [
        frame(
            1,
            "What the customer expected",
            f"<h2>Expectation</h2><p>{escape(report['expectation'])}</p><h2>Task</h2><p>{escape(report['task'])}</p>",
            first_refs,
        ),
        frame(
            2,
            "Recorded progress and stopping point",
            f"<p><strong>Customer-reported outcome:</strong> {escape(report['outcome'])}</p><p>{escape(report['accomplishment'])}</p><h2>Stopping reason</h2><p>{escape(report['stopping_reason'])}</p>{stages}{accomplishment_summary}",
            progress_refs,
        ),
        frame(
            3,
            "Consequential friction",
            friction or "<p>No friction findings reported.</p>",
            friction_refs,
        ),
        frame(
            4,
            "Customer priorities and help",
            (
                priorities
                if report["priorities"]
                else "<p>No supported priority proposed by the customer.</p>"
            )
            + "<h2>Help and workarounds</h2>"
            + paragraphs(report["help"])
            + "<h2>What worked</h2>"
            + paragraphs(report["positives"]),
            friction_refs,
        ),
        frame(
            5,
            "Uncertainty and evidence limits",
            f"<p><strong>Separate audit:</strong> {escape(audited['disposition'])}</p><ul>{limits}</ul><h2>Customer uncertainty</h2>{paragraphs(report['uncertainties'])}<p>{escape(audited['scope'])}</p>",
            list(reversed(first_refs)),
        ),
    ]
    document = (
        '<!doctype html><html lang="en"><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>Wright synthetic beta storyboard</title><style>body{margin:0;background:#e8edf2;color:#142232;font:17px system-ui,sans-serif}.frame{box-sizing:border-box;max-width:1440px;min-height:810px;margin:24px auto;padding:36px;background:white;break-after:page}header,footer{display:flex;justify-content:space-between;color:#526477;font-size:13px}h1{font-size:32px}h2{font-size:19px}.content{display:grid;grid-template-columns:minmax(0,1fr) minmax(0,1.2fr);gap:32px}p,li{line-height:1.45;overflow-wrap:anywhere}figure{margin:0}img{max-width:100%;height:auto;border:1px solid #c8d3df}figcaption{font-size:12px;color:#526477;overflow-wrap:anywhere}footer{margin-top:30px}article{border-top:1px solid #d8e0e8}.uncertain{color:#745321}@media(max-width:850px){.content{grid-template-columns:1fr}.frame{margin:0;padding:24px}}@media print{body{background:white}.frame{margin:0;max-width:none}}</style><body>'
        + "".join(frames)
        + "</body></html>"
    )
    # Verify source bytes did not change while the presentation was assembled.
    if any(
        hashlib.sha256((root / name).read_bytes()).hexdigest() != digest
        for name, digest in sources.items()
    ):
        raise ReportError("session source changed during storyboard generation")
    output.mkdir(parents=True)
    (output / "assets").mkdir()
    asset_rows = []
    for source, item in selected.items():
        (output / item["path"]).write_bytes(item["bytes"])
        asset_rows.append(
            {"source": source, "path": item["path"], "sha256": item["sha256"]}
        )
    (output / "storyboard.html").write_text(document, encoding="utf-8")
    manifest = {
        "schema_version": 1,
        "session_id": report["session_id"],
        "frames": 5,
        "source_sha256": sources,
        "captures": asset_rows,
        "html_sha256": hashlib.sha256(document.encode()).hexdigest(),
        "scope": "derived presentation of original report and independent audit; no new customer observation",
    }
    (output / "manifest.json").write_text(json.dumps(manifest, indent=2) + "\n")
    return manifest
