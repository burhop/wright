"""Offline compatibility check, not a historical canonical-run reconstruction."""
import hashlib, importlib.util, json, shutil
from pathlib import Path
from workspace_service.workflow_tool_observations import response_from_observations
from workspace_service.process_interfaces.representations import read_3mf_toolpaths
ROOT=Path.cwd()
old=ROOT/'.local-run/experience-review/mesh-repair-036/gateway-slice-repaired-01'
work=ROOT/'.local-run/experience-review/observation-inspection/retained-01'
work.mkdir(exist_ok=False)
(work/'outputs').mkdir()
def sha(p): return hashlib.sha256(p.read_bytes()).hexdigest()
originals={str(p.relative_to(old)):sha(p) for p in old.rglob('*') if p.is_file()}
for name in ('coupon.stl','output/coupon.gcode.3mf','machine.json','process.json','filament.json'):
    dest=work/name;dest.parent.mkdir(parents=True,exist_ok=True)
    shutil.copyfile(old/'workspace'/name,dest)
response=json.loads((old/'response.json').read_text())
intent=json.loads((old/'intent.json').read_text())
audit=json.loads((old/'audit.json').read_text())
assert response['is_error'] is False
assert any(e['request_id']=='slice-01' and e['outcome']=='succeeded' for e in audit)
# This replay fixture supplies a visibly synthetic schema identity: the original
# direct gateway probe did not retain a canonical task-call schema digest.
selector={'server_id':'offline-slicer-check','tool':'offline-slicer-check__slice_model_file','schema_digest':'offline-replay-fixture-not-historical-schema','arguments':intent['arguments']}
call={'tool':selector['tool'],'schema_digest':selector['schema_digest'],'arguments':selector['arguments'],'status':'succeeded','result':{'content':response['content']},'text':'\n'.join(c['text'] for c in response['content'] if c['type']=='text')}
(work/'observations.json').write_text(response_from_observations(selector['server_id'],[call]))
spec=importlib.util.spec_from_file_location('inspection',ROOT/'scripts/engineering/inspect_manufacturing_package.py');operation=importlib.util.module_from_spec(spec);spec.loader.exec_module(operation)
config={'workspace_root':str(work),'source_mesh':'coupon.stl','slice_package':'output/coupon.gcode.3mf','provider_response':'observations.json','provider_observation':selector,'output_root':'outputs','profiles':{k:k+'.json' for k in ('machine','process','filament')},'gcode_entry':'Metadata/plate_1.gcode','success_field':'ok','expected_response_fields':{k:intent['arguments'][k] for k in ('source','output','plate')},'success_contract':'Retained original ok true and exact paths; offline projection compatibility only','operation_label':'retained_response_offline_compatibility','nominal_layer_section':{'start_marker':';VT0','end_marker':'; filament end gcode'},'legacy_previews':True}
result=operation.run(config,read_3mf_toolpaths)
assert originals=={str(p.relative_to(old)):sha(p) for p in old.rglob('*') if p.is_file()}
report={'scope':'Offline replay of retained real coupon response/package; fixture schema identity, no new provider or workflow execution','originals_unchanged':True,'original_response_sha256':sha(old/'response.json'),'original_intent_sha256':sha(old/'intent.json'),'package_sha256':sha(work/'output/coupon.gcode.3mf'),'preview_sha256':sha(work/'outputs/slice-preview.png'),'inspection':result,'handle_qualified':False,'canonical_run_qualified':False}
(work/'report.json').write_text(json.dumps(report,indent=2)); print(json.dumps(report))
