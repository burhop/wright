import { useCallback, useMemo, useState } from "react";
import type { ProcessRef } from "@wright/process-client";
import type { WorkspaceWorkflowSourceDocument } from "../../services/workspace-service";
import { recoveryWorkflowSourceTitle } from "../workflow-recovery/recovery-authoring";
import { NativeWorkflowPanel } from "./NativeWorkflowPanel";
import { NativeProcessPanel } from "./NativeProcessPanel";
import { NativeSourceClient } from "./native-source-client";
import { createNativePanelProcessClient, type NativeProcessCall } from "./native-process-client";

/** One host surface, existing editor and working controller, no document-tab imitation. */
export function NativePanelContent({initial,sourceClient,call,sessionId,workspaceName,initialProcess,initialRunId,workingViewEnabled,onDirty,theme}: {
  readonly initial: WorkspaceWorkflowSourceDocument;
  readonly sourceClient: NativeSourceClient;
  readonly call: NativeProcessCall;
  readonly sessionId: string;
  readonly workspaceName: string;
  readonly initialProcess?: ProcessRef;
  readonly initialRunId?: string;
  readonly workingViewEnabled: boolean;
  readonly onDirty: (pending: boolean) => void;
  readonly theme?: "dark" | "light";
}) {
  const [accepted,setAccepted]=useState(initial);
  const [view,setView]=useState<"editor"|"working">(initialProcess&&workingViewEnabled?"working":"editor");
  const [process,setProcess]=useState<ProcessRef>(initialProcess??{workspace_id:initial.workspace_id,source_path:initial.path,source_digest:initial.storage_digest});
  const [run,setRun]=useState(initialRunId);
  const [workingGeneration,setWorkingGeneration]=useState(0);
  const [sourceDirty,setSourceDirty]=useState(false);
  const [workingDirty,setWorkingDirty]=useState(false);
  const [notice,setNotice]=useState("");
  const native=useMemo(()=>createNativePanelProcessClient({process,sessionId,workspaceName,call}),[process,sessionId,workspaceName,call]);
  const sourceChange=useCallback((pending:boolean)=>{setSourceDirty(pending);onDirty(pending||workingDirty);},[onDirty,workingDirty]);
  const workingChange=useCallback((pending:boolean)=>{setWorkingDirty(pending);if(!pending)setNotice("");onDirty(pending||sourceDirty);},[onDirty,sourceDirty]);
  const openWorking=async()=>{
    if(sourceDirty||workingDirty)return;
    try {
      const stored=await sourceClient.read();
      if(stored.storage_digest!==accepted.storage_digest){setNotice("The saved workflow changed. Compare or reload it before preparing another run.");return;}
      if(process.source_digest!==stored.storage_digest){setProcess({workspace_id:stored.workspace_id,source_path:stored.path,source_digest:stored.storage_digest});setRun(undefined);}
      setNotice("");setView("working");
    }catch{setNotice("Wright could not read the accepted workflow. Your draft is kept.");}
  };
  const openEditor=()=>{
    if(workingDirty){setNotice("Finish or reconcile the pending change before leaving this working view.");return;}
    if(process.source_digest!==accepted.storage_digest){setNotice("This run belongs to an older source revision. Open the current workflow from the conversation to edit it.");return;}
    setNotice("");setView("editor");
  };
  return <div style={{height:"100dvh",minHeight:0}}>
    {notice&&<p role="status">{notice}</p>}
    <div style={{display:view==="editor"?"block":"none",height:"100%"}}>
      <NativeWorkflowPanel initial={initial} client={sourceClient} workspaceName={workspaceName} onDirty={sourceChange} onAccepted={setAccepted} onOpenWorkingView={workingViewEnabled?()=>void openWorking():undefined}/>
    </div>
    {view==="working"&&workingViewEnabled&&<NativeProcessPanel key={`${process.source_digest}:${workingGeneration}`} {...native} sessionId={sessionId} workspaceName={workspaceName} title={process.source_digest===accepted.storage_digest?(recoveryWorkflowSourceTitle(accepted.source)??accepted.path):process.source_path} runId={run} theme={theme} onDirty={workingChange} onOpenWorkflow={openEditor} onRunAttached={setRun} onPrepareAnother={()=>{setRun(undefined);setWorkingGeneration(value=>value+1);}}/>}
  </div>;
}
