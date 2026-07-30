from __future__ import annotations

import subprocess
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def _tracked_shell_scripts() -> list[Path]:
    result = subprocess.run(
        ["git", "ls-files", "-z", "*.sh"],
        cwd=ROOT,
        check=True,
        capture_output=True,
    )
    return [ROOT / item.decode() for item in result.stdout.split(b"\0") if item]


def test_tracked_shell_scripts_are_lf_normalized() -> None:
    offending = [
        path.relative_to(ROOT).as_posix()
        for path in _tracked_shell_scripts()
        if b"\r\n" in path.read_bytes()
    ]

    assert offending == [], f"tracked shell scripts contain CRLF: {offending}"


def test_gitattributes_keeps_shell_scripts_lf_normalized() -> None:
    attributes = (ROOT / ".gitattributes").read_text(encoding="utf-8")
    assert "*.sh text eol=lf" in attributes.splitlines()
