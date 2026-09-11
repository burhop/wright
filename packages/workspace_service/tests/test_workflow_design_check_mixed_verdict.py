"""Captured mixed verdict regression: correction is not design acceptance."""
import asyncio
import json
from pathlib import Path
from types import SimpleNamespace

import pytest

from workspace_service.workflow_design_check import inspect_verdict
from workspace_service.workflow_source_execution import execute_prompt_workflow, WorkflowSourceExecutionError
from packages.workspace_service.tests.test_workflow_design_check import FakeCad, plan, report
from packages.workspace_service.tests.test_workflow_source_execution import service


def captured_report():
    # Exact response retained from the failed run, not regenerated test output.
    return json.loads((Path(__file__).parent / 'fixtures/design-check-mixed-verdict-20260908.json').read_text(encoding='utf-8'))


def successful_calls():
    # The captured report cites eight successful tool calls. Native verification
    # rejection is independently covered by test_workflow_design_check.py.
    return [{'status': 'succeeded'} for _ in range(8)]


def test_actual_mixed_response_is_preserved_for_bounded_correction():
    original = captured_report()
    validated = inspect_verdict(json.dumps(original), successful_calls())
    assert validated == original
    assert [sum(c['status'] == s for c in validated['checks']) for s in ('pass', 'fail', 'unverified')] == [18, 2, 3]
    failures = [c for c in validated['checks'] if c['status'] == 'fail']
    assert '75.2348' in failures[0]['observed']
    assert '37.1348' in failures[1]['observed']


@pytest.mark.parametrize('fault', ['no_failure', 'no_evidence', 'failed_call', 'out_of_range', 'bool_citation', 'no_corrections', 'empty_correction', 'claim_pass'])
def test_mixed_response_still_requires_evidenced_failure_and_correction(fault):
    value = captured_report()
    calls = successful_calls()
    failures = [c for c in value['checks'] if c['status'] == 'fail']
    if fault == 'no_failure':
        for c in failures:
            c['status'] = 'unverified'
    elif fault == 'no_evidence': failures[0]['evidence'] = []
    elif fault == 'failed_call': calls[3]['status'] = 'failed'
    elif fault == 'out_of_range': failures[0]['evidence'] = [9]
    elif fault == 'bool_citation': failures[0]['evidence'] = [True]
    elif fault == 'no_corrections': value['corrections'] = []
    elif fault == 'empty_correction': value['corrections'] = [' ']
    elif fault == 'claim_pass':
        value['verdict'] = 'pass'
        value['corrections'] = []
        for c in failures:
            c['status'] = 'pass'
        # Even after failures are resolved, remaining unknowns prohibit PASS.
    with pytest.raises(WorkflowSourceExecutionError):
        inspect_verdict(json.dumps(value), calls)


@pytest.mark.parametrize('end', ['needs_input', 'revision_limit'])
def test_mixed_revision_never_releases_unknowns_or_exceeds_bound(monkeypatch, tmp_path, end):
    monkeypatch.setattr('workspace_service.workflow_cad.CadTask', FakeCad)
    mixed = captured_report()
    responses = [mixed, report('needs_input')] if end == 'needs_input' else [mixed, mixed, mixed]
    sequence = iter(responses)
    called, prompts, events = [], [], []

    async def run_task(step, prompt, *args, **kwargs):
        called.append(step.id)
        prompts.append(prompt)
        return (json.dumps(next(sequence)) if step.design_check else 'Created'), successful_calls()

    async def generate(*args):
        called.append('quote')
        raise AssertionError('Unverified design must not reach quote')

    async def event(value):
        events.append(value)

    async def run():
        return await execute_prompt_workflow(service=service(tmp_path), workspace_dir=str(tmp_path), plan=plan(),
            input_values={}, response_generator=generate, tool_runtime=SimpleNamespace(run_task=run_task),
            action_generator=lambda: None, on_event=event)

    with pytest.raises(WorkflowSourceExecutionError) as error:
        asyncio.run(run())
    assert error.value.code == ('DESIGN_CHECK_NEEDS_INPUT' if end == 'needs_input' else 'DESIGN_CHECK_REJECTED')
    assert called == ['make', 'check'] * len(responses)
    assert not (tmp_path / 'quote.txt').exists()
    assert '75.2348' in prompts[2]
    assert 'Native flat development' in prompts[2]
    assert 'unverified' in prompts[2]
    assert 'Named datum scheme' in prompts[2]
    checks = [e['report'] for e in events if e['kind'] == 'design_check']
    assert checks[0] == mixed
    assert len([e for e in events if e['kind'] == 'design_revision']) == len(responses) - 1
