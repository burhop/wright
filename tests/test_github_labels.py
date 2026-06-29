import ast
import re
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
REQUIRED_LABELS = {
    "bug",
    "needs-triage",
    "alpha",
    "docker",
    "docs",
    "mcp",
    "ui",
    "hermes",
    "good-first-issue",
}


def read_text(relative_path: str) -> str:
    return (ROOT / relative_path).read_text(encoding="utf-8")


def manifest_labels() -> set[str]:
    manifest = read_text(".github/labels.yml")
    return set(re.findall(r"^- name: (.+)$", manifest, flags=re.MULTILINE))


def template_labels(relative_path: str) -> set[str]:
    text = read_text(relative_path)
    match = re.search(r'^labels:\s*(\[.+\])$', text, flags=re.MULTILINE)
    assert match is not None, f"{relative_path} must declare template labels"
    parsed = ast.literal_eval(match.group(1))
    return set(parsed)


def test_required_public_alpha_labels_are_declared() -> None:
    labels = manifest_labels()

    assert REQUIRED_LABELS <= labels


def test_issue_template_labels_exist_in_manifest() -> None:
    labels = manifest_labels()

    assert template_labels(".github/ISSUE_TEMPLATE/bug_report.yml") <= labels
    assert template_labels(".github/ISSUE_TEMPLATE/feature_request.yml") <= labels


def test_public_launch_checklist_points_to_label_manifest() -> None:
    checklist = read_text("docs/public-launch-checklist.md")

    assert ".github/labels.yml" in checklist
    for label in REQUIRED_LABELS:
        assert f"`{label}`" in checklist


def test_label_manifest_has_descriptions_and_colors() -> None:
    manifest = read_text(".github/labels.yml")
    chunks = [chunk for chunk in manifest.split("\n\n") if chunk.strip()]

    assert len(chunks) >= len(REQUIRED_LABELS)
    for chunk in chunks:
        assert re.search(r"^- name: .+", chunk, flags=re.MULTILINE)
        assert re.search(r"^  color: [0-9a-fA-F]{6}$", chunk, flags=re.MULTILINE)
        assert re.search(r"^  description: .+", chunk, flags=re.MULTILINE)
