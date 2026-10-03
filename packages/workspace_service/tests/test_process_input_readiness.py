"""Predictable input dependencies must be resolved before any execution effect."""

import hashlib
from types import SimpleNamespace

import pytest

from core.process_interactions import (
    ArtifactRef,
    FileBinding,
    OptionBinding,
    ProcessRef,
    ValueBinding,
)
from workspace_service.process_interfaces.errors import ProcessInterfaceError
from workspace_service.process_interfaces import inputs as owner
from packages.workspace_service.tests.test_workflow_artifact_review import section, port
from packages.workspace_service.tests.test_workflow_source_execution import service


def source(
    *,
    metadata=None,
    default=None,
    file=None,
    required=True,
    later=False,
    late_root=False,
):
    text = section(
        "workflow",
        "test",
        name="Test",
        purpose="Prepared input fixture",
        discipline="engineering",
        reviewed_ai_suggestions=False,
    )
    settings = {}
    if metadata is not None:
        settings["interaction_input"] = metadata
    if default is not None:
        settings["input_text"] = default
    if file:
        settings.update(input_mode="workspace-file", workspace_file=file)
    text += section(
        "input",
        "brief",
        name="Brief",
        purpose="Prepared input",
        group=None,
        provided_by="engineer",
        step_type="work",
        tool=None,
        reusable_step=None,
        instructions="Use exact input",
        inputs=[],
        outputs=[port("brief_out")],
        settings=settings,
    )
    text += section(
        "task",
        "first",
        name="First",
        purpose="Use exact input",
        group=None,
        step_type="work",
        performed_by="ai_assisted",
        inputs=[port("first_in", required)],
        outputs=[port("first_out")],
        prompt="Prepare a result",
        tool=None,
        reusable_step=None,
        settings={
            "output_format": "text",
            "save_output": True,
            "output_filename": "first.txt",
        },
    )
    if later:
        text += section(
            "task",
            "later",
            name="Later",
            purpose="Use the produced result",
            group=None,
            step_type="work",
            performed_by="ai_assisted",
            inputs=[port("later_in", True)]
            + ([port("late_choice", True)] if late_root else []),
            outputs=[port("later_out")],
            prompt="Use exact earlier result",
            tool=None,
            reusable_step=None,
            settings={"output_format": "text", "output_filename": "later.txt"},
        )
        text += section(
            "connection",
            "upstream",
            type="item",
            **{"from": "first.first_out", "to": "later.later_in"},
            label="Produced result",
            when=None,
        )
    text += section(
        "connection",
        "supplied",
        type="item",
        **{
            "from": "brief.brief_out",
            "to": "later.late_choice" if late_root else "first.first_in",
        },
        label="Input",
        when=None,
    )
    return text


def process(text):
    return ProcessRef(
        workspace_id="workspace",
        source_path="workflows/test.workflow.wflow",
        source_digest=hashlib.sha256(text.encode()).hexdigest(),
    )


def application(root, text):
    app = service(root, text)

    async def read_source(workspace_dir, path):
        return SimpleNamespace(source=text, storage_digest=process(text).source_digest)

    async def read_reference(workspace_dir, path):
        return (root / path).read_bytes()

    async def read_bytes(workspace_dir, path, *, maximum_bytes):
        with (root / path).open("rb") as stream:
            content = stream.read(maximum_bytes + 1)
        if len(content) > maximum_bytes:
            raise ValueError("The file exceeds this reader's supported size.")
        return content

    app.files.read_reference = read_reference
    app.files.read_bytes = read_bytes
    app.workflow_sources.read = read_source
    return app


async def prepare(root, text, bindings=(), **kwargs):
    return await owner.prepare_inputs(
        service=application(root, text),
        workspace_dir=str(root),
        process=process(text),
        source=text,
        bindings=bindings,
        **kwargs,
    )


@pytest.mark.asyncio
async def test_missing_required_input_blocks_before_a_later_stage(tmp_path):
    text = source(later=True)
    prepared = await prepare(tmp_path, text)
    ready = owner.input_readiness(prepared)
    assert ready.state == "blocked"
    assert any(
        item.code == "INPUT_REQUIRED" and item.binding_id == "brief"
        for item in ready.reasons
    )
    assert not (tmp_path / "first.txt").exists()


@pytest.mark.asyncio
@pytest.mark.parametrize("missing_file_default", [False, True])
async def test_missing_input_reason_targets_exact_accepted_block(
    tmp_path, missing_file_default
):
    text = source(file="missing.md") if missing_file_default else source(later=True)
    prepared = await prepare(tmp_path, text)
    readiness = owner.input_readiness(prepared)
    assert readiness.state == "blocked"
    missing = next(
        item for item in readiness.reasons
        if item.code == "INPUT_REQUIRED" and item.binding_id == "brief"
    )
    assert missing.navigation is not None
    assert missing.navigation.kind == "block"
    assert missing.navigation.block_id == "brief"
    assert not (tmp_path / "first.txt").exists()


@pytest.mark.asyncio
async def test_supplied_value_and_declared_upstream_output_are_ready(tmp_path):
    text = source(later=True)
    prepared = await prepare(
        tmp_path, text, (ValueBinding(input_id="brief", value="Use the exact drawing"),)
    )
    ready = owner.input_readiness(prepared)
    assert ready.state == "ready"
    states = {item.binding_id: item for item in ready.dependencies}
    assert states["brief"].classification == "supplied"
    assert states["later.later_in"].classification == "upstream_produced"
    assert states["later.later_in"].producer_step == "first"
    assert states["later.later_in"].producer_port == "first_out"
    assert not (tmp_path / "first.txt").exists()


@pytest.mark.asyncio
async def test_only_explicit_source_default_is_resolved(tmp_path):
    text = source(default="Recorded design requirements")
    prepared = await prepare(tmp_path, text)
    assert prepared.snapshot.bindings[0].provenance == "explicit_default"
    assert prepared.values["brief"] == "Recorded design requirements"
    assert owner.input_readiness(prepared).state == "ready"
    assert owner.input_readiness(await prepare(tmp_path, source())).state == "blocked"


@pytest.mark.asyncio
async def test_overlay_has_exact_identity_and_does_not_rewrite_source(tmp_path):
    text = source(default="Source default")
    path = tmp_path / process(text).source_path
    path.parent.mkdir(parents=True)
    path.write_bytes(text.encode())
    prepared = await prepare(
        tmp_path, text, (ValueBinding(input_id="brief", value="This run's value"),)
    )
    assert prepared.values == {"brief": "This run's value"}
    assert path.read_bytes() == text.encode()
    assert prepared.snapshot.process == process(text)
    assert prepared.definitions[0].default.value == "Source default"
    assert prepared.definitions[0].current_value.value == "This run's value"


@pytest.mark.asyncio
async def test_typed_value_schema_and_explicit_false_default(tmp_path):
    text = source(
        metadata={
            "version": 1,
            "value_schema": {"type": "boolean"},
            "default": False,
            "required": True,
        }
    )
    prepared = await prepare(tmp_path, text)
    assert prepared.snapshot.bindings[0].value is False
    assert prepared.values["brief"] is False
    assert owner.input_readiness(prepared).state == "ready"
    with pytest.raises(ProcessInterfaceError) as error:
        await prepare(tmp_path, text, (ValueBinding(input_id="brief", value="false"),))
    assert error.value.reason.code == "RESPONSE_INVALID"


@pytest.mark.asyncio
async def test_supplied_provenance_cannot_claim_an_unrelated_source_default(tmp_path):
    text = source(default="Accepted default")
    with pytest.raises(ProcessInterfaceError) as error:
        await prepare(
            tmp_path,
            text,
            (
                ValueBinding(
                    input_id="brief",
                    value="Different value",
                    provenance="explicit_default",
                ),
            ),
        )
    assert error.value.reason.code == "RESPONSE_INVALID"


@pytest.mark.asyncio
async def test_default_identity_compares_json_types_not_python_equality(tmp_path):
    text = source(metadata={"version": 1, "value_schema": {}, "default": False})
    with pytest.raises(ProcessInterfaceError):
        await prepare(
            tmp_path,
            text,
            (ValueBinding(input_id="brief", value=0, provenance="explicit_default"),),
        )


def option_metadata():
    return {
        "version": 1,
        "value_schema": {"type": "string"},
        "option_source": {
            "binding_id": "available-materials",
            "server_id": "manufacturing-provider",
            "tool_name": "available_choices",
            "schema_digest": "a" * 64,
        },
    }


class OptionsRuntime:
    def __init__(self, *, readonly=True):
        self.calls = []
        self.readonly = readonly
        self.options = [
            {"id": "material-a", "title": "Loaded material A", "value": "PLA"}
        ]

    def resolve(self, step):
        assert (step.server_id, step.tool_name, step.schema_digest) == (
            "manufacturing-provider",
            "available_choices",
            "a" * 64,
        )
        return SimpleNamespace(
            annotations={"readOnlyHint": self.readonly}, required_approvals=()
        )

    def preflight(self, step):
        return None

    async def call(self, step, arguments, **kwargs):
        self.calls.append((step.tool_name, arguments))
        return {"options": self.options}, "options"


@pytest.mark.asyncio
async def test_provider_choices_are_current_and_an_unselected_required_choice_blocks(
    tmp_path,
):
    runtime = OptionsRuntime()
    text = source(metadata=option_metadata())
    prepared = await prepare(
        tmp_path, text, tool_runtime=runtime, now="2026-09-30T12:00:00Z"
    )
    assert owner.input_readiness(prepared).state == "blocked"
    definition = prepared.definitions[0]
    assert definition.binding_kind == "option"
    assert definition.available_options[0].title == "Loaded material A"
    assert definition.options_observed_at == "2026-09-30T12:00:00+00:00"
    assert definition.options_stale_after == "2026-09-30T12:00:30+00:00"
    choice = OptionBinding(
        input_id="brief",
        option_id="material-a",
        capability=definition.option_source,
        value="PLA",
        observed_at=definition.options_observed_at,
        stale_after=definition.options_stale_after,
    )
    selected = await prepare(
        tmp_path, text, (choice,), tool_runtime=runtime, now="2026-09-30T12:00:01Z"
    )
    assert owner.input_readiness(selected).state == "ready"
    assert selected.values == {"brief": "PLA"}
    assert runtime.calls == [("available_choices", {})] * 2


@pytest.mark.asyncio
async def test_changed_provider_resource_or_expired_choice_cannot_pass(tmp_path):
    runtime = OptionsRuntime()
    text = source(metadata=option_metadata())
    prepared = await prepare(
        tmp_path, text, tool_runtime=runtime, now="2026-09-30T12:00:00Z"
    )
    choice = OptionBinding(
        input_id="brief",
        option_id="material-a",
        capability=prepared.definitions[0].option_source,
        value="PLA",
        observed_at="2026-09-30T12:00:00Z",
        stale_after="2026-09-30T12:00:30Z",
    )
    for changed, now in [
        (False, "2026-09-30T12:01:00Z"),
        (True, "2026-09-30T12:00:01Z"),
    ]:
        if changed:
            runtime.options[0]["value"] = "PETG"
        with pytest.raises(ProcessInterfaceError) as error:
            await prepare(tmp_path, text, (choice,), tool_runtime=runtime, now=now)
        assert error.value.reason.code == "OPTION_STALE"


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "provider_value,supplied_value",
    [(0, False), (1, True), ({"flag": 0}, {"flag": False}), ([1], [True])],
)
async def test_provider_choice_requires_exact_json_value_types(
    tmp_path, provider_value, supplied_value
):
    runtime = OptionsRuntime()
    runtime.options[0]["value"] = provider_value
    metadata = {**option_metadata(), "value_schema": {}}
    text = source(metadata=metadata)
    prepared = await prepare(
        tmp_path, text, tool_runtime=runtime, now="2026-09-30T12:00:00Z"
    )
    definition = prepared.definitions[0]
    choice = OptionBinding(
        input_id="brief",
        option_id="material-a",
        capability=definition.option_source,
        value=supplied_value,
        observed_at=definition.options_observed_at,
        stale_after=definition.options_stale_after,
    )
    with pytest.raises(ProcessInterfaceError) as error:
        await prepare(
            tmp_path, text, (choice,), tool_runtime=runtime, now="2026-09-30T12:00:01Z"
        )
    assert error.value.reason.code == "OPTION_STALE"
    assert runtime.calls == [("available_choices", {})] * 2
    assert not (tmp_path / "first.txt").exists()


@pytest.mark.asyncio
async def test_provider_choice_object_key_order_does_not_change_identity(tmp_path):
    runtime = OptionsRuntime()
    runtime.options[0]["value"] = {"count": 0, "enabled": False}
    metadata = {**option_metadata(), "value_schema": {"type": "object"}}
    text = source(metadata=metadata)
    prepared = await prepare(
        tmp_path, text, tool_runtime=runtime, now="2026-09-30T12:00:00Z"
    )
    definition = prepared.definitions[0]
    choice = OptionBinding(
        input_id="brief",
        option_id="material-a",
        capability=definition.option_source,
        value={"enabled": False, "count": 0},
        observed_at=definition.options_observed_at,
        stale_after=definition.options_stale_after,
    )
    selected = await prepare(
        tmp_path, text, (choice,), tool_runtime=runtime, now="2026-09-30T12:00:01Z"
    )
    assert owner.input_readiness(selected).state == "ready"
    assert selected.values == {"brief": {"enabled": False, "count": 0}}


@pytest.mark.asyncio
async def test_mutating_tool_cannot_be_used_for_option_preflight(tmp_path):
    runtime = OptionsRuntime(readonly=False)
    with pytest.raises(ProcessInterfaceError) as error:
        await prepare(
            tmp_path, source(metadata=option_metadata()), tool_runtime=runtime
        )
    assert error.value.reason.code == "READINESS_UNSUPPORTED"
    assert runtime.calls == []


@pytest.mark.asyncio
async def test_missing_option_capability_is_explicit(tmp_path):
    prepared = await prepare(tmp_path, source(metadata=option_metadata()))
    assert owner.input_readiness(prepared).state == "blocked"
    assert any(item.code == "CAPABILITY_UNAVAILABLE" for item in prepared.reasons)


@pytest.mark.asyncio
async def test_optional_absent_input_is_omitted_without_inventing_a_value(tmp_path):
    text = source(
        metadata={"version": 1, "value_schema": {"type": "string"}, "required": False},
        required=False,
    )
    prepared = await prepare(tmp_path, text)
    assert prepared.values == {} and prepared.snapshot.bindings == ()
    assert prepared.definitions[0].required is False
    assert prepared.plan.steps[0].references == ()
    assert owner.input_readiness(prepared).state == "ready"


@pytest.mark.asyncio
async def test_required_consumer_cannot_be_weakened_by_optional_input_label(tmp_path):
    text = source(
        metadata={"version": 1, "value_schema": {"type": "string"}, "required": False},
        required=True,
    )
    prepared = await prepare(tmp_path, text)
    assert prepared.definitions[0].required is True
    assert owner.input_readiness(prepared).state == "blocked"


@pytest.mark.asyncio
async def test_file_reference_is_hashed_and_reread_without_path_as_contents(tmp_path):
    raw = b"Actual engineering requirements"
    (tmp_path / "input.md").write_bytes(raw)
    text = source(file="input.md")
    supplied = FileBinding(
        input_id="brief",
        reference=ArtifactRef(
            artifact_ref="input.md", sha256=hashlib.sha256(raw).hexdigest()
        ),
    )
    prepared = await prepare(tmp_path, text, (supplied,))
    assert prepared.values["brief"].text == raw.decode()
    assert prepared.values["brief"].path == "input.md"
    assert owner.input_readiness(prepared).state == "ready"
    (tmp_path / "input.md").write_bytes(b"changed requirements")
    with pytest.raises(ProcessInterfaceError) as error:
        await prepare(tmp_path, text, prepared.snapshot.bindings)
    assert error.value.reason.code == "SUBJECT_STALE"


@pytest.mark.asyncio
async def test_missing_default_file_is_actionable_before_start(tmp_path):
    prepared = await prepare(tmp_path, source(file="missing.md"))
    assert owner.input_readiness(prepared).state == "blocked"
    assert prepared.definitions[0].binding_kind == "file"
    assert any(item.code == "INPUT_REQUIRED" for item in prepared.reasons)


@pytest.mark.asyncio
async def test_unknown_schema_or_graph_semantics_are_explicitly_unsupported(tmp_path):
    for text in (
        source(metadata={"version": 2, "value_schema": {"type": "string"}}),
        source(
            metadata={
                "version": 1,
                "value_schema": {"type": "string", "pattern": "unsafe"},
            }
        ),
        source(default="known").replace("when: null", 'when: "conditional"'),
    ):
        with pytest.raises(ProcessInterfaceError) as error:
            await prepare(tmp_path, text)
        assert error.value.reason.code == "READINESS_UNSUPPORTED"


@pytest.mark.asyncio
async def test_unknown_input_or_wrong_value_kind_cannot_enter_snapshot(tmp_path):
    for bindings in (
        (ValueBinding(input_id="other", value="undeclared"),),
        (
            FileBinding(
                input_id="brief",
                reference=ArtifactRef(artifact_ref="input.md", sha256="a" * 64),
            ),
        ),
    ):
        with pytest.raises(ProcessInterfaceError) as error:
            await prepare(tmp_path, source(default="text"), bindings)
        assert error.value.reason.code == "RESPONSE_INVALID"
