import hashlib,importlib.util,json,zipfile
from pathlib import Path
from workspace_service.workflow_tool_observations import response_from_observations
from workspace_service.process_interfaces.representations import read_3mf_toolpaths
root=Path(__file__).resolve().parent/'gateway-support-01';work=root/'workspace'
spec=importlib.util.spec_from_file_location('inspection',Path.cwd()/'scripts/engineering/inspect_manufacturing_package.py');m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)
tool=json.loads((root/'tool.json').read_text())
report={'scope':'synthetic 20 x 8 x 24 mm overhang in two orientations; not a handle or engineering approval','orientations':{},'profiles':{k:hashlib.sha256((work/(k+'.json')).read_bytes()).hexdigest() for k in ('machine','process','filament')}}
for orientation in ('upright','side'):
 intent=json.loads((root/(orientation+'-intent.json')).read_text());saved=json.loads((root/(orientation+'-response.json')).read_text());body=json.loads(saved['content'][0]['text'])
 assert not saved['is_error'] and body['ok'] is True
 assert all(body[k]==intent['arguments'][k] for k in ('source','output','plate'))
 selector={'server_id':'offline-slicer-check','tool':tool['name'],'schema_digest':tool['schema_digest'],'arguments':intent['arguments']}
 envelope=response_from_observations(selector['server_id'],[{'tool':selector['tool'],'schema_digest':selector['schema_digest'],'arguments':selector['arguments'],'status':'succeeded','result':{'content':saved['content']},'text':saved['content'][0]['text']}])
 (work/(orientation+'-observations.json')).write_text(envelope)
 (work/('inspection-'+orientation)).mkdir(exist_ok=False)
 config={'workspace_root':str(work),'source_mesh':orientation+'.stl','slice_package':'output/'+orientation+'.gcode.3mf','provider_response':orientation+'-observations.json','provider_observation':selector,'output_root':'inspection-'+orientation,'profiles':{k:k+'.json' for k in ('machine','process','filament')},'gcode_entry':'Metadata/plate_1.gcode','success_field':'ok','expected_response_fields':{k:body[k] for k in ('source','output','plate')},'success_contract':'actual pinned provider ok=true with exact source/output; digital fixture only','operation_label':'support_profile_fixture','legacy_previews':True,'nominal_layer_section':{'start_marker':';VT0','end_marker':'; filament end gcode'}}
 result=m.run(config,read_3mf_toolpaths)
 with zipfile.ZipFile(work/config['slice_package']) as z:
  settings=json.loads(z.read('Metadata/project_settings.config'))
  expected={'enable_support':'1','curr_bed_type':'Textured PEI Plate','filament_type':['PETG'],'layer_height':'0.2','nozzle_diameter':['0.4'],'printer_model':'Bambu Lab P1S','sparse_infill_density':'40%','wall_loops':'5'}
  assert all(settings.get(k)==v for k,v in expected.items())
 summary=json.loads((work/result['toolpath_summary']['path']).read_text())
 report['orientations'][orientation]={'package_sha256':hashlib.sha256((work/config['slice_package']).read_bytes()).hexdigest(),'package_bytes':(work/config['slice_package']).stat().st_size,'settings':expected,'inspection':result,'layers':summary['layer_count'],'segments':summary['path_segments'],'response_matches_actual_intent':True}
assert report['orientations']['upright']['segments']['support']>0
assert report['orientations']['side']['segments']['support']==0
(root/'inspection-report.json').write_text(json.dumps(report,indent=2)+'\n')
print(json.dumps(report,indent=2))
