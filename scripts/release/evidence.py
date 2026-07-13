from __future__ import annotations

from dataclasses import asdict, dataclass, field
from enum import StrEnum
import hashlib
import json
from pathlib import Path
import re
from typing import Any


SHA256_RE = re.compile(r"^[0-9a-f]{64}$")
DIGEST_RE = re.compile(r"^sha256:[0-9a-f]{64}$")
STAGES = (
    "preflight",
    "candidates_built",
    "candidates_verified",
    "test_index_verified",
    "approved",
    "promoted",
    "post_verified",
    "docs_verified",
    "release_ready",
)


class EvidenceError(ValueError):
    """Raised when release evidence is incomplete or inconsistent."""


class ReleaseMode(StrEnum):
    DRY_RUN = "dry-run"
    RELEASE = "release"


@dataclass(frozen=True, slots=True)
class ReleaseIdentity:
    version: str
    python_version: str
    tag: str
    source_commit: str

    def validate(self) -> None:
        if not re.fullmatch(r"[0-9a-f]{40}", self.source_commit):
            raise EvidenceError("source_commit must be a full lowercase Git SHA")


@dataclass(frozen=True, slots=True)
class PythonArtifact:
    filename: str
    kind: str
    sha256: str
    content_manifest_sha256: str

    def validate(self) -> None:
        if self.kind not in {"wheel", "sdist"}:
            raise EvidenceError(f"unsupported Python artifact kind: {self.kind}")
        if not SHA256_RE.fullmatch(self.sha256):
            raise EvidenceError(f"invalid SHA-256 for {self.filename}")
        if not SHA256_RE.fullmatch(self.content_manifest_sha256):
            raise EvidenceError(f"invalid content manifest SHA-256 for {self.filename}")


@dataclass(frozen=True, slots=True)
class OciCandidate:
    repository: str
    digest: str
    platforms: tuple[str, ...] = ("linux/amd64",)

    def validate(self) -> None:
        if not DIGEST_RE.fullmatch(self.digest):
            raise EvidenceError("invalid OCI digest")
        if self.platforms != ("linux/amd64",):
            raise EvidenceError("Feature 047 release candidates are linux/amd64 only")


@dataclass(slots=True)
class ReleaseEvidence:
    release_identity: ReleaseIdentity
    mode: ReleaseMode = ReleaseMode.DRY_RUN
    python_artifacts: list[PythonArtifact] = field(default_factory=list)
    python_install_evidence: list[dict[str, Any]] = field(default_factory=list)
    oci_candidate: OciCandidate | None = None
    oci_gate_evidence: dict[str, Any] | None = None
    promotions: list[dict[str, Any]] = field(default_factory=list)
    approvals: list[dict[str, Any]] = field(default_factory=list)
    verification_results: list[dict[str, Any]] = field(default_factory=list)
    skipped_optional_stages: list[str] = field(default_factory=list)
    stage_results: list[dict[str, Any]] = field(default_factory=list)
    status: str = "preflight"
    schema_version: int = 1

    def validate(self) -> None:
        self.release_identity.validate()
        if self.status not in (*STAGES, "failed", "quarantined"):
            raise EvidenceError(f"unknown release status: {self.status}")
        kinds = {artifact.kind for artifact in self.python_artifacts}
        if self.python_artifacts and kinds != {"wheel", "sdist"}:
            raise EvidenceError("release evidence requires one wheel and one sdist")
        if len(self.python_artifacts) not in {0, 2}:
            raise EvidenceError(
                "release evidence requires exactly two Python artifacts"
            )
        for artifact in self.python_artifacts:
            artifact.validate()
        if self.oci_candidate is not None:
            self.oci_candidate.validate()
            if self.oci_gate_evidence is not None:
                subject = self.oci_gate_evidence.get("candidate_digest")
                if subject != self.oci_candidate.digest:
                    raise EvidenceError(
                        "OCI gate evidence must reference the candidate digest"
                    )
            for promotion in self.promotions:
                source = promotion.get("source_digest")
                destination = promotion.get("resolved_digest")
                if source != self.oci_candidate.digest or destination != source:
                    raise EvidenceError(
                        "OCI promotion must preserve the candidate digest"
                    )
        observed: list[str] = []
        for result in self.stage_results:
            stage = str(result.get("stage", ""))
            if stage not in STAGES:
                raise EvidenceError(f"unknown stage result: {stage}")
            observed.append(stage)
        positions = [STAGES.index(stage) for stage in observed]
        if positions != sorted(set(positions)):
            raise EvidenceError("release stages must be unique and ordered")
        if self.mode is ReleaseMode.DRY_RUN:
            for result in self.stage_results:
                if result.get("external_mutation") is True:
                    raise EvidenceError(
                        "dry-run evidence cannot record external mutation"
                    )

    def to_dict(self) -> dict[str, Any]:
        self.validate()
        value = asdict(self)
        value["mode"] = self.mode.value
        if self.oci_candidate is not None:
            value["oci_candidate"]["platforms"] = list(self.oci_candidate.platforms)
        return value

    def write(self, path: Path) -> str:
        payload = json.dumps(self.to_dict(), indent=2, sort_keys=True) + "\n"
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(payload, encoding="utf-8", newline="\n")
        return hashlib.sha256(payload.encode()).hexdigest()

    @classmethod
    def read(cls, path: Path) -> ReleaseEvidence:
        raw = json.loads(path.read_text(encoding="utf-8"))
        evidence = cls(
            schema_version=int(raw["schema_version"]),
            mode=ReleaseMode(raw["mode"]),
            release_identity=ReleaseIdentity(**raw["release_identity"]),
            python_artifacts=[
                PythonArtifact(**item) for item in raw["python_artifacts"]
            ],
            python_install_evidence=list(raw.get("python_install_evidence", [])),
            oci_candidate=OciCandidate(
                repository=raw["oci_candidate"]["repository"],
                digest=raw["oci_candidate"]["digest"],
                platforms=tuple(raw["oci_candidate"]["platforms"]),
            )
            if raw.get("oci_candidate")
            else None,
            oci_gate_evidence=raw.get("oci_gate_evidence"),
            promotions=list(raw.get("promotions", [])),
            approvals=list(raw.get("approvals", [])),
            verification_results=list(raw.get("verification_results", [])),
            skipped_optional_stages=list(raw.get("skipped_optional_stages", [])),
            stage_results=list(raw.get("stage_results", [])),
            status=str(raw["status"]),
        )
        evidence.validate()
        return evidence
