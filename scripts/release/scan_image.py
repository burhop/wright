"""Scan one existing image with the same current-DB policy locally and in PR CI.

This never builds or publishes an image. Raw scanner output stays local; only the
allowlisted public projection is suitable for a CI artifact.
"""

from __future__ import annotations

import argparse
from datetime import UTC, datetime
import hashlib
import json
import os
from pathlib import Path
import re
import subprocess
from typing import Any
from uuid import uuid4

from scripts.release.vulnerability_policy import evaluate_report


SCANNER = (
    "docker.io/aquasec/trivy@sha256:"
    "be1190afcb28352bfddc4ddeb71470835d16462af68d310f9f4bca710961a41e"
)
SCANNER_VERSION = "0.70.0"
# Conservative superset of the standard Dockerfile's COPY/build inputs. Metadata
# descendants can reuse a tested image only when none of these paths changed.
BUILD_INPUTS = (
    ".dockerignore",
    "docker",
    "apps",
    "packages",
    "src",
    "hermes-plugin-wright",
    "integrations/rivet/editor",
    "integrations/rivet/runner",
    "pyproject.toml",
    "uv.lock",
    "package.json",
    "package-lock.json",
    "README.md",
)
SHA256 = re.compile(r"sha256:[0-9a-f]{64}\Z")
COMMIT = re.compile(r"[0-9a-f]{40}\Z")
SEVERITIES = {"UNKNOWN", "LOW", "MEDIUM", "HIGH", "CRITICAL"}


class ImageScanError(ValueError):
    """A scan or its exact-image binding cannot be trusted."""


class LocalDockerUnavailable(ImageScanError):
    """The local Docker daemon cannot perform this host's scan."""


def _sha(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def _write(path: Path, value: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, indent=2) + "\n", encoding="utf-8")


class Commands:
    def __init__(self, root: Path, output: Path):
        self.root, self.output = root, output

    def run(self, label: str, args: list[str], *, timeout: int = 600) -> str:
        try:
            result = subprocess.run(
                args,
                cwd=self.root,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                timeout=timeout,
                check=False,
            )
        except (OSError, subprocess.TimeoutExpired) as exc:
            # Exception strings may contain private command/environment context.
            raise ImageScanError(
                f"{label} could not run ({type(exc).__name__})"
            ) from exc
        (self.output / f"{label}.log").write_bytes(result.stdout)
        if result.returncode:
            raise ImageScanError(
                f"{label} failed with exit {result.returncode}; raw log retained"
            )
        return result.stdout.decode("utf-8")


def local_docker(commands: Commands) -> tuple[list[str], str]:
    for name in ("DOCKER_HOST", "DOCKER_TLS", "DOCKER_TLS_VERIFY", "DOCKER_CERT_PATH"):
        if os.environ.get(name):
            raise ImageScanError(f"Conflicting Docker target override: {name}")
    context = os.environ.get("DOCKER_CONTEXT")
    if not context:
        try:
            context = commands.run(
                "docker-context", ["docker", "context", "show"], timeout=10
            ).strip()
        except ImageScanError as exc:
            if isinstance(exc.__cause__, FileNotFoundError):
                raise LocalDockerUnavailable("Docker CLI is not installed") from exc
            raise
    if not re.fullmatch(r"[A-Za-z0-9_.-]+", context):
        raise ImageScanError("Invalid Docker context")
    docker = ["docker", "--context", context]
    records = json.loads(
        commands.run(
            "docker-endpoint", docker + ["context", "inspect", context], timeout=10
        )
    )
    if not isinstance(records, list) or len(records) != 1:
        raise ImageScanError("Ambiguous Docker context")
    endpoint = records[0]["Endpoints"]["docker"]["Host"]
    if re.fullmatch(r"npipe:////\./pipe/[A-Za-z0-9_.-]+", endpoint):
        socket = "/var/run/docker.sock"
    elif re.fullmatch(r"unix:///(?:var/run|run/user/[0-9]+)/docker\.sock", endpoint):
        socket = endpoint.removeprefix("unix://")
    else:
        raise ImageScanError(
            "Image scanning requires a local Docker socket; remote targets are rejected"
        )
    try:
        platform = commands.run(
            "docker-platform",
            docker + ["info", "--format", "{{.OSType}}/{{.Architecture}}"],
            timeout=10,
        ).strip()
    except ImageScanError as exc:
        raise LocalDockerUnavailable(
            "No responsive local Docker daemon within 10 seconds"
        ) from exc
    if platform not in {"linux/amd64", "linux/x86_64", "linux/arm64", "linux/aarch64"}:
        raise LocalDockerUnavailable(
            "This host does not expose a supported local Linux Docker daemon"
        )
    return docker, socket


def bind_source(
    commands: Commands, record: dict[str, Any], source: str
) -> dict[str, str]:
    image_id = record.get("Id", "")
    revision = (record.get("Config", {}).get("Labels") or {}).get(
        "org.opencontainers.image.revision", ""
    )
    if not SHA256.fullmatch(image_id) or not COMMIT.fullmatch(revision):
        raise ImageScanError(
            "Image must have an immutable ID and an exact OCI source revision"
        )
    if record.get("Os") != "linux" or record.get("Architecture") not in {
        "amd64",
        "arm64",
    }:
        raise ImageScanError("Unexpected candidate image platform")
    head = commands.run(
        "source-commit",
        ["git", "rev-parse", "--verify", f"{source}^{{commit}}"],
        timeout=10,
    ).strip()
    tree = commands.run(
        "source-tree", ["git", "rev-parse", f"{head}^{{tree}}"], timeout=10
    ).strip()
    commands.run(
        "image-source-ancestor",
        ["git", "merge-base", "--is-ancestor", revision, head],
        timeout=10,
    )
    # A named source must represent this checkout; include staged/unstaged and
    # untracked build inputs so an image from before a dependency edit is refused.
    checkout = commands.run(
        "checkout-commit", ["git", "rev-parse", "HEAD"], timeout=10
    ).strip()
    if checkout != head:
        raise ImageScanError("Requested scan source is not the current checkout")
    # Check each boundary separately. An unstaged revert must not cancel a
    # committed or staged change while we attribute the image to this HEAD.
    for label, revisions in (
        ("image-inputs", [revision, head]),
        ("staged-image-inputs", ["--cached", head]),
        ("unstaged-image-inputs", []),
    ):
        commands.run(
            label,
            ["git", "diff", "--quiet", *revisions, "--", *BUILD_INPUTS],
            timeout=10,
        )
    extra = commands.run(
        "untracked-image-inputs",
        ["git", "ls-files", "--others", "--exclude-standard", "--", *BUILD_INPUTS],
        timeout=10,
    )
    if extra.strip():
        raise ImageScanError(
            "Untracked Docker build inputs prevent image/source binding"
        )
    return {
        "image_id": image_id,
        "image_source_commit": revision,
        "source_commit": head,
        "source_tree": tree,
    }


def validate_report(report: dict[str, Any], image_id: str) -> None:
    if (
        report.get("SchemaVersion") != 2
        or report.get("ArtifactType") != "container_image"
        or report.get("ArtifactName") != image_id
        or report.get("Metadata", {}).get("ImageID") != image_id
    ):
        raise ImageScanError("Scanner report is not bound to the exact candidate image")
    results = report.get("Results")
    if not isinstance(results, list) or not results:
        raise ImageScanError("Scanner report has no package scan results")
    if any(not isinstance(item, dict) for item in results):
        raise ImageScanError("Malformed package scan results")
    types = {item.get("Type") for item in results}
    if not {"python-pkg", "node-pkg"} <= types or not any(
        item.get("Class") == "os-pkgs" for item in results
    ):
        raise ImageScanError(
            "Scanner report is missing Wright Python, Node or OS package coverage"
        )
    for section in results:
        if "Vulnerabilities" not in section:
            continue
        findings = section["Vulnerabilities"]
        if not isinstance(findings, list):
            raise ImageScanError("Malformed vulnerability collection")
        for finding in findings:
            if not isinstance(finding, dict) or any(
                not isinstance(finding.get(key), str) or not finding[key].strip()
                for key in ("VulnerabilityID", "PkgName", "InstalledVersion")
            ):
                raise ImageScanError("Malformed vulnerability identity or version")
            severity = finding.get("Severity")
            if not isinstance(severity, str) or severity not in SEVERITIES:
                raise ImageScanError("Malformed vulnerability severity")
            if "FixedVersion" in finding and not isinstance(
                finding["FixedVersion"], str
            ):
                raise ImageScanError("Malformed vulnerability fixed version")


def public_findings(report: dict[str, Any]) -> list[dict[str, str | None]]:
    return [
        {
            key: finding.get(key)
            for key in (
                "VulnerabilityID",
                "PkgName",
                "InstalledVersion",
                "FixedVersion",
                "Severity",
            )
        }
        for section in report.get("Results") or []
        for finding in section.get("Vulnerabilities") or []
    ]


def scan(
    root: Path,
    output: Path,
    image: str,
    *,
    source: str = "HEAD",
    allow_unavailable: bool = False,
    commands: Commands | None = None,
) -> int:
    output.mkdir(parents=True, exist_ok=False)
    commands = commands or Commands(root, output)
    observation: dict[str, Any] = {
        "status": "failed",
        "started_at": datetime.now(UTC).isoformat(),
        "scanner_image": SCANNER,
        "scanner_version": SCANNER_VERSION,
        "builds": 0,
        "publications": 0,
        "findings": [],
    }
    result = 1
    try:
        docker, socket = local_docker(commands)
        if not image:
            raise ImageScanError(
                "Set WRIGHT_GATE_DOCKER_IMAGE to the existing candidate image; build it once before the gate"
            )
        records = json.loads(
            commands.run(
                "candidate-image",
                docker + ["image", "inspect", "--", image],
                timeout=30,
            )
        )
        if not isinstance(records, list) or len(records) != 1:
            raise ImageScanError("Expected exactly one existing candidate image")
        binding = bind_source(commands, records[0], source)
        observation.update(binding)
        policy = root / "docker/release-policy.json"
        observation["policy_sha256"] = _sha(policy.read_bytes())
        policy_data = json.loads(policy.read_bytes())
        severities = policy_data["blocked_severities"]
        if (
            not isinstance(severities, list)
            or not severities
            or not set(severities) <= SEVERITIES
        ):
            raise ImageScanError("Invalid blocked-severity policy")
        # A fresh per-observation cache requires a current database download; an
        # unavailable database is an error, never a host-unavailability skip.
        cache = output / "cache"
        cache.mkdir()
        version = commands.run(
            "scanner-version",
            docker
            + [
                "run",
                "--rm",
                "--pull",
                "missing",
                "--network",
                "none",
                SCANNER,
                "--version",
            ],
        )
        if f"Version: {SCANNER_VERSION}" not in version.splitlines():
            raise ImageScanError("Scanner version differs from the pinned CI version")
        flags = [
            "--format",
            "json",
            "--output",
            "/evidence/trivy-private.json",
            "--exit-code",
            "0",
            "--vuln-type",
            "os,library",
            "--severity",
            ",".join(severities),
            "--skip-version-check",
        ]
        if policy_data.get("ignore_unfixed", True):
            flags.append("--ignore-unfixed")
        commands.run(
            "trivy",
            docker
            + [
                "run",
                "--rm",
                "--pull",
                "never",
                "--mount",
                f"type=bind,source={socket},target=/var/run/docker.sock,readonly",
                "--mount",
                f"type=bind,source={cache.as_posix()},target=/cache",
                "--mount",
                f"type=bind,source={output.as_posix()},target=/evidence",
                SCANNER,
                "image",
                "--image-src",
                "docker",
                "--cache-dir",
                "/cache",
                *flags,
                binding["image_id"],
            ],
        )
        report_path = output / "trivy-private.json"
        report = json.loads(report_path.read_bytes())
        observation["raw_report_sha256"] = _sha(report_path.read_bytes())
        validate_report(report, binding["image_id"])
        database = json.loads((cache / "db/metadata.json").read_bytes())
        now = datetime.now(UTC)
        updated = datetime.fromisoformat(database["UpdatedAt"].replace("Z", "+00:00"))
        next_update = datetime.fromisoformat(
            database["NextUpdate"].replace("Z", "+00:00")
        )
        if database.get("Version") != 2 or not updated <= now < next_update:
            raise ImageScanError(
                "Vulnerability database is missing or outside its validity window"
            )
        observation["database"] = {
            key: database.get(key)
            for key in ("Version", "UpdatedAt", "NextUpdate", "DownloadedAt")
        }
        observation["findings"] = public_findings(report)
        evaluate_report(report_path, policy)
        observation["status"] = "passed"
        result = 0
    except LocalDockerUnavailable as exc:
        observation["message"] = str(exc)
        if allow_unavailable:
            observation["status"] = "host-unavailable"
            print(
                f"Image scan HOST LIMITATION: {exc}. Record this limitation; OCI CI remains required."
            )
            result = 0
        else:
            print(f"Image scan failed: {exc}")
    except (ImageScanError, ValueError, KeyError, TypeError, OSError) as exc:
        message = (
            str(exc)
            if isinstance(exc, (ImageScanError, ValueError))
            and not isinstance(exc, json.JSONDecodeError)
            else type(exc).__name__
        )
        observation["message"] = message
        print(f"Image scan failed: {message}")
    finally:
        observation["completed_at"] = datetime.now(UTC).isoformat()
        # Never copy ImageConfig/env/history, Secret matches, paths, or raw command
        # output into the public artifact. Retain original bytes locally by hash.
        _write(output / "public/scan.json", observation)
        _write(
            output / "public/raw-hashes.json",
            [
                {
                    "filename": path.name,
                    "bytes": path.stat().st_size,
                    "sha256": _sha(path.read_bytes()),
                }
                for path in sorted(output.iterdir())
                if path.is_file()
            ],
        )
    print(f"Image scan {observation['status']}; public evidence: {output / 'public'}")
    return result


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--image", default=os.environ.get("WRIGHT_GATE_DOCKER_IMAGE", "")
    )
    parser.add_argument("--source", default="HEAD")
    parser.add_argument("--output", type=Path)
    parser.add_argument("--allow-unavailable-local-host", action="store_true")
    args = parser.parse_args()
    root = Path(__file__).resolve().parents[2]
    output = args.output or root / "test-results/docker-image-security" / (
        datetime.now(UTC).strftime("%Y%m%dT%H%M%SZ") + "-" + uuid4().hex[:8]
    )
    return scan(
        root,
        output.resolve(),
        args.image,
        source=args.source,
        allow_unavailable=args.allow_unavailable_local_host,
    )


if __name__ == "__main__":
    raise SystemExit(main())
