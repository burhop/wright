import { act, cleanup, fireEvent, render, screen, waitFor } from "@testing-library/react";
import { afterEach, beforeAll, beforeEach, expect, it, vi } from "vitest";
import { WorkflowRecoveryConcept, type WorkflowRunOptions, type WorkflowRecoveryRunResult } from "./WorkflowRecoveryConcept";
import { workspaceService, type WorkspaceWorkflowRunSummary } from "../../services/workspace-service";

const task=(id:string)=>`task ${id}
  name: "Report ${id}"
  purpose: "Create a report"
  step_type: work
  group: null
  performed_by: ai_assisted
  inputs: []
  outputs: [{"key":"${id}_out","kind":"engineering_document","name":"Report","quantity":"one","required":true,"item":null,"description":"Report"}]
  prompt: "Create a useful report."
  settings: {"authoring_template":"document","binding_state":"unbound","output_filename":"${id}.html","output_format":"html"}
  tool: null
  reusable_step: null
end`;
const source=`workflow observed_test
  name: "Observed workflow"
  purpose: "Controlled observer test"
  discipline: "mechanical.design"
  reviewed_ai_suggestions: true
end
${task("document_1")}
${task("document_2")}`;
const digest="b".repeat(64);
const props={workflowSource:source,workflowFilePath:"workflows/observed.workflow.wflow",definitionRevision:2,storageDigest:digest,workspaceSessionId:"session",workspaceId:"workspace"};
const snapshot=(status:WorkspaceWorkflowRunSummary["status"]="running"):WorkspaceWorkflowRunSummary=>({path:"runs/observed/20260908T100000Z-run.json",status,started_at:"2026-09-08T10:00:00Z",source_digest:digest,source_matches_current:true,run_id:"recorded-run",results:[],execution:{active_task_id:status==="running"?"document_2":null,completed_task_ids:["document_1"],event_count:8,model_call_count:2,tool_call_count:0,tool_completed_count:0,revision_count:0,outputs:[],last_progress:{kind:"step_started",at:"2026-09-08T10:00:01Z",task_id:"document_2",task_title:"Report document_2",execution_kind:"ai"},truncated:false}});
beforeAll(()=>vi.stubGlobal("ResizeObserver",class {observe=vi.fn();unobserve=vi.fn();disconnect=vi.fn();}));
beforeEach(()=>{vi.spyOn(document,"visibilityState","get").mockReturnValue("visible");vi.spyOn(workspaceService,"getWorkspaceWorkflowReviews").mockResolvedValue([]);});
afterEach(()=>{cleanup();vi.restoreAllMocks();});
const focus=()=>act(async()=>{window.dispatchEvent(new Event("focus"));});

it("recovers an external run into the existing graph and viewer links without POST or inert Cancel",async()=>{
  let current=snapshot();const get=vi.spyOn(workspaceService,"getWorkspaceWorkflowRuns").mockImplementation(async()=>[current]);
  const onRun=vi.fn(),onOpenFile=vi.fn();const rendered=render(<WorkflowRecoveryConcept {...props} onRun={onRun} onOpenFile={onOpenFile}/>);
  const first=screen.getByTestId("workflow-recovery-block-block.document-1"),second=screen.getByTestId("workflow-recovery-block-block.document-2");
  await waitFor(()=>expect(second).toHaveAttribute("data-run-state","running"));
  expect(first).toHaveAttribute("data-run-state","succeeded");
  expect(screen.getByTestId("workflow-recovery-run-start")).toBeDisabled();expect(screen.queryByTestId("workflow-recovery-run-cancel")).toBeNull();
  fireEvent.click(screen.getByTestId("workflow-recovery-run-details-toggle"));
  expect(screen.getByTestId("workflow-run-observed-metrics")).toHaveTextContent("2 model calls");
  fireEvent.click(screen.getByTestId("workflow-recovery-open-run-record"));expect(onOpenFile).toHaveBeenCalledWith(current.path);
  current={...snapshot("completed"),execution_ended_at:"2026-09-08T10:01:00Z",execution:{...current.execution!,active_task_id:null,completed_task_ids:["document_1","document_2"],outputs:[{task_id:"document_2",task_title:"Report document_2",output_path:"reports/result-003.html",output_bytes:123,output_format:"html"}]}};
  await focus();await waitFor(()=>expect(second).toHaveAttribute("data-run-state","idle"));
  expect(first).toHaveAttribute("data-run-state","idle");expect(screen.getByTestId("workflow-recovery-run-start")).not.toBeDisabled();
  fireEvent.click(screen.getByTestId("workflow-recovery-native-run-output-link"));expect(onOpenFile).toHaveBeenCalledWith("reports/result-003.html");
  expect(screen.getByTestId("workflow-native-run-summary")).toHaveTextContent("Workflow completed");
  const readSignal=get.mock.calls.at(-1)![2]!.signal!;rendered.unmount();expect(readSignal.aborted).toBe(true);
  render(<WorkflowRecoveryConcept {...props} onRun={onRun} onOpenFile={onOpenFile}/>);
  await waitFor(()=>expect(screen.getByTestId("workflow-recovery-run-details-toggle")).toHaveTextContent("Completed"));
  expect(onRun).not.toHaveBeenCalled();
});

it.each(["interrupted","unknown"] as const)("preserves truthful %s status and clears pulses",async status=>{
  vi.spyOn(workspaceService,"getWorkspaceWorkflowRuns").mockResolvedValue([snapshot(status)]);
  render(<WorkflowRecoveryConcept {...props} onRun={vi.fn()}/>);
  await waitFor(()=>expect(screen.getByTestId("workflow-recovery-run-details-toggle")).toHaveTextContent(status==="unknown"?"Execution status unknown":"Execution interrupted"));
  fireEvent.click(screen.getByTestId("workflow-recovery-run-details-toggle"));
  expect(screen.getByTestId("workflow-native-run-summary")).not.toHaveTextContent("Ready to run");
  expect(document.querySelector('[data-active="true"][data-run-state="running"]')).toBeNull();
  expect(screen.queryByTestId("workflow-recovery-run-cancel")).toBeNull();
});

it("hides badges for dirty drafts while retaining exact run status and refresh failures",async()=>{
  const get=vi.spyOn(workspaceService,"getWorkspaceWorkflowRuns").mockResolvedValue([snapshot()]);
  render(<WorkflowRecoveryConcept {...props} onRun={vi.fn()}/>);
  const second=screen.getByTestId("workflow-recovery-block-block.document-2");
  await waitFor(()=>expect(second).toHaveAttribute("data-run-state","running"));
  fireEvent.click(second);
  fireEvent.change(screen.getByTestId("workflow-recovery-block-instructions-block.document-2"),{target:{value:"An edited local draft"}});
  expect(second).toHaveAttribute("data-run-state","idle");
  fireEvent.click(screen.getByTestId("workflow-recovery-run-details-toggle"));
  expect(screen.getByTestId("workflow-run-source-mismatch")).toBeVisible();
  get.mockRejectedValue(new Error("Offline"));await focus();
  await waitFor(()=>expect(screen.getByTestId("workflow-run-refresh-error")).toHaveTextContent("last known status"));
  expect(screen.getByTestId("workflow-native-run-summary")).toHaveTextContent("Workflow running");
  expect(screen.getByTestId("workflow-recovery-block-instructions-block.document-2")).toHaveValue("An edited local draft");
});

it("does not assign an active badge to a different saved source",async()=>{
  vi.spyOn(workspaceService,"getWorkspaceWorkflowRuns").mockResolvedValue([{...snapshot(),source_digest:"c".repeat(64),source_matches_current:false}]);
  render(<WorkflowRecoveryConcept {...props} onRun={vi.fn()}/>);
  await waitFor(()=>expect(screen.getByTestId("workflow-recovery-run-details-toggle")).toHaveTextContent("Running"));
  expect(document.querySelector('[data-active="true"][data-run-state="running"]')).toBeNull();
  expect(screen.getByTestId("workflow-recovery-run-start")).toBeDisabled();
});

it("keeps the owned POST and richer result ahead of older observed history",async()=>{
  const get=vi.spyOn(workspaceService,"getWorkspaceWorkflowRuns").mockResolvedValue([]);
  let options!:WorkflowRunOptions;let finish!:(r:WorkflowRecoveryRunResult)=>void;
  const onRun=vi.fn((value?:WorkflowRunOptions)=>{options=value!;return new Promise<WorkflowRecoveryRunResult>(resolve=>{finish=resolve;});});
  render(<WorkflowRecoveryConcept {...props} onRun={onRun}/>);
  await waitFor(()=>expect(screen.getByTestId("workflow-recovery-run-start")).not.toBeDisabled());
  fireEvent.click(screen.getByTestId("workflow-recovery-run-start"));await waitFor(()=>expect(onRun).toHaveBeenCalledOnce());
  await act(async()=>{options.onEvent?.({kind:"run_started",run_log_path:"runs/owned/current.json",at:new Date().toISOString(),task_id:"",task_title:"Owned"});options.onEvent?.({kind:"step_started",at:new Date().toISOString(),task_id:"document_1",task_title:"Owned first step",execution_kind:"ai"});});
  get.mockResolvedValue([{...snapshot("completed"),started_at:"2000-01-01T00:00:00Z"}]);await focus();
  expect(screen.getByTestId("workflow-recovery-block-block.document-1")).toHaveAttribute("data-run-state","running");
  expect(screen.getByTestId("workflow-recovery-run-cancel")).toBeVisible();
  await act(async()=>{finish({outputPath:"owned.html",outputBytes:22,taskTitle:"Owned",runLogPath:"runs/owned/current.json"});});
  expect(screen.getByTestId("workflow-native-run-summary")).toHaveTextContent("Workflow completed");
  expect(screen.getByTestId("workflow-recovery-run-details-toggle")).toHaveTextContent("owned.html");
  expect(onRun).toHaveBeenCalledOnce();
});
