"""Declaration regression checks only; no network, CAD host, solver or grants."""
import importlib.util
import json
from pathlib import Path

import pytest

REPO = Path(__file__).resolve().parents[1]


@pytest.fixture
def prepared_inputs(tmp_path):
    spec = importlib.util.spec_from_file_location('stevecad_heat_example', REPO / 'examples/stevecad-demonstrations/heat-spreader/prepare.py')
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    workspace = tmp_path / 'workspace'
    workspace.mkdir()
    cad = tmp_path / 'cad'
    cad.mkdir()
    for case, width in [('baseline_40',40), ('revision_60',60)]:
        # Deliberately not valid geometry: this suite qualifies declarations only.
        data = ('mock STEP bytes for ' + case).encode()
        (cad / (case + '.step')).write_bytes(data)
        receipt = {'result': {'structuredContent': {
            'document': {'id':case, 'revision':1},
            'model': {'id':'fixture-model-' + case, 'status':'succeeded', 'metadata': {
                'bounds_mm':[100.,float(width),2.], 'extent_mm':[0.,0.,0.,100.,float(width),2.],
                'solids':1,'faces':6,'units':'mm','volume_mm3':100 * width * 2}}}},
            'export': {'sha256':module.h.digest(data)}}
        (cad / ('02-generate-' + case + '.json')).write_text(json.dumps(receipt))
    tools = [{'server_id':server,'tool_name':name,'name':server + '__' + name,'schema_digest':'a' * 64}
             for server,names in [('stevecad-mcp',('read_design','generate_model')),('fixture-solver',('run_simulation',))]
             for name in names]
    return module, workspace, cad, tools


def test_prepared_chain_compiles_with_original_checks_and_real_reviews(prepared_inputs):
    module, workspace, cad, tools = prepared_inputs
    result = module.prepare(workspace, 'declaration-test', tools, cad, 'fixture-solver')
    source = (workspace / result['source_path']).read_text(encoding='utf-8')
    plan = module.compile_prompt_workflow(source)
    assert len(plan.steps) == 9
    from workspace_service.workflow_source_execution import _parse
    tasks = {x['id']:x['fields'] for x in _parse(source) if x['kind']=='task'}
    assert tasks['review_basis']['step_type'] == 'review'
    assert tasks['review_result']['step_type'] == 'review'
    assert tasks['validate_outputs']['settings']['validation']['profile']['name'] == 'heat-spreader-sizing-01-full'
    for identity in ['record_basis','compute_fields']:
        settings = tasks[identity]['settings']
        arguments = json.loads(settings['mcp_arguments'])
        assert arguments['critic_approved'] is False
        assert '{{wright.run_id}}' in arguments['job_name']
    basis_code = json.loads(tasks['record_basis']['settings']['mcp_arguments'])['input_content']
    assert "exist_ok=True" in basis_code
    assert ".open('x'," in basis_code  # Runtime may create the directory; never replace its evidence.
    assert set(tasks['validate_outputs']['settings']['validation']['subjects']) == {
        'basis','baseline_40_geometry','revision_60_geometry','baseline_40_coarse','baseline_40_fine',
        'revision_60_coarse','revision_60_fine','decision','correspondence'}
    assert result['status']=='prepared_not_executed'


def test_changed_step_bytes_require_a_new_verified_export(prepared_inputs):
    module, workspace, cad, tools = prepared_inputs
    (cad/'baseline_40.step').write_bytes(b'different bytes')
    with pytest.raises(ValueError,match='exact export'):
        module.prepare(workspace,'changed-test',tools,cad,'fixture-solver')
    assert not list(workspace.rglob('*.wflow'))


@pytest.mark.parametrize(('field','value'), [('volume_mm3',6000),('units','m')])
def test_hollow_or_wrong_units_do_not_enter_rectangular_idealization(prepared_inputs, field, value):
    module, workspace, cad, tools = prepared_inputs
    path = cad/'02-generate-baseline_40.json'
    receipt = json.loads(path.read_text())
    receipt['result']['structuredContent']['model']['metadata'][field] = value
    path.write_text(json.dumps(receipt))
    with pytest.raises(ValueError,match='Native CAD differs'):
        module.prepare(workspace,'shape-test',tools,cad,'fixture-solver')
    assert not list(workspace.rglob('*.wflow'))
