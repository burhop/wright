import { act, cleanup, renderHook } from "@testing-library/react";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";
import { workspaceService, type WorkspaceWorkflowRunSummary } from "../../services/workspace-service";
import { preferObservedRun, useWorkflowRunObserver } from "./useWorkflowRunObserver";

vi.mock("../../services/workspace-service",()=>({workspaceService:{getWorkspaceWorkflowRuns:vi.fn(),runWorkspaceWorkflowSource:vi.fn()}}));
const get=vi.mocked(workspaceService.getWorkspaceWorkflowRuns);
const row=(status:WorkspaceWorkflowRunSummary["status"]="running"):WorkspaceWorkflowRunSummary=>({path:"runs/example/run.json",status,started_at:"2026-09-08T10:00:00Z",source_digest:"exact",source_matches_current:true,results:[],execution:{active_task_id:status==="running"?"design":null,completed_task_ids:[],event_count:1,model_call_count:1,tool_call_count:0,tool_completed_count:0,revision_count:0,outputs:[],last_progress:null,truncated:false}});
beforeEach(()=>{vi.useFakeTimers();get.mockReset();get.mockResolvedValue([row()]);vi.spyOn(document,"visibilityState","get").mockReturnValue("visible");});
afterEach(()=>{cleanup();vi.useRealTimers();vi.restoreAllMocks();});
const flush=()=>act(async()=>{await Promise.resolve();});

describe("scoped run observer",()=>{
  it("polls running at 2s and terminal at 10s, without a run POST",async()=>{
    const {result}=renderHook(()=>useWorkflowRunObserver("session","workspace","workflows/example.workflow.wflow","0"));
    await flush();expect(result.current.record?.status).toBe("running");
    await act(async()=>{await vi.advanceTimersByTimeAsync(1999);});expect(get).toHaveBeenCalledTimes(1);
    get.mockResolvedValue([row("completed")]);
    await act(async()=>{await vi.advanceTimersByTimeAsync(1);});expect(result.current.record?.status).toBe("completed");
    await act(async()=>{await vi.advanceTimersByTimeAsync(9999);});expect(get).toHaveBeenCalledTimes(2);
    await act(async()=>{await vi.advanceTimersByTimeAsync(1);});expect(get).toHaveBeenCalledTimes(3);
    expect(workspaceService.runWorkspaceWorkflowSource).not.toHaveBeenCalled();
  });
  it("preserves last known status on fetch failure and refreshes on focus",async()=>{
    const {result}=renderHook(()=>useWorkflowRunObserver("s","w","path","0"));await flush();
    get.mockRejectedValue(new Error("Network unavailable"));
    await act(async()=>{await vi.advanceTimersByTimeAsync(2000);});
    expect(result.current.record?.status).toBe("running");expect(result.current.error).toContain("Network unavailable");
    get.mockResolvedValue([row("failed")]);await act(async()=>{window.dispatchEvent(new Event("focus"));});
    expect(result.current.record?.status).toBe("failed");expect(result.current.error).toBe("");
  });
  it("ignores stale in-flight replies after changing workspace and path",async()=>{
    let finish!:(value:WorkspaceWorkflowRunSummary[])=>void;
    get.mockImplementationOnce(()=>new Promise(resolve=>{finish=resolve;}));
    const {result,rerender}=renderHook(({w,p})=>useWorkflowRunObserver("s",w,p,"0"),{initialProps:{w:"old",p:"old-path"}});
    const signal=get.mock.calls[0]![2]!.signal!;
    get.mockResolvedValue([]);rerender({w:"new",p:"new-path"});await flush();
    await act(async()=>{finish([row()]);});
    expect(signal.aborted).toBe(true);expect(result.current.record).toBeNull();
    expect(get).toHaveBeenLastCalledWith("s","new-path",expect.objectContaining({workspaceId:"new",latestOnly:true}));
  });
  it("stops hidden polling and refreshes when shown or reopened",async()=>{
    const visibility=vi.spyOn(document,"visibilityState","get").mockReturnValue("hidden");
    const {rerender}=renderHook(({key})=>useWorkflowRunObserver("s","w","path",key),{initialProps:{key:"0"}});
    await flush();expect(get).not.toHaveBeenCalled();
    visibility.mockReturnValue("visible");await act(async()=>{document.dispatchEvent(new Event("visibilitychange"));});
    expect(get).toHaveBeenCalledTimes(1);
    visibility.mockReturnValue("hidden");await act(async()=>{document.dispatchEvent(new Event("visibilitychange"));await vi.advanceTimersByTimeAsync(20000);});
    expect(get).toHaveBeenCalledTimes(1);
    visibility.mockReturnValue("visible");rerender({key:"1"});await flush();expect(get).toHaveBeenCalledTimes(2);
  });
  it("unmount aborts only the status GET and stops timers",async()=>{
    const {unmount}=renderHook(()=>useWorkflowRunObserver("s","w","path","0"));await flush();
    const signal=get.mock.calls[0]![2]!.signal!;unmount();
    await act(async()=>{await vi.advanceTimersByTimeAsync(20000);});
    expect(signal.aborted).toBe(true);expect(get).toHaveBeenCalledTimes(1);expect(workspaceService.runWorkspaceWorkflowSource).not.toHaveBeenCalled();
  });
  it("never takes precedence over a pending POST or an older owned identity",()=>{
    const owned={pending:true,startedAt:"2026-09-08T11:00:00Z",logPath:"runs/owned.json",hasResult:false};
    expect(preferObservedRun(row(),owned)).toBe(false);
    expect(preferObservedRun(row(),{...owned,pending:false})).toBe(false);
    expect(preferObservedRun({...row(),started_at:"2026-09-08T12:00:00Z"},{...owned,pending:false})).toBe(true);
    expect(preferObservedRun({...row(),path:owned.logPath},{...owned,pending:false,hasResult:true})).toBe(false);
    expect(preferObservedRun({...row(),path:owned.logPath},{...owned,pending:false,hasResult:false})).toBe(true);
  });
});
