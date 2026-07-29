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
class ManagerAdapterEvidence:
    manager_id: str
    manager_version: str
    adapter_protocol: str
    install_interface: str
    immutable_identity: str
    source: str

    def validate(self) -> None:
        if not all(
            (
                self.manager_id,
                self.manager_version,
                self.adapter_protocol,
                self.install_interface,
                self.immutable_identity,
            )
        ):
            raise EvidenceError("manager adapter evidence is incomplete")
        expected = {
            "hermes": ("hermes-git-plugin-v1", "git"),
            "codex": ("mcp-v1", "mcp-config"),
        }
        if self.manager_id not in expected:
            raise EvidenceError(f"unsupported manager adapter: {self.manager_id}")
        if (self.adapter_protocol, self.install_interface) != expected[self.manager_id]:
            raise EvidenceError(f"manager adapter protocol mismatch: {self.manager_id}")
        if self.source not in {"fixture", "released"}:
            raise EvidenceError("manager adapter source must be fixture or released")


@dataclass(frozen=True, slots=True)
class NativeCandidate:
    distribution: str
    runtime_version: str
    wheel_filename: str
    wheel_sha256: str
    compatibility_sha256: str
    ui_manifest_sha256: str
    runtime_extra_lock_sha256: str

    def validate(self) -> None:
        if self.distribution != "wright-engineering":
            raise EvidenceError("native candidate must be wright-engineering")
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
    manager_adapters: list[ManagerAdapterEvidence] = field(default_factory=list)
    native_platform_results: list[dict[str, Any]] = field(default_factory=list)
    manager_adapter_channels: list[dict[str, Any]] = field(default_factory=list)
    native_public_verification: dict[str, Any] | None = None
    promotions: list[dict[str, Any]] = field(default_factory=list)
    approvals: list[dict[str, Any]] = field(default_factory=list)
    verification_results: list[dict[str, Any]] = field(default_factory=list)
    skipped_optional_stages: list[str] = field(default_factory=list)
    stage_results: list[dict[str, Any]] = field(default_factory=list)
    status: str = "preflight"
    schema_version: int = 3

    def validate(self) -> None:
        self.release_identity.validate()
        if self.schema_version != 3:
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
        observed_managers: set[str] = set()
        for adapter in self.manager_adapters:
            adapter.validate()
            if adapter.manager_id in observed_managers:
                raise EvidenceError("manager adapter identities must be unique")
            observed_managers.add(adapter.manager_id)
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
        elif self.status in {
            "promoted",
            "post_verified",
            "docs_verified",
            "release_ready",
        }:
            if self.oci_candidate is None or self.oci_gate_evidence is None:
                raise EvidenceError(
                    "production evidence requires mandatory Docker evidence"
                )
            if self.native_candidate is None or not self.manager_adapters:
                raise EvidenceError(
                    "production evidence requires native candidate evidence"
                )
            required_managers = {"hermes", "codex"}
            if observed_managers != required_managers:
                raise EvidenceError(
                    "production evidence requires Hermes and Codex adapters"
                )
            if any(adapter.source != "released" for adapter in self.manager_adapters):
                raise EvidenceError(
                    "production evidence requires released manager adapters"
                )
            if not self.native_platform_results:
                raise EvidenceError(
                    "production evidence requires native platform results"
                )
            channel_managers = {
                str(channel.get("manager_id"))
                for channel in self.manager_adapter_channels
            }
            if channel_managers != required_managers:
                raise EvidenceError(
                    "production evidence requires manager adapter channel evidence"
                )
            if self.native_public_verification is None:
                raise EvidenceError(
                    "production evidence requires public native lifecycle evidence"
                )
            base_lifecycle = {
                "install",
                "start",
                "status",
                "doctor",
                "stop",
                "uninstall",
                "purge",
            }
            observed_lifecycle = set(
                self.native_public_verification.get("lifecycle", [])
            )
            release_mode = self.native_public_verification.get("release_mode")
            required_lifecycle = set(base_lifecycle)
            if release_mode == "upgrade":
                required_lifecycle.update({"update", "rollback"})
            elif release_mode != "initial_native_release":
                raise EvidenceError("public native release mode is missing")
            if observed_lifecycle != required_lifecycle:
                raise EvidenceError("public native lifecycle evidence is incomplete")
            if (
                release_mode == "initial_native_release"
                and self.native_public_verification.get("previous_stable") is not None
            ):
                raise EvidenceError(
                    "initial native release cannot claim a public predecessor"
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
            native_candidate=NativeCandidate(**raw["native_candidate"])
            if raw.get("native_candidate")
            else None,
            manager_adapters=[
                ManagerAdapterEvidence(**item)
                for item in raw.get("manager_adapters", [])
            ],
            native_platform_results=list(raw.get("native_platform_results", [])),
            manager_adapter_channels=list(raw.get("manager_adapter_channels", [])),
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
