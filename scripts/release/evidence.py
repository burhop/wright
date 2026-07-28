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


@dataclass(frozen=True, slots=True)
class HermesCapabilityEvidence:
    version: str
    capability: str
    install_interface: str
    source: str

    def validate(self) -> None:
        if not self.version or not self.install_interface:
            raise EvidenceError("Hermes capability evidence is incomplete")
        if self.capability != "python-distribution-v1":
            raise EvidenceError("Hermes lacks the required package-plugin capability")
        if self.source not in {"fixture", "released"}:
            raise EvidenceError("Hermes capability source must be fixture or released")


@dataclass(frozen=True, slots=True)
class NativeCandidate:
    distribution: str
    plugin_version: str
    runtime_version: str
    wheel_filename: str
    wheel_sha256: str
    compatibility_sha256: str
    ui_manifest_sha256: str
    runtime_extra_lock_sha256: str

    def validate(self) -> None:
        if self.distribution != "wright-engineering":
            raise EvidenceError("native candidate must be wright-engineering")
        if self.plugin_version != self.runtime_version:
            raise EvidenceError("plugin and runtime candidate versions must match")
        for name, value in (
            ("wheel", self.wheel_sha256),
            ("compatibility", self.compatibility_sha256),
            ("UI manifest", self.ui_manifest_sha256),
            ("runtime-extra lock", self.runtime_extra_lock_sha256),
        ):
            if not SHA256_RE.fullmatch(value):
                raise EvidenceError(f"invalid {name} SHA-256")


@dataclass(slots=True)
class ReleaseEvidence:
    release_identity: ReleaseIdentity
    mode: ReleaseMode = ReleaseMode.DRY_RUN
    python_artifacts: list[PythonArtifact] = field(default_factory=list)
    python_install_evidence: list[dict[str, Any]] = field(default_factory=list)
    oci_candidate: OciCandidate | None = None
    oci_gate_evidence: dict[str, Any] | None = None
    native_candidate: NativeCandidate | None = None
    hermes_capability: HermesCapabilityEvidence | None = None
    native_platform_results: list[dict[str, Any]] = field(default_factory=list)
    stable_hermes_channel: dict[str, Any] | None = None
    native_public_verification: dict[str, Any] | None = None
    promotions: list[dict[str, Any]] = field(default_factory=list)
    approvals: list[dict[str, Any]] = field(default_factory=list)
    verification_results: list[dict[str, Any]] = field(default_factory=list)
    skipped_optional_stages: list[str] = field(default_factory=list)
    stage_results: list[dict[str, Any]] = field(default_factory=list)
    status: str = "preflight"
    schema_version: int = 2

    def validate(self) -> None:
        self.release_identity.validate()
        if self.schema_version not in {1, 2}:
            raise EvidenceError("unsupported release evidence schema version")
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
        if self.native_candidate is not None:
            self.native_candidate.validate()
        if self.hermes_capability is not None:
            self.hermes_capability.validate()
        observed_platforms: set[str] = set()
        for result in self.native_platform_results:
            platform = str(result.get("platform", ""))
            if not platform or platform in observed_platforms:
                raise EvidenceError("native platform results must be named and unique")
            observed_platforms.add(platform)
            if result.get("status") != "passed":
                raise EvidenceError(f"native platform did not pass: {platform}")
            if result.get("forbidden_executables") != []:
                raise EvidenceError(
                    f"native platform invoked a forbidden executable: {platform}"
                )
            if result.get("source_isolation") is not True:
                raise EvidenceError(
                    f"native platform lacked source isolation: {platform}"
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
        elif self.schema_version >= 2 and self.status in {
            "promoted",
            "post_verified",
            "docs_verified",
            "release_ready",
        }:
            if self.oci_candidate is None or self.oci_gate_evidence is None:
                raise EvidenceError(
                    "production evidence requires mandatory Docker evidence"
                )
            if self.native_candidate is None or self.hermes_capability is None:
                raise EvidenceError(
                    "production evidence requires native candidate evidence"
                )
            if self.hermes_capability.source != "released":
                raise EvidenceError("production evidence requires released Hermes")
            if not self.native_platform_results:
                raise EvidenceError(
                    "production evidence requires native platform results"
                )
            if self.stable_hermes_channel is None:
                raise EvidenceError(
                    "production evidence requires stable Hermes channel evidence"
                )
            if self.native_public_verification is None:
                raise EvidenceError(
                    "production evidence requires public native lifecycle evidence"
                )
            required_lifecycle = {
                "install",
                "start",
                "status",
                "doctor",
                "stop",
                "update",
                "rollback",
                "uninstall",
                "purge",
            }
            if (
                set(self.native_public_verification.get("lifecycle", []))
                != required_lifecycle
            ):
                raise EvidenceError("public native lifecycle evidence is incomplete")

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
            native_candidate=NativeCandidate(**raw["native_candidate"])
            if raw.get("native_candidate")
            else None,
            hermes_capability=HermesCapabilityEvidence(**raw["hermes_capability"])
            if raw.get("hermes_capability")
            else None,
            native_platform_results=list(raw.get("native_platform_results", [])),
            stable_hermes_channel=raw.get("stable_hermes_channel"),
            native_public_verification=raw.get("native_public_verification"),
            promotions=list(raw.get("promotions", [])),
            approvals=list(raw.get("approvals", [])),
            verification_results=list(raw.get("verification_results", [])),
            skipped_optional_stages=list(raw.get("skipped_optional_stages", [])),
            stage_results=list(raw.get("stage_results", [])),
            status=str(raw["status"]),
        )
        evidence.validate()
        return evidence
