import { useEffect, useRef, useState } from "react";
import { workspaceService, type WorkspaceWorkflowRunSummary } from "../../services/workspace-service";

const isVisible = () => document.visibilityState !== "hidden";

export function useWorkflowRunObserver(sessionId: string | undefined, workspaceId: string | undefined, path: string, refreshKey: string) {
  const scope = `${sessionId ?? ""}\u0000${workspaceId ?? ""}\u0000${path}`;
  const enabled = Boolean(sessionId && workspaceId);
  const [state, setState] = useState<{scope: string; record: WorkspaceWorkflowRunSummary | null; error: string; checked: boolean}>({scope,record:null,error:"",checked:false});
  const [retry, setRetry] = useState(0);
  const lastKnown = useRef<{scope:string;record:WorkspaceWorkflowRunSummary|null}>({scope,record:null});
  useEffect(() => {
    let current = true;
    let serial = 0;
    let timer: ReturnType<typeof setTimeout> | undefined;
    let request: AbortController | undefined;
    let latest = lastKnown.current.scope === scope ? lastKnown.current.record : null;
    setState(previous => previous.scope === scope ? previous : {scope,record:null,error:"",checked:false});
    if (!enabled) return;
    const refresh = async () => {
      if (!current || !isVisible()) return;
      clearTimeout(timer);
      request?.abort(); // Cancels only this status GET, never a workflow POST.
      request = new AbortController();
      const token = ++serial;
      try {
        const runs = await workspaceService.getWorkspaceWorkflowRuns(sessionId!,path,{workspaceId,latestOnly:true,signal:request.signal});
        if (!current || token !== serial) return;
        const incoming = runs[0] ?? null;
        // Do not let a delayed history snapshot move an observed run backward.
        latest = latest && incoming && Date.parse(incoming.started_at) < Date.parse(latest.started_at) ? latest : incoming ?? latest;
        lastKnown.current={scope,record:latest};
        setState({scope,record:latest,error:"",checked:true});
      } catch (cause) {
        if (!current || token !== serial) return;
        setState(previous => ({scope,record:previous.scope === scope ? previous.record : null,checked:true,
          error:cause instanceof Error ? cause.message : "Execution status could not be refreshed."}));
      } finally {
        if (current && token === serial && isVisible()) timer = setTimeout(() => void refresh(), latest?.status === "running" ? 2000 : 10000);
      }
    };
    const onVisible = () => {
      if (document.visibilityState === "hidden") { clearTimeout(timer); ++serial; request?.abort(); }
      else void refresh();
    };
    const onFocus = () => { void refresh(); };
    void refresh();
    document.addEventListener("visibilitychange",onVisible);
    window.addEventListener("focus",onFocus);
    return () => { current=false; ++serial; clearTimeout(timer); request?.abort(); document.removeEventListener("visibilitychange",onVisible); window.removeEventListener("focus",onFocus); };
  }, [enabled,scope,sessionId,workspaceId,path,refreshKey,retry]);
  return {...(state.scope === scope ? state : {record:null,error:"",checked:false}),enabled,refresh:() => setRetry(value=>value+1)};
}

export function preferObservedRun(record: WorkspaceWorkflowRunSummary | null, owned: {pending:boolean;startedAt:string;logPath:string;hasResult:boolean}) {
  if (!record || owned.pending) return false;
  if (!owned.startedAt) return true;
  if (record.path === owned.logPath) return !owned.hasResult;
  // A different run must be demonstrably newer than the locally requested run.
  // Unparseable timestamps or older history cannot erase a local success/error.
  return Date.parse(record.started_at) > Date.parse(owned.startedAt);
}
