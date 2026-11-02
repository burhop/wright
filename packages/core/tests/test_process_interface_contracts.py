"""Process presentation contracts retain identity and never invent authority."""

import json
import base64
from importlib.resources import files

import pytest
from pydantic import TypeAdapter, ValidationError

from core.process_interactions import (
    Action,
    ArtifactRef,
    FileLocator,
    InputSnapshot,
    InputDefinition,
    InputDependency,
    InteractionContext,
    InteractionSnapshot,
    Readiness,
    NavigationTarget,
    Observation,
    PendingInteraction,
    ProcessRef,
    Reason,
    StartReceipt,
    ValueBinding,
    checked_value_schema,
    validate_response,
)
from core.process_interfaces import (
    CodingRole,
    InterfaceBinding,
    InterfaceManifest,
    SourceEnvelope,
    SourceAsset,
    contract_schemas,
)

NOW = "2026-09-30T12:00:00Z"
DIGEST = "a" * 64


def process(**changes):
    return ProcessRef(
        **{
            "workspace_id": "workspace-one",
            "source_path": "workflows/analysis.wflow",
            "source_digest": DIGEST,
            **changes,
        }
    )


@pytest.mark.parametrize(
    "path", ["../other.wflow", "/tmp/p.wflow", "C:/p.wflow", "a\\b", "a//b"]
)
def test_process_paths_are_confined(path):
    with pytest.raises(ValidationError):
        process(source_path=path)


def test_process_rejects_client_supplied_authority():
    with pytest.raises(ValidationError):
        process(principal="administrator")


@pytest.mark.parametrize("length", [171, 8192])
def test_file_locators_preserve_full_paths_without_expanding_source_or_id_bounds(
    length,
):
    path = "outputs/" + "x" * (length - len("outputs/"))
    assert TypeAdapter(FileLocator).validate_python(path) == path
    artifact = ArtifactRef(artifact_ref=path, sha256=DIGEST)
    assert ArtifactRef.model_validate_json(artifact.model_dump_json()) == artifact
    assert NavigationTarget(kind="evidence", artifact_ref=path).artifact_ref == path
    assert (
        Reason(
            code="DETAILS",
            message="Read",
            correction="Open",
            technical_details_ref=path,
        ).technical_details_ref
        == path
    )
    receipt = StartReceipt(
        principal_id="reviewer",
        process=process(),
        request_id="start-one",
        payload_digest=DIGEST,
        input_snapshot_id="input-one",
        input_digest=DIGEST,
        run_id="run-one",
        run_log_path=path,
        created_at=NOW,
    )
    assert receipt.run_log_path == path
    with pytest.raises(ValidationError):
        process(source_path=path)
    with pytest.raises(ValidationError):
        process(workspace_id="w" * 161)


@pytest.mark.parametrize(
    "path",
    [
        "x" * 8193,
        "",
        "../outside",
        "/outside",
        "C:/outside",
        "a\\b",
        "a//b",
        "a/./b",
        "a/../b",
        "a:b",
        "a\x00b",
        "a\nb",
        "a\tb",
        "a\x1fb",
        "a\x7fb",
        " outputs/result.txt",
        "outputs/result.txt ",
    ],
)
def test_file_locators_reject_oversize_ambiguous_and_unconfined_paths(path):
    with pytest.raises(ValidationError):
        ArtifactRef(artifact_ref=path, sha256=DIGEST)


def snapshot(**changes):
    return InputSnapshot.create(
        snapshot_id="inputs-one",
        process=process(),
        created_at=NOW,
        bindings=(ValueBinding(input_id="width", value=100),),
        **changes,
    )


def test_snapshot_round_trip_and_digest_are_stable():
    original = snapshot()
    restored = InputSnapshot.model_validate_json(original.model_dump_json())
    assert restored == original
    assert len(original.digest) == 64
    assert original.bindings[0].value == 100
    assert original.process.source_digest == DIGEST


def test_snapshot_changed_value_cannot_keep_digest():
    data = snapshot().model_dump(mode="json")
    data["bindings"][0]["value"] = 101
    with pytest.raises(ValidationError, match="digest"):
        InputSnapshot.model_validate(data)


def test_snapshot_rejects_duplicate_input_identity():
    with pytest.raises(ValidationError, match="unique"):
        InputSnapshot.create(
            snapshot_id="duplicate",
            process=process(),
            created_at=NOW,
            bindings=(
                ValueBinding(input_id="x", value=1),
                ValueBinding(input_id="x", value=2),
            ),
        )


@pytest.mark.parametrize(
    "value",
    [float("nan"), float("inf"), "x" * 65537],
    ids=["nan", "infinite", "oversized"],
)
def test_inline_values_are_finite_and_bounded(value):
    with pytest.raises(ValidationError):
        ValueBinding(input_id="x", value=value)


@pytest.mark.parametrize(
    "schema",
    [
        {"$ref": "https://example.test/schema.json"},
        {"$defs": {"x": {"$ref": "#/$defs/x"}}, "$ref": "#/$defs/x"},
        {"$ref": "#/$defs/missing"},
        {"type": "string", "python_validator": "run_code()"},
        {"type": "object", "properties": {"x": {"$ref": "file:///secret"}}},
        {"type": "string", "pattern": "(a+)+$"},
    ],
)
def test_unsupported_or_external_schema_is_rejected(schema):
    with pytest.raises(ValueError):
        checked_value_schema(schema)


def test_local_schema_and_declared_response_are_validated():
    schema = {
        "type": "object",
        "$defs": {"choice": {"type": "string", "enum": ["a", "b"]}},
        "properties": {"selection": {"$ref": "#/$defs/choice"}},
        "required": ["selection"],
        "additionalProperties": False,
    }
    checked_value_schema(schema)
    validate_response(schema, {"selection": "a"})
    with pytest.raises(ValueError):
        validate_response(schema, {"selection": "other"})
    with pytest.raises(ValueError):
        validate_response(schema, {"selection": "a", "hidden": True})


def test_waiting_input_requires_declared_schema():
    with pytest.raises(ValidationError):
        PendingInteraction(
            checkpoint_id="checkpoint",
            step_id="selection",
            kind="input",
            subject_digest=DIGEST,
            instructions="Select the candidate.",
        )
    item = PendingInteraction(
        checkpoint_id="checkpoint",
        step_id="selection",
        kind="input",
        subject_digest=DIGEST,
        instructions="Select the candidate.",
        response_schema={"type": "string", "enum": ["a", "b"]},
    )
    assert item.kind == "input"


def test_disabled_action_has_readable_reason_and_enabled_action_exact_subject():
    with pytest.raises(ValidationError):
        Action(action_id="start", operation="start", title="Run", enabled=False)
    with pytest.raises(ValidationError):
        Action(action_id="start", operation="start", title="Run", enabled=True)
    disabled = Action(
        action_id="start",
        operation="start",
        title="Run",
        enabled=False,
        reasons=(
            Reason(
                code="INPUT_REQUIRED",
                message="Choose a material.",
                correction="Provide the required input.",
            ),
        ),
    )
    assert disabled.reasons[0].message == "Choose a material."


def test_missing_progress_is_null_not_fabricated_zero():
    observation = Observation(
        observation_id="operation",
        provider_binding="provider",
        state="waiting_external",
        observed_at=NOW,
    )
    assert observation.progress_percent is None
    assert observation.estimated_remaining_seconds is None
    assert json.loads(observation.model_dump_json())["progress_percent"] is None


@pytest.mark.parametrize("progress", [-1, 101, float("inf")])
def test_progress_is_bounded(progress):
    with pytest.raises(ValidationError):
        Observation(
            observation_id="operation",
            provider_binding="provider",
            state="running",
            observed_at=NOW,
            progress_percent=progress,
        )


def test_navigation_is_an_identity_not_executable_url():
    with pytest.raises(ValidationError):
        NavigationTarget(kind="block", block_id="design", url="javascript:run()")


def test_first_coding_role_inherits_default_and_has_no_tools():
    role = CodingRole(instructions_version="1", instructions_digest=DIGEST)
    assert role.model_policy == "inherit_default"
    assert role.allowed_tools == ()
    assert role.max_repairs == 2
    with pytest.raises(ValidationError):
        CodingRole(
            instructions_version="1", instructions_digest=DIGEST, api_key="secret"
        )
    with pytest.raises(ValidationError):
        CodingRole(instructions_version="1", instructions_digest=DIGEST, max_repairs=3)


def test_binding_optional_absence_needs_a_fallback():
    with pytest.raises(ValidationError):
        InterfaceBinding(
            binding_id="camera", kind="observation", selector="camera", required=False
        )
    item = InterfaceBinding(
        binding_id="camera",
        kind="observation",
        selector="camera",
        required=False,
        fallback="This provider does not supply camera images.",
    )
    assert item.fallback


def test_manifest_cannot_request_generic_tool_or_admin_scope():
    base = dict(
        ui_id="analysis-ui",
        revision_id="revision-one",
        title="Compare candidates",
        process=process(),
        client_version="0.1.0",
        kit_version="0.1.0",
        bindings=(
            InterfaceBinding(binding_id="basis", kind="input", selector="basis"),
        ),
    )
    manifest = InterfaceManifest(**base)
    assert manifest.interaction_version == "wright.process-interaction/1"
    with pytest.raises(ValidationError):
        InterfaceManifest(**base, capabilities=("invokeTool",))
    with pytest.raises(ValidationError):
        InterfaceManifest(**base, capabilities=("administrator",))


@pytest.mark.parametrize(
    "path",
    ["package.json", "server.py", "../App.tsx", "vite.config.ts", "App.tsx/evil"],
)
def test_source_envelope_rejects_arbitrary_build_or_backend(path):
    with pytest.raises(ValidationError):
        SourceEnvelope(
            files={"App.tsx": "export default function App(){return null}", path: "bad"}
        )


def test_source_envelope_requires_fixed_entry():
    with pytest.raises(ValidationError):
        SourceEnvelope(files={"style.css": "body {}"})
    envelope = SourceEnvelope(
        files={"App.tsx": "export default function App(){return null}"}
    )
    assert tuple(envelope.files) == ("App.tsx",)


def test_local_assets_are_typed_bounded_and_confined():
    asset = SourceAsset(
        media_type="image/png",
        data_base64=base64.b64encode(b"\x89PNG\r\n\x1a\n").decode(),
    )
    source = {"App.tsx": "export default function App(){return null}"}
    envelope = SourceEnvelope(files=source, assets={"assets/reference.png": asset})
    assert envelope.assets["assets/reference.png"].decoded().startswith(b"\x89PNG")
    for path in (
        "../reference.png",
        "https://example.test/image.png",
        "assets/reference.js",
    ):
        with pytest.raises(ValidationError):
            SourceEnvelope(files=source, assets={path: asset})
    with pytest.raises(ValidationError):
        SourceAsset(media_type="image/png", data_base64="bad!")
    with pytest.raises(ValidationError):
        SourceAsset(
            media_type="image/png",
            data_base64=base64.b64encode(b"<script>bad</script>").decode(),
        )


def test_source_text_limit_accepts_boundary_and_rejects_next_byte():
    source = "x" * 1_048_576
    assert SourceEnvelope(files={"App.tsx": source}).files["App.tsx"] == source
    with pytest.raises(ValidationError, match="Interface source exceeds 1 MiB"):
        SourceEnvelope(files={"App.tsx": source + "x"})
    with pytest.raises(ValidationError, match="Interface source exceeds 1 MiB"):
        SourceEnvelope(files={"App.tsx": source, "style.css": "x"})


def test_raster_asset_limit_accepts_boundary_and_rejects_next_byte():
    content = b"\x89PNG\r\n\x1a\n" + b"x" * (10_485_760 - 8)
    asset = SourceAsset(
        media_type="image/png", data_base64=base64.b64encode(content).decode()
    )
    assert len(asset.decoded()) == 10_485_760
    with pytest.raises(ValidationError, match="10 MiB bound"):
        SourceAsset(
            media_type="image/png",
            data_base64=base64.b64encode(content + b"x").decode(),
        )


def test_aggregate_assets_limit_cannot_be_bypassed_with_smaller_files():
    content = b"\x89PNG\r\n\x1a\n" + b"x" * (5_242_880 - 8)
    asset = SourceAsset(
        media_type="image/png", data_base64=base64.b64encode(content).decode()
    )
    source = {"App.tsx": "export default function App(){return null}"}
    boundary = SourceEnvelope(
        files=source, assets={"assets/first.png": asset, "assets/second.png": asset}
    )
    assert len(boundary.assets) == 2
    larger = SourceAsset(
        media_type="image/png", data_base64=base64.b64encode(content + b"x").decode()
    )
    with pytest.raises(ValidationError, match="Interface assets exceed 10 MiB"):
        SourceEnvelope(
            files=source,
            assets={"assets/first.png": asset, "assets/second.png": larger},
        )


def test_total_source_asset_count_limit_includes_fixed_source_files():
    asset = SourceAsset(
        media_type="image/png",
        data_base64=base64.b64encode(b"\x89PNG\r\n\x1a\n").decode(),
    )
    source = {"App.tsx": "export default function App(){return null}", "style.css": ""}
    assets = {f"assets/reference-{index}.png": asset for index in range(30)}
    assert len(SourceEnvelope(files=source, assets=assets).assets) == 30
    with pytest.raises(ValidationError, match="32 source/asset files"):
        SourceEnvelope(files=source, assets=assets | {"assets/extra.png": asset})


@pytest.mark.parametrize("kind", ["block", "run", "result", "assessment", "evidence"])
def test_navigation_requires_exact_destination(kind):
    with pytest.raises(ValidationError):
        NavigationTarget(kind=kind)


def test_packaged_schemas_match_domain_contracts():
    resource = files("core").joinpath("process_schemas/contracts-v1.json")
    assert json.loads(resource.read_text(encoding="utf-8")) == contract_schemas()


def test_input_definition_checks_supplied_value_against_declared_schema():
    with pytest.raises(ValidationError):
        InputDefinition(
            input_id="width",
            block_id="basis",
            port_id="width",
            title="Width",
            value_schema={"type": "number", "minimum": 1},
            current_value=ValueBinding(input_id="width", value="wide"),
        )


def test_dependency_classifications_require_declared_producer_or_correction():
    for kind in ("upstream_produced", "declared_human_response", "unresolved"):
        with pytest.raises(ValidationError):
            InputDependency(binding_id="later", classification=kind)


def test_dependency_preserves_full_connected_input_address():
    from jsonschema import validate

    address = "b" * 160 + "." + "p" * 160
    dependency = InputDependency(
        binding_id=address,
        classification="upstream_produced",
        producer_step="s" * 160,
        producer_port="o" * 160,
    )
    assert (
        InputDependency.model_validate_json(dependency.model_dump_json()) == dependency
    )
    assert dependency.binding_id == address
    validate(dependency.model_dump(mode="json"), InputDependency.model_json_schema())
    with pytest.raises(ValidationError):
        InputDependency.model_validate(
            {**dependency.model_dump(), "binding_id": address + "x"}
        )
    with pytest.raises(ValidationError):
        InputDependency.model_validate(
            {**dependency.model_dump(), "producer_step": "s" * 161}
        )


def test_snapshot_projection_does_not_accept_another_input_assessment():
    context = InteractionContext(
        process=process(),
        input_snapshot_id="inputs",
        input_digest=DIGEST,
        generated_at=NOW,
    )
    readiness = Readiness(
        state="ready",
        assessment_id="ready",
        process=process(),
        input_digest="b" * 64,
        assessed_at=NOW,
    )
    with pytest.raises(ValidationError):
        InteractionSnapshot(context=context, state="ready", readiness=readiness)
    with pytest.raises(ValidationError):
        InteractionContext(process=process(), input_digest=DIGEST, generated_at=NOW)


def test_local_schema_expansion_is_bounded_even_without_recursion():
    definitions = {"base": {"type": "string"}}
    previous = "base"
    for i in range(9):
        key = f"level{i}"
        definitions[key] = {
            "type": "object",
            "properties": {
                "a": {"$ref": f"#/$defs/{previous}"},
                "b": {"$ref": f"#/$defs/{previous}"},
                "c": {"$ref": f"#/$defs/{previous}"},
            },
        }
        previous = key
    with pytest.raises(ValueError, match="expansion"):
        checked_value_schema({"$defs": definitions, "$ref": f"#/$defs/{previous}"})
