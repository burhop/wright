#!/usr/bin/env python3
"""Lightweight public-alpha leak scan for tracked repository text files."""

from __future__ import annotations

import argparse
import re
import subprocess
import sys
from dataclasses import dataclass
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]

SKIP_PARTS = {
    ".git",
    ".mypy_cache",
    ".pytest_cache",
    ".ruff_cache",
    ".venv",
    "blob-report",
    "dist",
    "dist-desktop",
    "node_modules",
    "playwright-report",
    "site",
    "test-results",
}

SKIP_SUFFIXES = {
    ".ico",
    ".jpg",
    ".jpeg",
    ".lock",
    ".pdf",
    ".png",
    ".sqlite",
    ".sqlite3",
    ".webp",
    ".zip",
}

PLACEHOLDER_HINTS = (
    "${{ secrets.",
    "<token>",
    "<your",
    "changeme",
    "ci-test",
    "dummy",
    "example",
    "fake",
    "not-needed",
    "notneeded",
    "placeholder",
    "provider-token",
    "sk-your-key",
    "test-secret",
    "wright-dev-key",
    "your-",
)

PATTERNS: tuple[tuple[str, re.Pattern[str]], ...] = (
    (
        "private-key",
        re.compile(r"-----BEGIN (?:RSA |DSA |EC |OPENSSH )?PRIVATE KEY-----"),
    ),
    ("openai-key", re.compile(r"\bsk-[A-Za-z0-9]{20,}\b")),
    ("github-token", re.compile(r"\bgh[pousr]_[A-Za-z0-9_]{30,}\b")),
    (
        "generic-secret-assignment",
        re.compile(
            r"(?i)\b(?:api[_-]?key|secret|token|password|jwt[_-]?secret|client[_-]?secret)\b"
            r"\s*[:=]\s*[\"']?([^\"'\s#]{12,})"
        ),
    ),
)


@dataclass(frozen=True)
class Finding:
    path: Path
    line_number: int
    kind: str
    snippet: str


def is_placeholder(text: str) -> bool:
    lowered = text.lower()
    return any(hint in lowered for hint in PLACEHOLDER_HINTS)


def looks_like_generic_secret(value: str) -> bool:
    cleaned = value.strip().strip("\"'`,;")
    lowered = cleaned.lower()

    if is_placeholder(cleaned):
        return False
    if len(cleaned) < 12:
        return False
    if any(char in cleaned for char in ("(", ")", "[", "]", ",", ".")):
        return False
    if lowered in {"none", "null", "true", "false"}:
        return False
    if "_" in cleaned:
        return False
    if cleaned[:1].isupper():
        return False
    return any(char.isdigit() for char in cleaned) or any(
        char in cleaned for char in ("-", "/", "+", "=")
    )


def should_scan(path: Path) -> bool:
    relative = path.relative_to(ROOT) if path.is_absolute() else path
    if any(part in SKIP_PARTS for part in relative.parts):
        return False
    if relative.suffix.lower() in SKIP_SUFFIXES:
        return False
    return True


def tracked_files(include_untracked: bool = False) -> list[Path]:
    result = subprocess.run(
        ["git", "ls-files"],
        cwd=ROOT,
        check=True,
        text=True,
        stdout=subprocess.PIPE,
    )
    paths = [ROOT / line for line in result.stdout.splitlines() if line]

    if include_untracked:
        result = subprocess.run(
            ["git", "ls-files", "--others", "--exclude-standard"],
            cwd=ROOT,
            check=True,
            text=True,
            stdout=subprocess.PIPE,
        )
        paths.extend(ROOT / line for line in result.stdout.splitlines() if line)

    return [path for path in paths if path.exists() and path.is_file() and should_scan(path)]


def read_text(path: Path) -> str | None:
    data = path.read_bytes()
    if b"\0" in data[:4096]:
        return None
    try:
        return data.decode("utf-8")
    except UnicodeDecodeError:
        return None


def scan_file(path: Path) -> list[Finding]:
    text = read_text(path)
    if text is None:
        return []

    findings: list[Finding] = []
    for line_number, line in enumerate(text.splitlines(), start=1):
        if is_placeholder(line):
            continue
        for kind, pattern in PATTERNS:
            match = pattern.search(line)
            if not match:
                continue
            if kind == "generic-secret-assignment" and not looks_like_generic_secret(
                match.group(1)
            ):
                continue
            if not is_placeholder(match.group(0)):
                findings.append(
                    Finding(
                        path=path.relative_to(ROOT),
                        line_number=line_number,
                        kind=kind,
                        snippet=line.strip()[:160],
                    )
                )
                break
    return findings


def scan_paths(paths: list[Path]) -> list[Finding]:
    findings: list[Finding] = []
    for path in paths:
        findings.extend(scan_file(path))
    return findings


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--include-untracked",
        action="store_true",
        help="Also scan untracked files that are not ignored.",
    )
    args = parser.parse_args()

    findings = scan_paths(tracked_files(include_untracked=args.include_untracked))
    if not findings:
        print("No public-alpha leak patterns found.")
        return 0

    print("Potential public-alpha leaks found:", file=sys.stderr)
    for finding in findings:
        print(
            f"{finding.path}:{finding.line_number}: {finding.kind}: {finding.snippet}",
            file=sys.stderr,
        )
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
