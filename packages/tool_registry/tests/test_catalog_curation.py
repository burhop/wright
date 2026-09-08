from datetime import date

import httpx
import pytest
from pydantic import ValidationError

from tool_registry.catalog_curation import (
    build_report,
    discover_registry,
    github_repository,
    report_delta,
    research_github,
)
from tool_registry.catalog_models import CatalogEntry
from tool_registry.curation_models import CurationDecision, evaluate_curation


def entry(**changes):
    return CatalogEntry.model_validate(
        dict(
            id="sample",
            name="Sample",
            vendor="Publisher",
            description="Sample CAD",
            domains=["cad"],
            engineering_stages=["design"],
            transport="stdio",
            command=["sample"],
            locality="local",
            weight="light",
            source_url="https://github.com/publisher/sample",
            **changes,
        )
    )


def decision():
    return CurationDecision.model_validate(
        {
            "disposition": "curated",
            "reviewed_at": "2026-09-08",
            "review_due": "2026-10-08",
            "qualifications": [
                {
                    "platform": "linux_x64",
                    "environment": "clean Linux container",
                    "distribution_mode": "docker",
                    "configuration_sha256": "b" * 64,
                    "workflow": "Export a dimensioned cube",
                    "source_revision": "v1",
                    "wright_revision": "candidate",
                    "verified_at": "2026-09-08",
                    "expires_at": "2026-10-08",
                    "evidence_path": "evidence.json",
                    "evidence_sha256": "a" * 64,
                    "protocol": "passed",
                    "backend": "passed",
                    "gateway": "passed",
                    "outcome": "passed",
                }
            ],
        }
    )


def test_curated_requires_workflow_evidence_and_adoption_is_not_inferred():
    with pytest.raises(ValidationError, match="scoped qualification"):
        CurationDecision(disposition="curated", reviewed_at=date(2026, 9, 8))
    assert decision().adoption == "unknown"
    with pytest.raises(ValidationError, match="adoption claims"):
        CurationDecision(adoption="wright_repeat_use")


def test_expired_or_wrong_platform_recommendations_fall_back_without_mutating_decision():
    source = decision()
    assert (
        evaluate_curation(
            source, today=date(2026, 9, 9), platform="linux_x64"
        ).effective_disposition
        == "curated"
    )
    assert (
        evaluate_curation(
            source, today=date(2026, 9, 9), platform="windows_11_x64"
        ).effective_disposition
        == "follow_up"
    )
    assert (
        evaluate_curation(
            source, today=date(2026, 10, 8), platform="linux_x64"
        ).effective_disposition
        == "follow_up"
    )
    assert (
        evaluate_curation(source, today=date(2026, 9, 7)).effective_disposition
        == "follow_up"
    )
    assert source.disposition == "curated"


def test_configuration_and_deployment_changes_require_requalification():
    source = decision()
    assert (
        evaluate_curation(
            source, today=date(2026, 9, 9), distribution_mode="native"
        ).effective_disposition
        == "follow_up"
    )
    assert (
        evaluate_curation(
            source, today=date(2026, 9, 9), configuration_sha256="c" * 64
        ).effective_disposition
        == "follow_up"
    )
    assert (
        evaluate_curation(
            source,
            today=date(2026, 9, 9),
            distribution_mode="docker",
            configuration_sha256="b" * 64,
        ).effective_disposition
        == "curated"
    )


def test_environment_recognizes_the_container_boundary(monkeypatch):
    from tool_registry import compatibility

    monkeypatch.delenv("WRIGHT_DISTRIBUTION_MODE", raising=False)
    monkeypatch.setattr(compatibility.platform, "system", lambda: "Linux")
    monkeypatch.setattr(
        compatibility.Path, "is_file", lambda path: path.as_posix() == "/.dockerenv"
    )
    assert compatibility._distribution_mode() == "docker"
    monkeypatch.setattr(compatibility.platform, "system", lambda: "Windows")
    assert compatibility._distribution_mode() == "native"
    monkeypatch.setenv("WRIGHT_DISTRIBUTION_MODE", "custom")
    assert compatibility._distribution_mode() == "custom"


@pytest.mark.parametrize(
    "changes",
    [
        {"integration_kind": "protocol_reference"},
        {"hardware_standard": "mhs_preview"},
        {"risk_level": "safety-critical"},
        {"installability_tier": "non_working"},
    ],
)
def test_reference_hardware_and_broken_entries_cannot_claim_qualification(changes):
    with pytest.raises(ValidationError):
        entry(curation=decision(), **changes)


def test_report_is_repeatable_and_exposes_all_lifecycle_gaps():
    entries = [entry()]
    report = build_report(entries, as_of=date(2026, 9, 8))
    assert report == build_report(entries, as_of=date(2026, 9, 8))
    assert report_delta(report, report) == []
    assert report["counts"] == {"curated": 0, "follow_up": 1, "removed": 0}
    assert len(report["coverage"]) == 9
    assert all(not cell["curated"] for cell in report["coverage"])


def test_research_does_not_follow_redirects_or_treat_missing_source_as_abandonment():
    calls = []

    def handle(request):
        calls.append(str(request.url))
        return httpx.Response(301, headers={"Location": "http://127.0.0.1/private"})

    with httpx.Client(transport=httpx.MockTransport(handle)) as client:
        result = research_github([entry()], client)
    assert len(calls) == 1
    assert result[0]["status"] == "unavailable"
    assert result[0]["http_status"] == 301
    assert "archived" not in result[0]
    assert github_repository("https://github.com/topics/cad") is None
    assert (
        github_repository("https://github.com/publisher/sample.git")
        == "publisher/sample"
    )


def test_discovery_stays_a_follow_up_and_never_returns_execution_commands():
    def handle(request):
        assert request.url.host == "registry.modelcontextprotocol.io"
        return httpx.Response(
            200,
            json={
                "servers": [
                    {
                        "server": {
                            "name": "io.github.new/tool",
                            "version": "1",
                            "packages": [{"command": "unsafe"}],
                            "repository": {"url": "https://github.com/new/tool"},
                        }
                    }
                ],
                "metadata": {"nextCursor": "next-page"},
            },
        )

    with httpx.Client(transport=httpx.MockTransport(handle)) as client:
        result = discover_registry(client, search="manufacturing", entries=[])
    assert result["next_cursor"] == "next-page"
    assert result["candidates"][0]["proposed_disposition"] == "follow_up"
    assert "unsafe" not in str(result)


def test_shared_repository_cannot_resurrect_a_removed_implementation():
    removed = entry(curation={"disposition": "removed", "reviewed_at": "2026-09-08"})
    other = removed.model_copy(update={"id": "another", "curation": CurationDecision()})
    with httpx.Client(
        transport=httpx.MockTransport(
            lambda _: httpx.Response(
                200,
                json={
                    "servers": [
                        None,
                        {
                            "server": {
                                "name": "org/lead",
                                "version": "2",
                                "repository": {"url": removed.source_url},
                            }
                        },
                    ],
                },
            )
        )
    ) as client:
        result = discover_registry(client, search="cad", entries=[removed, other])
    assert result["candidates"][0]["related_catalog_ids"] == ["another", "sample"]
    assert result["candidates"][0]["proposed_disposition"] == "follow_up"
    assert removed.curation.disposition == "removed"


def test_failed_discovery_preserves_last_good_evidence(tmp_path, monkeypatch):
    from tool_registry import catalog_curation

    destination = tmp_path / "discover.json"
    destination.write_text('{"last_good": true}')

    def unavailable(*args, **kwargs):
        raise httpx.ConnectError("unavailable")

    monkeypatch.setattr(catalog_curation, "discover_registry", unavailable)
    assert (
        catalog_curation.main(
            ["discover", "--search", "cad", "--output-dir", str(tmp_path)]
        )
        == 2
    )
    assert destination.read_text() == '{"last_good": true}'
    assert (tmp_path / "discover.attempt.json").exists()


def test_bundled_qualifications_are_bound_to_real_passing_evidence():
    import hashlib
    import json
    from pathlib import Path
    from tool_registry.canonical_catalog import load_canonical_entries
    from tool_registry.curation_models import qualification_configuration

    root = Path(__file__).resolve().parents[3]
    for item in load_canonical_entries():
        if item.curation.disposition != "curated":
            continue
        for scope in item.curation.qualifications:
            path = (root / scope.evidence_path).resolve()
            assert path.is_relative_to(root)
            raw = path.read_bytes()
            assert b"\r\n" not in raw, (
                "Qualification evidence must retain UTF-8/LF bytes across checkouts"
            )
            assert hashlib.sha256(raw).hexdigest() == scope.evidence_sha256
            evidence = json.loads(raw)
            assert evidence["status"] == "passed" and evidence["cleanup"] == "passed"
            assert evidence["server_id"] == item.id
            assert evidence["platform"] == scope.platform
            assert (
                evidence["configuration_sha256"]
                == scope.configuration_sha256
                == qualification_configuration(item)
            )
            assert any(
                step["stage"] == "hermes_facing_gateway_mcp_backend_outcome"
                and step["status"] == "passed"
                for step in evidence["steps"]
            )
