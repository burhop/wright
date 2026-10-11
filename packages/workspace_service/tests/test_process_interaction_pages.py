"""Bounded pages retain exact bindings and invalidate changed projection cursors."""

from dataclasses import replace

import pytest

from workspace_service.process_interfaces.errors import ProcessInterfaceError
from workspace_service.process_interfaces.projection import project_interactions
from packages.workspace_service.tests.test_process_interaction_projection import (
    facts,
    run,
    result,
    scope,
)


def wide():
    outputs = tuple(
        replace(
            result(),
            id=f"run:model:part-{index}",
            provenance=replace(result().provenance, output_port=f"part-{index}"),
        )
        for index in range(300)
    )
    return facts(run=run(results=outputs))


def test_complete_paged_projection_has_exact_outputs_and_navigation():
    value = wide()
    page = project_interactions(value, scope())
    assert len(page.outputs) == 256 and page.next_page
    outputs, navigation = list(page.outputs), list(page.navigation)
    count = 1
    while page.next_page:
        page = project_interactions(value, scope(), page=page.next_page)
        assert page.context.run_id == "run"
        assert len(page.outputs) <= 256 and len(page.navigation) <= 256
        outputs.extend(page.outputs)
        navigation.extend(page.navigation)
        count += 1
        assert count < 10
    assert len(outputs) == 300 and len({item.result_id for item in outputs}) == 300
    assert {item.result_id for item in navigation if item.kind == "result"} == {
        item.result_id for item in outputs
    }


def test_page_survives_later_read_time_without_changing_recorded_context():
    value = wide()
    token = project_interactions(value, scope()).next_page
    later = replace(value, generated_at="2026-09-30T12:01:00Z")
    assert project_interactions(later, scope(), page=token).outputs


@pytest.mark.parametrize("change", ["cursor", "result", "principal", "source"])
def test_page_cannot_cross_changed_run_result_or_scope(change):
    value = wide()
    token = project_interactions(value, scope()).next_page
    context = scope()
    if change == "cursor":
        value = replace(value, run=replace(value.run, cursor=4))
    elif change == "result":
        updated = replace(
            value.run.results[0],
            representations=(
                replace(value.run.results[0].representations[0], sha256="b" * 64),
            ),
        )
        value = replace(
            value, run=replace(value.run, results=(updated,) + value.run.results[1:])
        )
    elif change == "principal":
        context = replace(context, principal_id="another-user")
    else:
        value = replace(
            value, process=value.process.model_copy(update={"source_digest": "b" * 64})
        )
    with pytest.raises(ProcessInterfaceError) as error:
        project_interactions(value, context, page=token)
    assert error.value.reason.code == "SUBJECT_STALE"


@pytest.mark.parametrize(
    "token",
    ["garbage", "p1:" + "a" * 64 + ":-1", "p1:" + "a" * 64 + ":999999", "x" * 1000],
)
def test_malformed_or_outside_page_requires_fresh_snapshot(token):
    with pytest.raises(ProcessInterfaceError):
        project_interactions(wide(), scope(), page=token)
