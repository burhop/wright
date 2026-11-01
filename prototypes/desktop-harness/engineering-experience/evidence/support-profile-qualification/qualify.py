import asyncio,json,os,sys,time,shutil,hashlib
from pathlib import Path
sys.path.insert(0,str(Path.cwd()/'scripts'))
from qualify_stdio_mcp import (_Workspaces,_Audit,_Catalog,_Lifecycle,McpServer,StdioRunner,GatewayService,GatewayNotificationHub,SUPPORTED_PROTOCOL_VERSION)
ROOT=Path(__file__).resolve().parent
async def main():
    out=ROOT/'gateway-support-01';out.mkdir(exist_ok=False)
    work=out/'workspace';work.mkdir();(work/'output').mkdir()
    for name in ('machine','process','filament'):
        shutil.copyfile(ROOT.parent/'slicer-provider-audit/profile-probe'/f'{name}.json',work/f'{name}.json')
    original_process=json.loads((work/'process.json').read_text())
    process={**original_process,'enable_support':'1'}
    (work/'process.json').write_text(json.dumps(process,indent=2)+'\n')
    # Watertight extruded L: 20 x 8 x 24 mm. Digital support fixture only.
    polygon=[(0,0),(4,0),(4,20),(20,20),(20,24),(0,24)]
    vertices=[(x,y,z) for y in (0,8) for x,z in polygon]
    face=[(0,1,2),(0,2,5),(2,3,4),(2,4,5)]
    triangles=face+[(a+6,c+6,b+6) for a,b,c in face]
    for i in range(6):
        j=(i+1)%6
        triangles.extend([(i,j+6,j),(i,i+6,j+6)])
    from collections import Counter
    edges=Counter(tuple(sorted((a,b))) for t in triangles for a,b in zip(t,t[1:]+t[:1]))
    assert set(edges.values())=={2}
    for orientation in ('upright','side'):
        vs=vertices if orientation=='upright' else [(x,24-z,y) for x,y,z in vertices]
        lines=['solid synthetic_overhang']
        for triangle in triangles:
            lines+=['facet normal 0 0 0','outer loop']+['vertex '+' '.join(map(str,vs[i])) for i in triangle]+['endloop','endfacet']
        lines+=['endsolid synthetic_overhang']
        (work/(orientation+'.stl')).write_text('\n'.join(lines)+'\n')
    (out/'profile-change.json').write_text(json.dumps({'change':{'enable_support':{'before':original_process['enable_support'],'after':process['enable_support']}},'original_unchanged':True,'scope':'support coupon qualification only; not accepted handle profile'},indent=2))
    command=['docker','run','--init','--rm','--name','wright-experience-support-slicer-036','-i','--network','none','--read-only','--cap-drop','ALL','--security-opt','no-new-privileges','--user',f'{os.getuid()}:{os.getgid()}','--cpus','2','--memory','4g','--pids-limit','128','--tmpfs','/tmp:rw,exec,nosuid,size=768m','--entrypoint','/usr/bin/xvfb-run','--mount',f'type=bind,source={work},target=/workspace']
    for name in ('machine','process','filament'):
        command+=['-e',f'BAMBU_{name.upper()}_JSON=/workspace/{name}.json']
    command+=['-e','BAMBU_MCP_SKIP_DOTENV=1','sha256:ec4229b057a0a4897ce1a614b4cd627a366704a7f8b071965a0ec084d14b60d3','-a','--server-args=-screen 0 1280x1024x24','/opt/venv/bin/bambu-p1s-mcp']
    now=int(time.time());server=McpServer(server_id='offline-slicer-check',name='Isolated offline slicer qualification',type='stdio',command=command,is_active=True,is_installed=True,status='active',created_at=now,updated_at=now,risk_level='high',default_enabled=False)
    runner=StdioRunner(command,cwd=str(out),operation_timeout=660);audit=_Audit()
    try:
        await runner.start();tools=await runner.list_tools()
        tools=[t for t in tools if t['name']=='slice_model_file'];assert len(tools)==1
        gateway=GatewayService(workspaces=_Workspaces(out,server.server_id),catalog=_Catalog(server,tools),lifecycle=_Lifecycle(runner),audit=audit,notifier=GatewayNotificationHub(),operation_timeout=660)
        gateway.open_session(session_id='qualification',principal_id='wright-validator',workspace_id='qualification-workspace',transport='stdio')
        gateway.initialize_session('qualification',protocol_version=SUPPORTED_PROTOCOL_VERSION,client_name='wright-qualification',client_version='1',client_capabilities={})
        name='offline-slicer-check__slice_model_file';assert [t.name for t in gateway.list_tools('qualification')]==[name]
        from workspace_service.workflow_mcp_execution import schema_digest
        qualified_tool=gateway.list_tools('qualification')[0]
        (out/'command.json').write_text(json.dumps(command,indent=2))
        (out/'tool.json').write_text(json.dumps({'name':qualified_tool.name,'schema_digest':schema_digest(qualified_tool),'input_schema':dict(qualified_tool.input_schema)},indent=2))
        for orientation in ('upright','side'):
            arguments={'source':f'/workspace/{orientation}.stl','output':f'/workspace/output/{orientation}.gcode.3mf','plate':1,'orient':False,'arrange':True,'confirm':True}
            (out/(orientation+'-intent.json')).write_text(json.dumps({'arguments':arguments,'input_sha256':hashlib.sha256((work/(orientation+'.stl')).read_bytes()).hexdigest(),'scope':'synthetic overhang; actual GatewayService; no hardware or process approval'},indent=2))
            result=await gateway.call_tool('qualification','slice-'+orientation,name,arguments)
            (out/(orientation+'-response.json')).write_text(json.dumps({'content':list(result.content),'structured_content':result.structured_content,'is_error':result.is_error},indent=2,default=str))
            print(json.dumps({'orientation':orientation,'is_error':result.is_error,'output':str(out)}),flush=True)
            if result.is_error: raise RuntimeError('Provider returned an error; inspect retained response before further calls')

    finally:
        (out/'audit.json').write_text(json.dumps(audit.events,indent=2,default=str));await runner.stop()
asyncio.run(main())
