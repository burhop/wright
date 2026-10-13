from __future__ import annotations

from pathlib import Path
import re


ACTION_RE = re.compile(r"^\s*(?:-\s+)?uses:\s*([^#\s]+)", re.MULTILINE)
FULL_SHA_RE = re.compile(r"^[^@]+@[0-9a-f]{40}$")
JOB_RE = re.compile(r"^  ([\w-]+):", re.MULTILINE)


def job_blocks(text: str) -> list[tuple[str, str]]:
    """Read repository workflow job blocks without requiring an installed YAML tool."""
    jobs = re.search(r"^jobs:\s*$", text, re.MULTILINE)
    if jobs is None:
        return []
    body = text[jobs.end() :]
    matches = list(JOB_RE.finditer(body))
    return [
        (
            match[1],
            body[
                match.start() : matches[i + 1].start()
                if i + 1 < len(matches)
                else len(body)
            ],
        )
        for i, match in enumerate(matches)
    ]


class WorkflowPolicyError(ValueError):
    """Raised when a release workflow violates supply-chain policy."""


def validate_action_pins(path: Path) -> None:
    text = path.read_text(encoding="utf-8")
    bad = [
        value
        for value in ACTION_RE.findall(text)
        if not value.startswith("./") and not FULL_SHA_RE.fullmatch(value)
    ]
    if bad:
        raise WorkflowPolicyError(
            f"{path}: third-party actions must use full commit SHAs: {', '.join(bad)}"
        )


def validate_scoped_workflows(root: Path) -> None:
    for path in sorted((root / ".github" / "workflows").glob("*.yml")):
        validate_action_pins(path)
        validate_checkout_readiness(path)


def validate_checkout_readiness(path: Path) -> None:
    for name, block in job_blocks(path.read_text(encoding="utf-8")):
        if "    steps:" not in block:
            continue  # Reusable jobs own checkout in their called workflow.
        metadata, steps = block.split("    steps:", 1)
        checkout = re.search(r"uses:\s*actions/checkout@", steps)
        if checkout is None:
            continue
        runner = re.search(r"^    runs-on:\s*(.+)$", metadata, re.MULTILINE)
        windows = runner is not None and (
            "windows" in runner[1].lower()
            or ("${{" in runner[1] and "windows" in metadata.lower())
        )
        if windows:
            before_checkout = steps[: checkout.start()]
            expected = (
                "      - name: Enable long Git paths on Windows\n"
                "        if: runner.os == 'Windows'\n"
                "        shell: pwsh\n"
                "        run: git config --global core.longpaths true\n"
            )
            if expected not in before_checkout:
                raise WorkflowPolicyError(
                    f"{path}:{name}: enable Git long paths before Windows checkout"
                )
        # Python runtime tests include real fixed-compiler contracts. Merely
        # installing Python dependencies leaves their readiness unresolved.
        if "packages/workspace_service/tests" in steps:
            tests = re.search(r"- name: Run (?:Tests with pytest|pytest)\s*\n", steps)
            if tests is None:
                raise WorkflowPolicyError(
                    f"{path}:{name}: backend test step is not inspectable"
                )
            preparation = steps[: tests.start()]
            for required in (
                "uses: actions/setup-node@",
                "run: npm ci",
                "BuildToolchain(",
                ").describe()",
            ):
                if required not in preparation:
                    raise WorkflowPolicyError(
                        f"{path}:{name}: backend compiler readiness missing before tests: {required}"
                    )
