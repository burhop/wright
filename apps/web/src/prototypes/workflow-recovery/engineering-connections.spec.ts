import { expect,it } from "vitest";
import { engineeringConnectionIssue } from "./engineering-connections";
import { applicationPortId,type ApplicationCapabilities } from "./ApplicationTaskOptions";
import { initialWorkflow,type RecoveryBlock,type RecoveryPort } from "./model";

it("requires the declared receiving format even when both sockets have file type",()=>{
  const producer={...initialWorkflow.blocks[0],id:"block.producer",configuration:{mcp_server:"first",application_resource:JSON.stringify({kind:"cad_model",exports:[{id:"step",format:"step",name:"model.step"}]})}} as RecoveryBlock;
  const consumer={...producer,id:"block.consumer",configuration:{mcp_server:"second",application_resource:JSON.stringify({kind:"cad_model",source:"upstream",exports:[]})}} as RecoveryBlock;
  const source={...initialWorkflow.ports[0],id:applicationPortId(producer,"step"),ownerBlockId:producer.id,direction:"output",typeId:"type.file.workspace",cardinality:"one"} as RecoveryPort;
  const target={...source,id:applicationPortId(consumer,"input"),ownerBlockId:consumer.id,direction:"input"} as RecoveryPort;
  const workflow={...initialWorkflow,blocks:[producer,consumer],ports:[source,target]};
  const capability={supported:true,import_formats:["step"],import_kinds:["file"]} as ApplicationCapabilities;
  expect(engineeringConnectionIssue(workflow,source.id,target.id,{second:capability})).toBeNull();
  expect(engineeringConnectionIssue(workflow,source.id,target.id,{second:{...capability,import_formats:["iges"]}})).toContain("needs iges");
  expect(engineeringConnectionIssue(workflow,source.id,target.id,{})).toContain("Checking");
  expect(engineeringConnectionIssue({...workflow,ports:[{...source,cardinality:"many"},target]},source.id,target.id,{second:capability})).toContain("one result");
});

it("offers workspace file and image inputs only for declared kinds and formats",()=>{
  const producer={...initialWorkflow.blocks[0],configuration:{__wright_authoring_section:"input",workspace_file:"reference.PNG"}} as RecoveryBlock;
  const consumer={...producer,id:"block.consumer",configuration:{mcp_server:"second",application_resource:JSON.stringify({kind:"cad_model",source:"upstream",exports:[]})}} as RecoveryBlock;
  const source={...initialWorkflow.ports[0],id:"port.image",ownerBlockId:producer.id,direction:"output",typeId:"type.image.reference-set",cardinality:"one"} as RecoveryPort;
  const target={...source,id:applicationPortId(consumer,"input"),ownerBlockId:consumer.id,direction:"input"} as RecoveryPort;
  const workflow={...initialWorkflow,blocks:[producer,consumer],ports:[source,target]};
  const cap={supported:true,import_formats:["png"],import_kinds:["image"]} as ApplicationCapabilities;
  expect(engineeringConnectionIssue(workflow,source.id,target.id,{second:cap})).toBeNull();
  expect(engineeringConnectionIssue(workflow,source.id,target.id,{second:{...cap,import_kinds:["file"]}})).not.toBeNull();
  const fileWorkflow={...workflow,blocks:[{...producer,configuration:{...producer.configuration,workspace_file:"models/bracket.psm"}},consumer],ports:[{...source,typeId:"type.file.workspace"},target]};
  expect(engineeringConnectionIssue(fileWorkflow,source.id,target.id,{second:{...cap,import_formats:["psm"],import_kinds:["file"]}})).toBeNull();
  expect(engineeringConnectionIssue({...fileWorkflow,ports:[{...source,typeId:"type.file.workspace",cardinality:"many"},target]},source.id,target.id,{second:cap})).toContain("one result");
});
