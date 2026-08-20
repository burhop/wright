import type { Page } from "@playwright/test";

import {
  mockManagedRivetSurface,
  mockWorkspaceShell,
} from "../presentation-fixture";

const digest = "a".repeat(64);
export const workflow = {
  workflow_id: "workflow-rivet",
  slug: "rivet",
  revision: 2,
  digest,
  review_state: null,
  reviewer: null,
  reviewed_at: null,
};

const canvas = `<!doctype html><html><body style="margin:0;background:#101827;color:white">
<main data-testid="rivet2-graph-canvas" aria-label="Rivet workflow canvas" style="min-height:100vh;padding:24px">
  <button data-testid="node-1">Inspect CAD</button><output data-testid="focused-node">none</output>
</main><script>
const parentOrigin = new URLSearchParams(location.search).get('parentOrigin'); let project='';
const reply=(message)=>parent.postMessage(message,parentOrigin);
addEventListener('message',(event)=>{ if(event.source!==parent||event.origin!==parentOrigin)return; const m=event.data||{};
 if(m.type==='wright-rivet:set-project'){project=String(m.project||'');reply({type:'wright-rivet:project-set',requestId:m.requestId});}
 else if(m.type==='wright-rivet:get-project')reply({type:'wright-rivet:project',requestId:m.requestId,project});
 else if(m.type==='wright-rivet:set-run-state'){for(const step of m.steps||[]){const node=document.querySelector('[data-testid="'+step.nodeId+'"]');if(node){node.dataset.runState=step.state;node.setAttribute('aria-label',node.textContent+': '+step.state);}}reply({type:'wright-rivet:run-state-set',requestId:m.requestId,count:(m.steps||[]).length});}
 else if(m.type==='wright-rivet:clear-run-state'){reply({type:'wright-rivet:run-state-cleared',requestId:m.requestId});}
 else if(m.type==='wright-rivet:focus-node'){const found=Boolean(document.querySelector('[data-testid="'+m.nodeId+'"]'));if(found)document.querySelector('[data-testid="focused-node"]').textContent=m.nodeId;reply({type:'wright-rivet:node-focused',requestId:m.requestId,nodeId:m.nodeId,found});}
 else if(m.type==='wright-rivet:focus-canvas')reply({type:'wright-rivet:canvas-focused'});
}); setTimeout(()=>reply({type:'wright-rivet:ready',protocolVersion:3}),50);
</script></body></html>`;

const summary = (state: string) => ({
  run_id: "run-inspector",
  workspace_id: "ws-1",
  session_id: "session-1",
  workflow_id: workflow.workflow_id,
  revision: 2,
  digest,
  graph: "Main",
  generation: 1,
  state,
  started_at: "2026-08-20T14:00:00Z",
  completed_at: state === "running" ? null : "2026-08-20T14:00:03Z",
  duration_ms: state === "running" ? null : 3000,
  reason_code: state === "failed" ? "RIVET_MCP_TRANSPORT_CANCELLED" : null,
  trace_id: "trace-safe",
  latest_sequence: state === "running" ? 2 : 4,
  has_outputs: state !== "running",
  has_diagnostic: state === "failed",
  output_truncated: false,
  output_redaction_count: 1,
});

const inspection = (state: "running" | "succeeded" | "failed") => ({
  schema_version: 1,
  run: summary(state),
  progress: { phase: state, current_step_id: "call-1", completed_steps: state === "running" ? 0 : 1, total_steps: 1, last_sequence: state === "running" ? 2 : 4, updated_at: "2026-08-20T14:00:03Z" },
  events: [{ sequence: state === "running" ? 2 : 4, kind: state, occurred_at: "2026-08-20T14:00:03Z", payload: { phase: state } }],
  steps: [{ step_id: "call-1", sequence: 1, node_id: "node-1", label: "Inspect CAD", kind: "mcp_call", qualified_tool_name: "cad.inspect", request_id: "request-safe", trace_id: "trace-safe", state, started_at: "2026-08-20T14:00:01Z", completed_at: state === "running" ? null : "2026-08-20T14:00:03Z", duration_ms: state === "running" ? null : 2000, reason_code: state === "failed" ? "RIVET_MCP_TRANSPORT_CANCELLED" : null, result: null, artifacts: [], redaction_count: 0, complete: true }],
  final_outputs: state === "running" ? [] : [{ result_id: "output", name: "output", origin: "workflow_output", kind: "structured", value: { status: "complete", credential: "[REDACTED]" }, preview: '{"status":"complete","credential":"[REDACTED]"}', complete: true, truncation_reason: null, original_bytes: 48, retained_bytes: 48, digest: "b".repeat(64), redaction_count: 1, artifact: null }],
  diagnostic: state === "failed" ? { code: "RIVET_MCP_TRANSPORT_CANCELLED", summary: "The MCP connection ended while Inspect CAD was running.", recovery_action: "Confirm the server is healthy, then run the saved revision again.", failed_step_id: "call-1", failed_node_id: "node-1", qualified_tool_name: "cad.inspect", trace_id: "trace-safe", full_rerun_available: true, partial_retry_available: false, residue_possible: true } : null,
  completeness: { outputs_complete: true, steps_complete: true, events_complete: true, evidence_available: true, reasons: [] },
});

export async function mockRivetRunInspector(page: Page, terminal: "succeeded" | "failed" = "succeeded") {
  let startCount = 0;
  let inspectionCount = 0;
  let hasRun = false;
  await mockWorkspaceShell(page, []);
  await page.route("**/api/auth/session/status", (route) => route.fulfill({ json: { auth_required: false, authenticated: true } }));
  await mockManagedRivetSurface(page, canvas);
  await page.route("**/api/workspace/workflow-templates", (route) => route.fulfill({ json: { templates: [] } }));
  await page.route("**/api/workspace/workflows?session_id=*", (route) => route.fulfill({ json: { workflows: [workflow] } }));
  await page.route("**/api/workspace/workflows/rivet?session_id=*", (route) => route.fulfill({ json: { ...workflow, project: "version: 4\nmetadata:\n  name: rivet\n", datasets: {} } }));
  await page.route("**/api/workspace/workflows/rivet/runs", async (route) => {
    startCount += 1; hasRun = true;
    await route.fulfill({ status: 201, json: { run_id: "run-inspector", workflow_id: workflow.workflow_id, revision: 2, digest, graph: null, generation: 1, state: "running", reason: null, outputs: null, duration_ms: null, output_truncated: false } });
  });
  await page.route("**/api/workspace/workflows/rivet/runs?*", (route) => route.fulfill({ json: { workflow_id: workflow.workflow_id, current_revision: 2, runs: hasRun ? [summary(inspectionCount ? terminal : "running")] : [] } }));
  await page.route("**/api/workspace/workflows/runs/run-inspector/inspection?*", (route) => {
    inspectionCount += 1;
    return route.fulfill({ headers: { "Cache-Control": "no-store" }, json: inspection(inspectionCount === 1 ? "running" : terminal) });
  });
  await page.route("**/api/workspace/workflows/runs/run-inspector/evidence/export?*", (route) => route.fulfill({ json: { run_id: "run-inspector", token: "[REDACTED]" } }));
  return { startCount: () => startCount, inspectionCount: () => inspectionCount };
}
