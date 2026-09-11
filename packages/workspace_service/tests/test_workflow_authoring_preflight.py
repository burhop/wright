import asyncio
import json
import pytest
from workspace_service.workflow_source_execution import (
    validate_workspace_authoring_shape,
    prepare_prompt_workflow,
    WorkflowSourceExecutionError,
)
from packages.workspace_service.tests.test_workflow_source_execution import service


def definition(port_key="first_result"):
    def section(kind, key, fields):
        return (
            f"{kind} {key}\n"
            + "".join(f"  {k}: {json.dumps(v)}\n" for k, v in fields.items())
            + "end\n"
        )

    workflow = section(
        "workflow",
        "example",
        dict(
            name="Example",
            purpose="Create a document",
            discipline="engineering",
            reviewed_ai_suggestions=True,
        ),
    )
    for name, key in [("first", "first_result"), ("second", port_key)]:
        workflow += section(
            "task",
            name,
            dict(
                name=name,
                purpose="Write a report",
                step_type="work",
                group=None,
                performed_by="ai_assisted",
                inputs=[],
                outputs=[
                    dict(
                        key=key,
                        name="Result",
                        kind="engineering_document",
                        item=None,
                        required=False,
                        quantity="optional",
                        description="Report",
                    )
                ],
                prompt="Write a report.",
                settings={},
                tool=None,
                reusable_step=None,
            ),
        )
    return workflow


def test_duplicate_port_keys_fail_even_on_different_blocks():
    with pytest.raises(
        WorkflowSourceExecutionError, match="Duplicate connection identity"
    ):
        validate_workspace_authoring_shape(definition())
    validate_workspace_authoring_shape(definition("second_result"))


def test_missing_authoring_fields_stop_before_opening_tools(tmp_path):
    text = definition("second_result").replace("  reviewed_ai_suggestions: true\n", "")
    opened = []
    with pytest.raises(WorkflowSourceExecutionError, match="reviewed_ai_suggestions"):
        asyncio.run(
            prepare_prompt_workflow(
                service=service(tmp_path, text),
                workspace_dir=str(tmp_path),
                path="workflows/test.wflow",
                expected_digest="a" * 64,
                tool_runtime=lambda: opened.append(True),
            )
        )
    assert not opened
