import { exportFormatLabel, outputConsumers, exportFilename, exportPortId } from "./output-contracts";
import { useEffect, useState } from "react";
import type { RecoveryCommand } from "./command-system";
import { findBlock, findPort, recoveryAuthoringSectionKind, type RecoveryBlock, type RecoveryPort, type RecoveryWorkflow } from "./model";
import { readJson } from "./mcp-settings";
import { sourceKey } from "./prompt-settings";
import { cadCommands, cadPortId, type CadOptions } from "./CadTaskOptions";

export interface ApplicationOptions {
  source: "new" | "resource" | "upstream";
  kind: "cad_model" | "analysis" | "structured" | "file" | "image" | "text";
  resource_id?: string; revision?: string; resource_name?: string; from_port?: string;
  edit_mode: "modify" | "copy";
  exports: { id: string; port?: string; format: string; name: string; policy?: "indexed" | "overwrite" }[];
}
export interface ApplicationCapabilities {
  supported: boolean; name: string; kind: ApplicationOptions["kind"];
  can_create: boolean; can_copy: boolean; formats: string[]; export_policies?: string[]; exports_to_workspace?: boolean;
  resources: {resource_id: string; name: string; revision?: string; durability: string}[];
  import_formats?: string[]; import_kinds?: string[];
}
const resultTypes = {cad_model:"type.geometry.brep", analysis:"type.result.structured", structured:"type.result.structured", file:"type.file.workspace", image:"type.image.reference-set", text:"type.value.text"};
const resourceName = (kind: ApplicationOptions["kind"]) => kind === "cad_model" ? "CAD model" : kind === "analysis" ? "Analysis result" : "Application result";
export const applicationPortId = (block: RecoveryBlock, role: string) => `port.${block.id.slice(6)}-application-${role}`;

export function declaredExportFormat(block:RecoveryBlock,portId:string):string|null {
  const cad=readJson<CadOptions|null>(block.configuration.cad,null);
  const app=readJson<ApplicationOptions|null>(block.configuration.application_resource,null);
  return cad?.exports.find(ex=>ex.port===sourceKey(portId)||cadPortId(block,ex.id)===portId)?.format
    ?? app?.exports.find(ex=>ex.port===sourceKey(portId)||applicationPortId(block,ex.id)===portId)?.format ?? null;
}

export function applicationImportRepresentation(block:RecoveryBlock,port:RecoveryPort):{format:string;kind:"file"|"image"}|null {
  const exported=declaredExportFormat(block,port.id);
  if(exported)return {format:exported,kind:"file"};
  if(recoveryAuthoringSectionKind(block)!=="input")return null;
  const filename=String(block.configuration.workspace_file??"").split(/[\\/]/).at(-1)??"";
  const format=filename.includes(".")?filename.split(".").at(-1)!.toLowerCase():"";
  if(!format)return null;
  if(port.typeId==="type.image.reference-set")return {format,kind:"image"};
  return port.typeId==="type.file.workspace"?{format,kind:"file"}:null;
}

export function applicationConnectionCommands(block:RecoveryBlock,workflow:RecoveryWorkflow,sourceId:string,sourceType:string):RecoveryCommand[] {
  const options=readJson<ApplicationOptions|null>(block.configuration.application_resource,null);
  if(!options)return [];
  const id=applicationPortId(block,"input"),existing=findPort(workflow,id);
  const commands:RecoveryCommand[]=workflow.relationships.filter(e=>e.targetId===id).map(e=>({kind:"disconnect",relationshipId:e.id}));
  if(sourceId){
    if(!existing)commands.push({kind:"add_port",port:{id,ownerBlockId:block.id,direction:"input",name:sourceType==="type.file.workspace"?"File":sourceType==="type.image.reference-set"?"Image":resourceName(options.kind),typeId:sourceType,required:false,cardinality:"optional",artifactContractId:null,description:"Identified upstream resource or an explicitly supported export."}});
    else if(existing.typeId!==sourceType)commands.push({kind:"set_port_type",portId:id,typeId:sourceType});
    commands.push({kind:"connect",relationship:{id:`rel.${block.id.slice(6)}-application-resource`,kind:"data",sourceId,targetId:id,label:resourceName(options.kind),condition:null}});
  }
  return [...commands,...applicationCommands(block,workflow,{...options,source:"upstream",from_port:sourceKey(id)})];
}

export function configureApplicationExport(producer:RecoveryBlock,consumer:RecoveryBlock,workflow:RecoveryWorkflow,format:string):RecoveryCommand[] {
  const existing=workflow.ports.find(p=>p.ownerBlockId===producer.id&&p.direction==="output"&&declaredExportFormat(producer,p.id)===format);
  if(existing)return applicationConnectionCommands(consumer,workflow,existing.id,existing.typeId);
  const id=`export-${crypto.randomUUID().slice(0,8)}`;
  const filename=`exports/${sourceKey(producer.id)}.${format.toLowerCase()}`;
  const cad=readJson<CadOptions|null>(producer.configuration.cad,null);
  const app=readJson<ApplicationOptions|null>(producer.configuration.application_resource,null);
  if(cad)return [...cadCommands(producer,workflow,{...cad,exports:[...cad.exports,{id,format,path:filename,policy:"indexed"}]}),
    ...applicationConnectionCommands(consumer,workflow,cadPortId(producer,id),"type.file.workspace")];
  if(app)return [...applicationCommands(producer,workflow,{...app,exports:[...app.exports,{id,format,name:filename,policy:"indexed"}]}),
    ...applicationConnectionCommands(consumer,workflow,applicationPortId(producer,id),"type.file.workspace")];
  return [];
}

export function applicationCommands(block: RecoveryBlock, workflow: RecoveryWorkflow, value: ApplicationOptions | null): RecoveryCommand[] {
  const wanted = value ? [{id:applicationPortId(block,"result"), name:resourceName(value.kind), typeId:resultTypes[value.kind]},
    ...value.exports.map(ex=>({id:exportPortId(block,workflow,ex,"application"),name:ex.name || "Export",typeId:"type.file.workspace"}))] : [];
  const commands: RecoveryCommand[]=[];
  for (const port of workflow.ports.filter(p=>p.ownerBlockId===block.id && p.direction==="output" && p.id.startsWith(applicationPortId(block,"")) && !wanted.some(w=>w.id===p.id))) {
    commands.push(...workflow.relationships.filter(e=>e.sourceId===port.id).map(e=>({kind:"disconnect" as const,relationshipId:e.id})),{kind:"delete_port",portId:port.id});
  }
  for (const port of wanted.filter(p=>!findPort(workflow,p.id))) commands.push({kind:"add_port",port:{...port,ownerBlockId:block.id,direction:"output",required:false,cardinality:"optional",artifactContractId:null,description:"Verified application resource; the consumer must support its representation."}});
  if(value?.source!=="upstream")commands.push(...workflow.relationships.filter(e=>e.targetId===applicationPortId(block,"input")).map(e=>({kind:"disconnect" as const,relationshipId:e.id})));
  commands.push({kind:"set_block_configuration",blockId:block.id,key:"application_resource",value:value?JSON.stringify({...value,output_port:sourceKey(applicationPortId(block,"result")),exports:value.exports.map(ex=>({...ex,port:sourceKey(exportPortId(block,workflow,ex,"application"))}))}):""});
  return commands;
}

export function ApplicationTaskOptions({block,workflow,sessionId,readOnly,onApply}:{block:RecoveryBlock;workflow:RecoveryWorkflow;sessionId?:string;readOnly:boolean;onApply:(commands:RecoveryCommand[])=>boolean}) {
  const server=String(block.configuration.mcp_server??"");
  const options=readJson<ApplicationOptions|null>(block.configuration.application_resource,null);
  if(options)options.exports=options.exports.map((ex,index)=>({...ex,id:ex.id||`legacy-${ex.port??index}`}));
  const [pendingExport,setPendingExport]=useState<{id:string;format:string}|null>(null);
  const [caps,setCaps]=useState<ApplicationCapabilities|null>(null),[error,setError]=useState(""),[busy,setBusy]=useState(false);
  const [exportFormats,setExportFormats]=useState<Record<string,string[]>>({});
  const endpoint=(resources=false)=>`/api/workspace/workflow-sources/application?${new URLSearchParams({session_id:sessionId??"",server_id:server,resources:String(resources)})}`;
  async function load(resources=false):Promise<ApplicationCapabilities>{
    const response=await fetch(endpoint(resources));
    if(!response.ok)throw new Error("Could not load application resources. Check the selected server in Tool Registry.");
    return response.json();
  }
  useEffect(()=>{
    let active=true;setCaps(null);setError("");
    if(sessionId&&server&&!block.configuration.cad)void load().then(value=>{if(active)setCaps(value);}).catch(e=>{if(active&&options)setError(String(e));});
    return()=>{active=false;};
  },[sessionId,server,block.configuration.cad]);
  const producers=workflow.blocks.filter(b=>b.id!==block.id&&(b.configuration.cad||b.configuration.application_resource));
  const producerIdentity=producers.map(b=>`${b.id}:${b.configuration.mcp_server}:${Boolean(b.configuration.cad)}`).join('|');
  useEffect(()=>{
    let current=true;setExportFormats({});
    if(options?.source!=="upstream"||!sessionId)return;
    for(const producer of producers){
      const query=new URLSearchParams({session_id:sessionId,server_id:String(producer.configuration.mcp_server??"")});
      void fetch(`/api/workspace/workflow-sources/${producer.configuration.cad?"cad":"application"}?${query}`).then(async response=>response.ok?response.json():null)
        .then(value=>{if(current&&value?.supported)setExportFormats(formats=>({...formats,[producer.id]:producer.configuration.cad||value.export_policies?.includes("indexed")?value.formats??[]:[]}));}).catch(()=>undefined);
    }
    return()=>{current=false;};
  },[sessionId,options?.source,producerIdentity]);
  async function refresh(){setBusy(true);setError("");try{setCaps(await load(true));}catch(e){setError(String(e));}finally{setBusy(false);}}
  if(block.configuration.cad || (!caps?.supported&&!options))return null;
  const update=(patch:Partial<ApplicationOptions>)=>{if(options)onApply(applicationCommands(block,workflow,{...options,...patch}));};
  const descendants=new Set([block.id]);
  for(let i=0;i<workflow.blocks.length;i++)for(const edge of workflow.relationships){const a=findPort(workflow,edge.sourceId)?.ownerBlockId,b=findPort(workflow,edge.targetId)?.ownerBlockId;if(a&&b&&descendants.has(a))descendants.add(b);}
  const candidates=options?workflow.ports.filter(p=>{
    if(p.direction!=="output"||p.cardinality==="many"||descendants.has(p.ownerBlockId))return false;
    const producer=findBlock(workflow,p.ownerBlockId)!;
    const representation=applicationImportRepresentation(producer,p);
    return (p.typeId===resultTypes[options.kind]&&producer.configuration.mcp_server===server&&p.id===applicationPortId(producer,"result"))
      || Boolean(representation&&(caps?.import_kinds??[]).includes(representation.kind)&&(caps?.import_formats??[]).includes(representation.format));
  }):[];
  const connected=workflow.relationships.find(e=>e.targetId===applicationPortId(block,"input"));
  function connect(sourceId:string){
    onApply(applicationConnectionCommands(block,workflow,sourceId,findPort(workflow,sourceId)?.typeId??"type.file.workspace"));
  }
  const pending = options?.exports.find(ex => ex.id === pendingExport?.id);
  const exportName = (name:string,format:string) => caps?.exports_to_workspace ? exportFilename(name,format) : name;
  const changeFormat = (ex:ApplicationOptions["exports"][number],format:string) => {
    if(format===ex.format)return;
    if(outputConsumers(workflow,exportPortId(block,workflow,ex,"application")).length){setPendingExport({id:ex.id,format});return;}
    update({exports:options!.exports.map(x=>x.id===ex.id?{...x,format,name:exportName(x.name,format)}:x)});
  };
  return <section data-testid="workflow-recovery-application-options">
    <label className="recovery-prompt-editor__checkbox"><input type="checkbox" checked={Boolean(options)} disabled={readOnly||(!caps?.supported&&!options)} onChange={e=>onApply([...applicationCommands(block,workflow,e.target.checked?{source:caps?.can_create?"new":"resource",kind:caps!.kind,edit_mode:"modify",exports:[]}:null),...(e.target.checked?[{kind:"set_block_configuration" as const,blockId:block.id,key:"save_output",value:false}]:[])])}/>Work with {caps?.name??"an application resource"}</label>
    {options&&<>
      <label>Resource to work on<select data-testid="workflow-recovery-application-source" disabled={readOnly} value={options.source} onChange={e=>{update({source:e.target.value as ApplicationOptions["source"]});if(e.target.value==="resource")void refresh();}}>
        <option value="new" disabled={!caps?.can_create}>Create new</option><option value="resource">Select existing</option><option value="upstream">From another block</option>
      </select></label>
      {options.source==="resource"&&<>
        <label>{resourceName(options.kind)}<select data-testid="workflow-recovery-application-resource" value={options.resource_id??""} disabled={readOnly||busy} onChange={e=>{const item=caps?.resources.find(r=>r.resource_id===e.target.value);update({resource_id:item?.resource_id??"",revision:item?.revision,resource_name:item?.name});}}>
          <option value="">Choose a resource</option>{options.resource_id&&!caps?.resources.some(r=>r.resource_id===options.resource_id)&&<option value={options.resource_id}>{options.resource_name??"Previously selected resource"} · refresh to check</option>}
          {caps?.resources.map(item=><option key={item.resource_id} value={item.resource_id}>{item.name}{item.revision?` · ${item.revision}`:""}{item.durability!=="persistent"?" · temporary":""}</option>)}
        </select></label><button type="button" disabled={readOnly||busy} onClick={()=>void refresh()}>{busy?"Loading…":"Refresh resources"}</button>
      </>}
      {options.source==="upstream"&&<label>Resource from<select disabled={readOnly} value={connected?.sourceId??""} onChange={e=>connect(e.target.value)}><option value="">Choose an upstream result</option>{candidates.map(p=><option key={p.id} value={p.id}>{findBlock(workflow,p.ownerBlockId)?.title} · {p.name}</option>)}</select></label>}
      {options.source==="upstream"&&<section data-testid="workflow-application-export-offers">
        {(caps?.import_formats?.length??0)>0?<p>This application accepts {caps!.import_formats!.join(", ")} files. Import creates a new resource and leaves the source unchanged.</p>:<p>Choose a resource from this application. This server has not declared a supported file import.</p>}
        {producers.filter(producer=>!descendants.has(producer.id)).map(producer=>{
          const formats=(exportFormats[producer.id]??[]).filter(format=>caps?.import_formats?.includes(format));
          const count=(readJson<CadOptions|null>(producer.configuration.cad,null)?.exports??readJson<ApplicationOptions|null>(producer.configuration.application_resource,null)?.exports??[]).length;
          return formats.length>0&&(caps?.import_kinds??[]).includes("file")?<div key={producer.id}><b>{producer.title}</b>{formats.map(format=><button type="button" key={format} className="recovery-button recovery-button--secondary" disabled={readOnly||count>=12} onClick={()=>onApply(configureApplicationExport(producer,block,workflow,format))}>Use {format.toUpperCase()} export</button>)}</div>:null;
        })}
      </section>}
      {options.source!=="new"&&<label>Edit<select disabled={readOnly} value={options.edit_mode} onChange={e=>update({edit_mode:e.target.value as ApplicationOptions["edit_mode"]})}><option value="modify">The selected resource</option><option value="copy" disabled={!caps?.can_copy}>A working copy or new revision</option></select></label>}
      <h3>Exports</h3>
      {pending && pendingExport && <section className="recovery-export-impact" role="alert" aria-label="Connected output change">
        <p>{outputConsumers(workflow,exportPortId(block,workflow,pending,"application")).join(", ")} uses {exportFormatLabel(pending.format)}. Keep that output for the existing connections, or disconnect those inputs before changing its format.</p>
        <button type="button" disabled={readOnly || !pendingExport.format || options.exports.length >= 12 || !caps?.export_policies?.includes("indexed")} onClick={() => { if(onApply(applicationCommands(block,workflow,{...options,exports:[...options.exports,{...pending,port:undefined,id:`export-${crypto.randomUUID().slice(0,8)}`,format:pendingExport.format,name:exportName(pending.name,pendingExport.format),policy:"indexed"}]}))) setPendingExport(null); }}>Add {exportFormatLabel(pendingExport.format)} and keep {exportFormatLabel(pending.format)}</button>
        <button type="button" onClick={() => setPendingExport(null)}>Keep {exportFormatLabel(pending.format)}</button>
      </section>}
      {options.exports.map((ex,index)=><fieldset key={ex.id}><legend>Export {index+1}</legend>
        <label>Format<select disabled={readOnly} value={ex.format} onChange={e=>changeFormat(ex,e.target.value)}><option value="">Choose a format</option>{ex.format&&!caps?.formats.includes(ex.format)&&<option>{ex.format}</option>}{caps?.formats.map(f=><option key={f}>{f}</option>)}</select></label>
        <label>{caps?.exports_to_workspace?"File name or path":"Export name"}<input readOnly={readOnly} value={ex.name} onChange={e=>update({exports:options.exports.map(x=>x.id===ex.id?{...x,name:e.target.value}:x)})}/></label>
        {caps?.exports_to_workspace&&<p>Saved in this workspace. A filename without a folder is saved in the workspace root.</p>}
        <label>If the export exists<select disabled={readOnly} value={ex.policy??"indexed"} onChange={e=>update({exports:options.exports.map(x=>x.id===ex.id?{...x,policy:e.target.value as "indexed"|"overwrite"}:x)})}><option value="indexed" disabled={!caps?.export_policies?.includes("indexed")}>Create an indexed export</option><option value="overwrite" disabled={!caps?.export_policies?.includes("overwrite")}>Overwrite existing export</option></select></label>
        {outputConsumers(workflow,exportPortId(block,workflow,ex,"application")).length > 0 && <small>Used by {outputConsumers(workflow,exportPortId(block,workflow,ex,"application")).join(", ")}. Disconnect those inputs before removing this export.</small>}<button type="button" disabled={readOnly || outputConsumers(workflow,exportPortId(block,workflow,ex,"application")).length > 0} onClick={()=>update({exports:options.exports.filter(x=>x.id!==ex.id)})}>Remove export {index+1}</button>
      </fieldset>)}
      <button type="button" disabled={readOnly||!caps?.formats.length||options.exports.length>=12} onClick={()=>update({exports:[...options.exports,{id:`export-${crypto.randomUUID().slice(0,8)}`,format:"",name:""}]})}>Add export</button>
      <small>Results retain their application location. Available result and export links appear in Run details.</small>
    </>}
    {error&&<p role="alert">{error}</p>}
  </section>;
}
