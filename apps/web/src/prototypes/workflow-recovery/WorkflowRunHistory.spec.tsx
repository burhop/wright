import { fireEvent,render,screen,waitFor } from "@testing-library/react";
import { expect,it,vi } from "vitest";
import { workspaceService } from "../../services/workspace-service";
import { WorkflowRunHistory } from "./WorkflowRunHistory";

it("reports an interrupted operation without restarting and opens its existing log",async()=>{
  const fetch=vi.spyOn(workspaceService,"getWorkspaceWorkflowRuns").mockResolvedValue([{path:"runs/task/run.json",status:"interrupted",started_at:"2026-09-07T10:00:00Z",source_digest:"digest",results:[],last_event:{kind:"operation_progress",task_title:"Solve analysis",message:"Remote job submitted"}}]);
  const open=vi.fn();
  render(<WorkflowRunHistory sessionId="session" path="workflows/task.wflow" refreshKey="" onOpenFile={open}/>);
  expect(fetch).not.toHaveBeenCalled();
  fireEvent.click(screen.getByText("Previous runs"));
  await waitFor(()=>expect(screen.getByText(/Interrupted ·/)).toBeVisible());
  expect(screen.getByText(/nothing has been restarted/)).toBeVisible();
  expect(screen.getByText(/Remote job submitted/)).toBeVisible();
  fireEvent.click(screen.getByRole("button",{name:"Open saved run log"}));
  expect(open).toHaveBeenCalledWith("runs/task/run.json");
  expect(fetch).toHaveBeenCalledWith("session","workflows/task.wflow");
  fetch.mockRestore();
});
