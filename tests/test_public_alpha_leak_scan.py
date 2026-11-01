import importlib.util
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SCRIPT_PATH = ROOT / "scripts" / "check-public-alpha-leaks.py"

spec = importlib.util.spec_from_file_location("check_public_alpha_leaks", SCRIPT_PATH)
assert spec is not None
leak_scan = importlib.util.module_from_spec(spec)
assert spec.loader is not None
sys.modules["check_public_alpha_leaks"] = leak_scan
spec.loader.exec_module(leak_scan)


def test_scan_file_detects_realistic_secret_patterns(tmp_path, monkeypatch) -> None:
    monkeypatch.setattr(leak_scan, "ROOT", tmp_path)
    sample = tmp_path / "sample.env"
    sample.write_text(
        "\n".join(
            [
                "OPENAI_API_KEY=" + "sk-" + "abcdefghijklmnopqrstuvwxyz123456",
                "GITHUB_TOKEN=" + "ghp_" + "abcdefghijklmnopqrstuvwxyz1234567890",
                "-----BEGIN " + "PRIVATE KEY-----",
            ]
        ),
        encoding="utf-8",
    )

    findings = leak_scan.scan_file(sample)

    assert [finding.kind for finding in findings] == [
        "openai-key",
        "github-token",
        "private-key",
    ]


def test_scan_file_ignores_documented_placeholders(tmp_path, monkeypatch) -> None:
    monkeypatch.setattr(leak_scan, "ROOT", tmp_path)
    sample = tmp_path / "example.env"
    sample.write_text(
        "\n".join(
            [
                "LLM_API_KEY=sk-your-key-here",
                "API_SERVER_KEY=wright-dev-key",
                "API_SERVER_KEY=wright-local-dev-key-000000000000000000000000",
                "password: ${{ secrets.DOCKERHUB_TOKEN }}",
                "TOKEN=provider-token",
            ]
        ),
        encoding="utf-8",
    )

    assert leak_scan.scan_file(sample) == []


def test_should_scan_skips_generated_and_binary_paths() -> None:
    assert not leak_scan.should_scan(Path("node_modules/pkg/index.js"))
    assert not leak_scan.should_scan(Path("site/index.html"))
    assert not leak_scan.should_scan(Path("docs/images/wright-logo.png"))
    assert leak_scan.should_scan(Path("docs/public-launch-checklist.md"))


def test_script_passes_current_tracked_tree() -> None:
    findings = leak_scan.scan_paths(leak_scan.tracked_files())

    assert findings == []


def test_leak_scan_is_wired_into_ci_and_release_docs() -> None:
    workflow = (ROOT / ".github" / "workflows" / "public-alpha-safety.yml").read_text(
        encoding="utf-8"
    )
    checklist = (ROOT / "docs" / "public-launch-checklist.md").read_text(
        encoding="utf-8"
    )
    testing = (ROOT / "docs" / "contributing" / "testing.md").read_text(
        encoding="utf-8"
    )

    assert "python scripts/check-public-alpha-leaks.py" in workflow
    assert "python scripts/check-public-alpha-leaks.py --include-untracked" in checklist
    assert "python scripts/check-public-alpha-leaks.py --include-untracked" in testing


def test_reviewed_canaries_have_exact_path_rule_and_whole_line_scope(
    tmp_path, monkeypatch
) -> None:
    import hashlib

    approved = leak_scan.fixture_exceptions()
    assert len(approved) == 4
    sources = {}
    for relative, rule, digest in approved:
        lines = (ROOT / relative).read_text().splitlines()
        matching = [
            line
            for line in lines
            if hashlib.sha256(line.encode()).hexdigest() == digest
        ]
        assert len(matching) == 1
        sources[(relative, rule, digest)] = matching[0]
    monkeypatch.setattr(leak_scan, "ROOT", tmp_path)
    for (relative, rule, digest), line in sources.items():
        sample = tmp_path / relative
        sample.parent.mkdir(parents=True, exist_ok=True)
        sample.write_text(line + "\n")
        assert leak_scan.scan_file(sample, exceptions=approved) == []
        assert leak_scan.scan_file(sample, exceptions=set())
        sample.write_text(line + " additional-content\n")
        assert leak_scan.scan_file(sample, exceptions=approved)
        sample.write_text(
            line.replace("abc123", "abc124")
            .replace("OPENSSH", "RSA")
            .replace("7890", "7891")
            + "\n"
        )
        assert leak_scan.scan_file(sample, exceptions=approved)
        sample.write_text(line + "\n" + "token=" + "x12345678901234567890" + "\n")
        assert any(
            finding.line_number == 2
            for finding in leak_scan.scan_file(sample, exceptions=approved)
        )
        other = tmp_path / "unapproved.py"
        other.write_text(line)
        assert leak_scan.scan_file(other, exceptions=approved)
        sample.write_text(line)
        wrong_rule = {(relative, "github-token", digest)}
        assert leak_scan.scan_file(sample, exceptions=wrong_rule)


def test_malformed_exception_policy_fails_closed(tmp_path, monkeypatch) -> None:
    import json
    import pytest

    monkeypatch.setattr(leak_scan, "ROOT", tmp_path)
    policy = tmp_path / ".github/public-alpha-fixture-exceptions.json"
    policy.parent.mkdir()
    for value in (
        {"schema_version": 2, "exceptions": []},
        {"schema_version": 1, "exceptions": [{"path": "../outside"}]},
        {"schema_version": 1, "exceptions": "all"},
    ):
        policy.write_text(json.dumps(value))
        with pytest.raises(ValueError):
            leak_scan.fixture_exceptions()
