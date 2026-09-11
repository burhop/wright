import asyncio

import pytest

from workspace_service.workflow_source_execution import (
    WorkflowSourceExecutionError,
    compile_prompt_workflow,
    prepare_prompt_workflow,
)
from packages.workspace_service.tests.test_workflow_source_execution import (
    service,
    source,
    task,
)
from packages.workspace_service.tests.test_workflow_authoring_preflight import (
    definition,
)


def test_disconnected_chains_fail_before_opening_tools_or_writing_files(tmp_path):
    opened = []
    with pytest.raises(WorkflowSourceExecutionError) as error:
        asyncio.run(
            prepare_prompt_workflow(
                service=service(tmp_path, definition("second_result")),
                workspace_dir=str(tmp_path),
                path="workflows/test.wflow",
                expected_digest="a" * 64,
                tool_runtime=lambda: opened.append(True),
            )
        )
    assert error.value.code == "WORKFLOW_DISCONNECTED_PROCESS"
    assert "2 disconnected groups" in str(error.value)
    assert "each independent process to its own workflow" in error.value.correction
    assert "first" in error.value.correction and "second" in error.value.correction
    assert opened == []
    assert not list(tmp_path.iterdir())


def test_two_chains_and_an_isolated_input_are_not_silently_run():
    text = source(
        task("a"), task("b"), task("c"), task("d"), links=[("a", "b"), ("c", "d")]
    )
    text += 'input unused\n  name: "Unused image"\n  inputs: []\n  outputs: []\nend\n'
    with pytest.raises(WorkflowSourceExecutionError, match="3 disconnected groups"):
        compile_prompt_workflow(text)


def test_joining_independent_chains_makes_one_process():
    text = source(
        task("a"),
        task("b"),
        task("c"),
        task("d"),
        links=[("a", "b"), ("c", "d"), ("b", "c")],
    )
    assert [step.id for step in compile_prompt_workflow(text).steps] == [
        "a",
        "b",
        "c",
        "d",
    ]


def test_multiple_inputs_and_outputs_are_one_connected_process():
    merge = task("merge").replace('"key":"merge_prompt"', '"key":"left"')
    merge = merge.replace(
        '"required":false}]',
        '"required":false},{"key":"right","kind":"engineering_document","name":"Right","required":false}]',
    )
    text = source(
        task("a"),
        task("b"),
        merge,
        task("c"),
        task("d"),
        links=[("merge", "c"), ("merge", "d")],
    )
    for key, port in [("a", "left"), ("b", "right")]:
        text += f'connection link_{key}\n  type: item\n  from: "{key}.{key}_response"\n  to: "merge.{port}"\n  label: "Reference"\n  when: null\nend\n'
    assert len(compile_prompt_workflow(text).steps) == 5
