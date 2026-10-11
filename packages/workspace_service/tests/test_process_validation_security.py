"""Adversarial lifecycle checks for the process-validation service boundary."""

from __future__ import annotations

from concurrent.futures import ThreadPoolExecutor
from threading import Event, Lock
import hashlib
import json

import pytest

from core.process_validation import (
    ProducerIdentity,
    ResourceBudget,
    SubjectBinding,
    ValidationProfile,
    ValidationRequest,
    canonical_digest,
)
from data_vault.process_validation_repository import ProcessValidationRepository
from workspace_service.process_validation.profiles import load_profile
from workspace_service.process_validation.readers.base import ReaderRegistry
from workspace_service.process_validation.readers.structured import StructuredReader
from workspace_service.process_validation.service import ProcessValidationService
from workspace_service.process_validation.subjects import SubjectResolver


def _value_request(profile, *, key="security", trace_id="trace-security"):
    value = {"length_mm": 100, "part_id": "demo-plate"}
    subject = SubjectBinding(
        id="subject",
        role="result",
        result_id="run:producer:result",
        producer=ProducerIdentity(
            run_id="run", step_id="producer", attempt=1, output_port="result"
        ),
        kind="value",
        value=value,
        sha256=canonical_digest(value),
    )
    return ValidationRequest(
        trace_id=trace_id,
        workspace_id="workspace",
        invocation_id="inspect",
        subjects=(subject,),
        profile_ref=profile.reference(),
        baseline_ref=profile.baseline.reference(),
        idempotency_key=key,
    )


def _service(tmp_path, *, registry=None, provider_readback=None):
    return ProcessValidationService(
        ProcessValidationRepository(tmp_path / "state.sqlite3"),
        SubjectResolver(
            "workspace",
            str(tmp_path),
            provider_readback=provider_readback,
        ),
        registry=registry,
    )


def test_concurrent_duplicate_invocation_runs_the_reader_only_once(tmp_path):
    profile = load_profile("structured-demo")
    entered, release = Event(), Event()

    class BlockingReader(StructuredReader):
        def __init__(self):
            self.calls = 0
            self.lock = Lock()

        def measure(self, snapshot, check, context):
            with self.lock:
                self.calls += 1
                call = self.calls
            if call == 1:
                entered.set()
                assert release.wait(5)
            return super().measure(snapshot, check, context)

    reader = BlockingReader()
    registry = ReaderRegistry()
    registry.register(reader)
    service = _service(tmp_path, registry=registry)
    request = _value_request(profile)

    with ThreadPoolExecutor(max_workers=1) as pool:
        first = pool.submit(service.evaluate, request, profile)
        assert entered.wait(5)
        duplicate = service.evaluate(request, profile)
        assert duplicate.attempt.state == "running"
        assert duplicate.assessment is None
        assert not duplicate.release_eligible
        release.set()
        completed = first.result(timeout=5)

    repeated = service.evaluate(request, profile)
    assert completed.release_eligible and repeated.release_eligible
    assert repeated.assessment.id == completed.assessment.id
    assert reader.calls == len(profile.checks)


def test_active_cancellation_releases_reader_resource_and_is_terminal(tmp_path):
    profile = load_profile("structured-demo")
    entered, cleaned, cancelled = Event(), Event(), Event()

    class OwnedResourceReader(StructuredReader):
        open_resources = 0

        def measure(self, snapshot, check, context):
            self.open_resources += 1
            entered.set()
            try:
                while not cancelled.wait(0.01):
                    context.checkpoint()
                context.checkpoint()
                raise AssertionError("cancel checkpoint must stop the reader")
            finally:
                self.open_resources -= 1
                cleaned.set()

    reader = OwnedResourceReader()
    registry = ReaderRegistry()
    registry.register(reader)
    service = _service(tmp_path, registry=registry)
    request = _value_request(profile, key="cancel-active")

    with ThreadPoolExecutor(max_workers=1) as pool:
        future = pool.submit(service.evaluate, request, profile, cancelled=cancelled)
        assert entered.wait(5)
        cancelled.set()
        outcome = future.result(timeout=5)

    assert cleaned.is_set() and reader.open_resources == 0
    assert outcome.attempt.state == "cancelled"
    assert not outcome.release_eligible
    assert {finding.code for finding in outcome.assessment.findings} == {
        "validation.cancelled"
    }
    with pytest.raises(ValueError, match="unchanged nonterminal"):
        service.repository.resume(request, outcome.attempt.id)


def test_provider_readback_receives_exact_trace_and_pinned_revision(tmp_path):
    base = load_profile("structured-demo")
    profile = ValidationProfile(
        **{
            **base.model_dump(),
            "version": "provider-security",
            "supported_kinds": ("provider",),
        }
    )
    content = json.dumps(
        {"length_mm": 100, "part_id": "demo-plate"},
        separators=(",", ":"),
    ).encode()
    subject = SubjectBinding(
        id="provider-subject",
        role="result",
        result_id="provider-result",
        producer=ProducerIdentity(
            run_id="provider-run",
            step_id="producer",
            attempt=1,
            output_port="result",
        ),
        kind="provider",
        format="json",
        provider_id="qualified-provider",
        resource_id="resource-1",
        revision="revision-7",
        sha256=hashlib.sha256(content).hexdigest(),
    )
    request = ValidationRequest(
        trace_id="trace-provider-7",
        workspace_id="workspace",
        invocation_id="inspect-provider",
        subjects=(subject,),
        profile_ref=profile.reference(),
        baseline_ref=profile.baseline.reference(),
        idempotency_key="provider-security",
    )
    observed = []

    def readback(bound, context):
        observed.append((context.trace_id, bound.provider_id, bound.revision))
        return content

    outcome = _service(tmp_path, provider_readback=readback).evaluate(request, profile)
    assert outcome.release_eligible
    # The same pinned resource is read once for measurement and again for the
    # post-read stability guard; both calls retain the invocation trace.
    assert observed == [
        ("trace-provider-7", "qualified-provider", "revision-7"),
        ("trace-provider-7", "qualified-provider", "revision-7"),
    ]
    assert outcome.assessment.request.trace_id == "trace-provider-7"


@pytest.mark.parametrize(
    ("raw", "budget", "code"),
    [
        (
            ("[" * 70 + "0" + "]" * 70).encode(),
            ResourceBudget(),
            "reader.depth_limit",
        ),
        (
            json.dumps(list(range(100))).encode(),
            ResourceBudget(max_entities=20),
            "reader.entity_limit",
        ),
    ],
)
def test_untrusted_deep_or_entity_heavy_json_fails_closed(tmp_path, raw, budget, code):
    profile = load_profile("structured-demo")
    path = tmp_path / "untrusted.json"
    path.write_bytes(raw)
    subject = SubjectBinding(
        id="untrusted",
        role="result",
        result_id="untrusted-result",
        producer=ProducerIdentity(
            run_id="run", step_id="producer", attempt=1, output_port="result"
        ),
        kind="file",
        format="json",
        locator="untrusted.json",
        encoding="raw-bytes",
        sha256=hashlib.sha256(raw).hexdigest(),
    )
    request = ValidationRequest(
        trace_id="trace-untrusted",
        workspace_id="workspace",
        invocation_id="inspect-untrusted",
        subjects=(subject,),
        profile_ref=profile.reference(),
        baseline_ref=profile.baseline.reference(),
        idempotency_key=code.replace(".", "-"),
        budget=budget,
    )

    outcome = _service(tmp_path).evaluate(request, profile)
    assert not outcome.release_eligible
    assert outcome.attempt.state == "blocked"
    assert {finding.code for finding in outcome.assessment.findings} == {code}
    assert path.read_bytes() == raw


def test_stable_duplicate_result_keeps_digest_and_safe_artifact_references(tmp_path):
    profile = load_profile("structured-demo")
    service = _service(tmp_path)
    request = _value_request(profile, key="stable-result")
    first = service.evaluate(request, profile)
    repeated = service.evaluate(request, profile)

    assert repeated.assessment == first.assessment
    report = service.get_result(first.assessment.id)
    assert report.assessment_digest == canonical_digest(first.assessment)
    assert report.assessment.id == first.assessment.id
    assert all(
        not reference.startswith(("/", "file:", "C:\\"))
        for row in report.traceability
        for reference in row.evidence_refs
    )
