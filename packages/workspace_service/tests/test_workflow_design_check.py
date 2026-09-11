import asyncio
import json
from copy import deepcopy
from contextlib import nullcontext
from dataclasses import replace
from types import SimpleNamespace

import pytest

from workspace_service.workflow_design_check import inspect_verdict, validate_rework
from workspace_service.workflow_source_execution import PromptStep, PromptWorkflow, execute_prompt_workflow, WorkflowSourceExecutionError
from workspace_service.workflow_results import EngineeringResult, Representation, Provenance
from workspace_service.workflow_cad import CadDocument
from packages.workspace_service.tests.test_workflow_source_execution import service


def report(verdict='pass'):
    return dict(verdict=verdict, checks=[dict(requirement='Thickness', expected='2 mm', observed='2 mm',
                status={'pass':'pass','revise':'fail','needs_input':'unverified'}[verdict], evidence=[1])],
                corrections=[] if verdict=='pass' else ['Resolve the thickness requirement.'])


@pytest.mark.parametrize('patch', [
    {'checks': []}, {'verdict': 'approved'}, {'corrections': ['But fix this']},
    {'checks': [{'requirement':'Thickness','expected':'2 mm','observed':'2 mm','status':'pass','evidence':[2]}]},
    {'checks': [{'requirement':'Thickness','expected':'2 mm','observed':'unknown','status':'unverified','evidence':[]}]},
])
def test_invalid_or_unsupported_checks_cannot_release_downstream(patch):
    with pytest.raises(WorkflowSourceExecutionError):
        inspect_verdict(json.dumps({**report(), **patch}), [{'status':'succeeded'}])


def native_inspection():
    # CadInspectionVerificationReport, matching the observed Solid Edge schema.
    observation = {'observationId':'thickness-observed', 'kind':'thickness',
                   'evidenceStatus':{'provenance':'observed', 'disposition':'pass'},
                   'value':{'scalar':{'value':'2', 'unit':'mm'}}}
    return {'operationId':'inspect-model', 'allCriticalRequirementsPass':True,
            'inspection':{'evidenceKind':'inspection', 'scopeId':'inspect-model',
                          'evidenceStatus':{'provenance':'observed', 'disposition':'pass'},
                          'observations':[deepcopy(observation)]},
            'requirementEvaluations':[{'requirementId':'thickness', 'isSatisfied':True,
                                      'isBlocking':False, 'disposition':'pass',
                                      'observation':deepcopy(observation), 'issues':[]}]}


@pytest.mark.parametrize('fault', [
    'critical_false', 'critical_string', 'report_unavailable', 'report_not_evaluated',
    'observation_fail', 'observation_inferred', 'evaluation_blocking', 'evaluation_unsatisfied',
    'evaluation_not_evaluated', 'evaluation_observation_missing', 'evaluations_empty',
    'is_valid_false', 'overall_fail', 'overall_unverified', 'verdict_fail',
])
def test_native_rejection_cannot_be_relabelled_as_pass(fault):
    native = native_inspection()
    if fault == 'critical_false': native['allCriticalRequirementsPass'] = False
    if fault == 'critical_string': native['allCriticalRequirementsPass'] = 'true'
    if fault == 'report_unavailable': native['inspection']['evidenceStatus']['provenance'] = 'unavailable'
    if fault == 'report_not_evaluated': native['inspection']['evidenceStatus']['disposition'] = 'not_evaluated'
    if fault == 'observation_fail': native['inspection']['observations'][0]['evidenceStatus']['disposition'] = 'fail'
    if fault == 'observation_inferred': native['inspection']['observations'][0]['evidenceStatus']['provenance'] = 'inferred'
    if fault == 'evaluation_blocking': native['requirementEvaluations'][0]['isBlocking'] = True
    if fault == 'evaluation_unsatisfied': native['requirementEvaluations'][0]['isSatisfied'] = False
    if fault == 'evaluation_not_evaluated': native['requirementEvaluations'][0]['disposition'] = 'not_evaluated'
    if fault == 'evaluation_observation_missing': native['requirementEvaluations'][0]['observation'] = None
    if fault == 'evaluations_empty': native['requirementEvaluations'] = []
    if fault == 'is_valid_false': native['isValid'] = False
    if fault == 'overall_fail': native['overall'] = 'fail'
    if fault == 'overall_unverified': native['overall'] = {'status':'unverified'}
    if fault == 'verdict_fail': native['verdict'] = 'fail'
    calls = [{'status':'succeeded', 'result':{'result':native}}]
    with pytest.raises(WorkflowSourceExecutionError, match='native evidence that failed or is unverified'):
        inspect_verdict(json.dumps(report()), calls)


def test_native_pass_and_raw_observations_remain_available_for_independent_review():
    assert inspect_verdict(json.dumps(report()), [{'status':'succeeded', 'result':native_inspection()}])['verdict'] == 'pass'
    # The raw face/extent APIs explicitly leave design acceptance to the reviewer.
    raw = {'evidenceStatus':{'provenance':'observed', 'disposition':'not_evaluated'}, 'extentMm':2}
    assert inspect_verdict(json.dumps(report()), [{'status':'succeeded', 'result':raw}])['verdict'] == 'pass'


def test_failed_native_evidence_can_support_revise_or_needs_input():
    native = native_inspection()
    native['allCriticalRequirementsPass'] = False
    native['requirementEvaluations'][0].update(isSatisfied=False, isBlocking=True, disposition='fail')
    for verdict in ('revise', 'needs_input'):
        assert inspect_verdict(json.dumps(report(verdict)), [{'status':'succeeded', 'result':native}])['verdict'] == verdict


def test_omitting_failed_native_verification_from_citations_does_not_release():
    native = native_inspection()
    native['allCriticalRequirementsPass'] = False
    native['requirementEvaluations'][0].update(isSatisfied=False, isBlocking=True, disposition='fail')
    raw_face = {'evidenceStatus':{'provenance':'observed', 'disposition':'not_evaluated'}, 'radiusMm':2}
    check = report()
    check['checks'][0]['evidence'] = [2]
    calls = [{'status':'succeeded', 'result':native}, {'status':'succeeded', 'result':raw_face}]
    with pytest.raises(WorkflowSourceExecutionError, match='native evidence that failed or is unverified'):
        inspect_verdict(json.dumps(check), calls)


def test_uncited_capability_limit_is_not_a_failed_model_verification():
    capability = {'providerId':'solid_edge', 'capabilities':[{'kind':'motion', 'isSupported':False}],
                  'overall':'unverified'}
    check = report()
    check['checks'][0]['evidence'] = [2]
    calls = [{'status':'succeeded', 'result':capability}, {'status':'succeeded', 'result':native_inspection()}]
    assert inspect_verdict(json.dumps(check), calls)['verdict'] == 'pass'


@pytest.mark.parametrize('native_result', [None, '', [], {'content':[]}, {'result':None},
                                        {'allCriticalRequirementsPass':True}, {'result':{'evidenceKind':'inspection'}}])
@pytest.mark.parametrize('cited', [True, False])
def test_known_native_verification_requires_structured_report(native_result, cited):
    check = report()
    check['checks'][0]['evidence'] = [1 if cited else 2]
    calls = [{'tool':'solid-edge__cad.verify_inspection_requirements', 'status':'succeeded', 'result':native_result},
             {'tool':'solid-edge__cad.measure_body_extents', 'status':'succeeded',
              'result':{'evidenceStatus':{'provenance':'observed', 'disposition':'not_evaluated'}, 'extentMm':2}}]
    with pytest.raises(WorkflowSourceExecutionError, match='native evidence that failed or is unverified'):
        inspect_verdict(json.dumps(check), calls)


def test_local_argument_correction_before_native_inspection_is_allowed():
    check = report()
    check['checks'][0]['evidence'] = [2]
    calls = [{'tool':'cad.verify_inspection_requirements', 'status':'invalid_arguments', 'result':{}},
             {'tool':'cad.verify_inspection_requirements', 'status':'succeeded', 'result':{'result':native_inspection()}}]
    assert inspect_verdict(json.dumps(check), calls)['verdict'] == 'pass'


def plan():
    make=PromptStep('make','Make CAD','Create the requested part',None,(),'text','',False,'indexed',
                    output_ports=(('model','cad_model'),), agent_task=True, server_id='cad',
                    cad={'source':'new','native_path':'part.psm','policy':'indexed'})
    check=PromptStep('check','Design Check','Inspect the part',None,(),'json','check.json',True,'indexed',
                    output_ports=(('model_checked','cad_model'),), agent_task=True, server_id='cad',
                    cad={'source':'upstream','from_port':'input','save_native':False}, cad_from='make.model',
                    design_check=True, max_revisions=2)
    quote=PromptStep('quote','Quote','Prepare quote',None,(),'text','quote.txt',True,'indexed',output_ports=(('response','text'),))
    return PromptWorkflow('Test', (make,check,quote), {}, {'check':'make'})


def test_rework_cannot_replay_in_place_or_overwrite_edits():
    workflow=plan()
    for config in ({'source':'session','policy':'indexed'}, {'source':'new','policy':'overwrite'}):
        steps=(replace(workflow.steps[0],cad=config), *workflow.steps[1:])
        with pytest.raises(WorkflowSourceExecutionError): validate_rework(steps,workflow.revisions)


class FakeCad:
    def __init__(self,runtime,step,root,responses,emit):
        self.step=step;self.lock=nullcontext();self.records=[];self.input_document=None
    async def start(self): return ''
    async def finish(self): return CadDocument('cad',{'documentId':'test'}), []
    def engineering_result(self, run_id):
        return EngineeringResult(f'{run_id}:{self.step.id}', 'cad_model', 'Model',
                (Representation('application_document','test',provider_id='cad',resource_id='test'),),
                Provenance(run_id,self.step.id,self.step.output_ports[0][0]))


@pytest.mark.parametrize('verdicts,expected_calls,error_code', [
    (['pass'], ['make','check','quote'], None),
    (['revise','pass'], ['make','check','make','check','quote'], None),
    (['revise','revise','revise'], ['make','check','make','check','make','check'], 'DESIGN_CHECK_REJECTED'),
    (['needs_input'], ['make','check'], 'DESIGN_CHECK_NEEDS_INPUT'),
])
def test_actual_scheduler_gates_revises_and_stops(monkeypatch,tmp_path,verdicts,expected_calls,error_code):
    monkeypatch.setattr('workspace_service.workflow_cad.CadTask', FakeCad)
    calls=[];prompts=[];events=[];sequence=iter(verdicts)
    async def run_task(step,prompt,*args,**kwargs):
        calls.append(step.id);prompts.append(prompt)
        return (json.dumps(report(next(sequence))) if step.design_check else 'Created'), [{'status':'succeeded'}]
    async def generate(*args): calls.append('quote');return 'Quote handoff'
    async def event(value):events.append(value)
    async def run():
        return await execute_prompt_workflow(service=service(tmp_path),workspace_dir=str(tmp_path),plan=plan(),
            input_values={},response_generator=generate,tool_runtime=SimpleNamespace(run_task=run_task),
            action_generator=lambda:None,on_event=event)
    if error_code:
        with pytest.raises(WorkflowSourceExecutionError) as error:asyncio.run(run())
        assert error.value.code==error_code
        assert not (tmp_path/'quote.txt').exists()
    else:
        result=asyncio.run(run())
        assert len(result['steps'])==3
        assert len({r['id'] for r in result['results']})==len(result['results'])
        assert (tmp_path/'quote.txt').read_text()=='Quote handoff'
        if 'revise' in verdicts:
            assert result['revision_attempts']
            assert 'Previous design check' in prompts[2]
            assert any(e['kind']=='design_revision' for e in events)
    assert calls==expected_calls


def test_native_fail_mislabeled_pass_stops_before_export_and_quote(monkeypatch, tmp_path):
    monkeypatch.setattr('workspace_service.workflow_cad.CadTask', FakeCad)
    workflow = plan()
    export = PromptStep('export', 'Flat export', 'Export', None, (), 'text', 'flat.txt', True, 'indexed')
    workflow = replace(workflow, steps=(*workflow.steps[:2], export, workflow.steps[2]))
    calls = []
    native = native_inspection()
    native['allCriticalRequirementsPass'] = False
    native['requirementEvaluations'][0].update(isSatisfied=False, isBlocking=True, disposition='fail')
    async def run_task(step, *args, **kwargs):
        calls.append(step.id)
        return (json.dumps(report()) if step.design_check else 'Created'), [{'status':'succeeded', 'result':native}]
    async def generate(*args):
        calls.append('export-or-quote')
        return 'Must not execute'
    async def run():
        return await execute_prompt_workflow(service=service(tmp_path), workspace_dir=str(tmp_path), plan=workflow,
            input_values={}, response_generator=generate, tool_runtime=SimpleNamespace(run_task=run_task), action_generator=lambda:None)
    with pytest.raises(WorkflowSourceExecutionError, match='native evidence that failed or is unverified'):
        asyncio.run(run())
    assert calls == ['make', 'check']
    assert not (tmp_path / 'flat.txt').exists()
    assert not (tmp_path / 'quote.txt').exists()
