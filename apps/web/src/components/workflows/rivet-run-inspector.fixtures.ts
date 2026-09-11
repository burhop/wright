import type {
  RivetRunInspection,
  RivetRunSummary,
} from "../../services/workspace-service";

export const runningRun: RivetRunSummary = {
  run_id: "run-1",
  workspace_id: "workspace-1",
  session_id: "session-1",
  workflow_id: "workflow-1",
  revision: 2,
  digest: "a".repeat(64),
  graph: "Main",
  generation: 1,
  state: "running",
  started_at: "2026-08-20T14:00:00Z",
  completed_at: null,
  duration_ms: null,
  reason_code: null,
  trace_id: "trace-1",
  latest_sequence: 2,
  has_outputs: false,
  has_diagnostic: false,
  output_truncated: false,
  output_redaction_count: 0,
};

export const runningInspection: RivetRunInspection = {
  schema_version: 1,
  run: runningRun,
  progress: {
    phase: "child-call",
    current_step_id: "call-1",
    completed_steps: 0,
    total_steps: 1,
    last_sequence: 2,
    updated_at: "2026-08-20T14:00:02Z",
  },
  events: [],
  run_inputs: [],
  inputs_state: "available",
  steps: [
    {
      step_id: "call-1",
      sequence: 1,
      node_id: "node-1",
      node_type: "mcpToolCall",
      label: "Inspect CAD",
      kind: "mcp_call",
      qualified_tool_name: "cad.inspect",
      request_id: "request-1",
      trace_id: "trace-child",
      state: "running",
      started_at: "2026-08-20T14:00:01Z",
      completed_at: null,
      duration_ms: null,
      reason_code: null,
      inputs: [],
      outputs: [],
      input_state: "available",
      output_state: "unavailable",
      result: null,
      artifacts: [],
      redaction_count: 0,
      complete: true,
    },
  ],
  final_outputs: [],
  diagnostic: null,
  completeness: {
    inputs_complete: true,
    outputs_complete: true,
    steps_complete: true,
    events_complete: true,
    evidence_available: true,
    reasons: [],
  },
};

const result = (
  name: string,
  kind: string,
  value: unknown,
  overrides: Partial<RivetRunInspection["final_outputs"][number]> = {},
): RivetRunInspection["final_outputs"][number] => ({
  result_id: `result-${name}`,
  name,
  origin: "workflow_output",
  kind,
  data_type: kind,
  evidence_state: value === null ? "no-value" : "available",
  value,
  preview:
    value === null
      ? "null"
      : typeof value === "string"
        ? value
        : JSON.stringify(value),
  complete: true,
  truncation_reason: null,
  original_bytes: 8,
  retained_bytes: 8,
  digest: "b".repeat(64),
  redaction_count: 0,
  artifact: null,
  ...overrides,
});

export const succeededInspection: RivetRunInspection = {
  ...runningInspection,
  run: {
    ...runningRun,
    state: "succeeded",
    completed_at: "2026-08-20T14:00:03Z",
    duration_ms: 3000,
    has_outputs: true,
  },
  progress: {
    ...runningInspection.progress,
    phase: "completed",
    completed_steps: 1,
  },
  steps: runningInspection.steps.map((step) => ({
    ...step,
    state: "succeeded",
    completed_at: "2026-08-20T14:00:03Z",
    duration_ms: 2000,
  })),
  final_outputs: [
    result(
      "model",
      "artifact",
      { artifact_id: "artifact-1" },
      {
        data_type: "artifact-reference",
        artifact: { artifact_id: "artifact-1", label: "CAD model" },
      },
    ),
    result("message", "text", "Inspection complete"),
    result("empty", "null", null),
    result("dimensions", "structured", { width: 4, height: 2 }),
    result("items", "list", ["a", "b"]),
    result("report", "link", "https://example.test/report"),
    result("large", "text", "x".repeat(300), {
      complete: false,
      evidence_state: "truncated",
      truncation_reason: "size_limit",
      original_bytes: 1200,
      retained_bytes: 300,
    }),
    result(
      "secret",
      "structured",
      { token: "[REDACTED]" },
      { evidence_state: "redacted", redaction_count: 1 },
    ),
  ],
  completeness: {
    ...runningInspection.completeness,
    outputs_complete: false,
    reasons: ["output_bounded"],
  },
};

export const failedInspection: RivetRunInspection = {
  ...succeededInspection,
  run: {
    ...succeededInspection.run,
    state: "failed",
    reason_code: "RIVET_MCP_TRANSPORT_CANCELLED",
    has_diagnostic: true,
  },
  steps: [
    succeededInspection.steps[0],
    {
      ...succeededInspection.steps[0],
      step_id: "call-2",
      sequence: 2,
      node_id: "node-2",
      label: "Create feature",
      qualified_tool_name: "onshape.create_feature",
      state: "failed",
      reason_code: "RIVET_MCP_TRANSPORT_CANCELLED",
      result: null,
    },
  ],
  diagnostic: {
    code: "RIVET_MCP_TRANSPORT_CANCELLED",
    summary: "The MCP connection ended while Create feature was running.",
    recovery_action:
      "Confirm the server is healthy, then run the saved revision again.",
    failed_step_id: "call-2",
    failed_node_id: "node-2",
    failed_node_label: "Create feature",
    qualified_tool_name: "onshape.create_feature",
    trace_id: "trace-child",
    full_rerun_available: true,
    partial_retry_available: false,
    residue_possible: true,
  },
};

export const cancelledInspection: RivetRunInspection = {
  ...failedInspection,
  run: {
    ...failedInspection.run,
    state: "cancelled",
    reason_code: "RIVET_RUN_CANCELLED",
  },
  diagnostic: {
    ...failedInspection.diagnostic!,
    code: "RIVET_RUN_CANCELLED",
    summary: "The workflow run was cancelled.",
    residue_possible: false,
  },
};

export const emptyInspection: RivetRunInspection = {
  ...succeededInspection,
  run: { ...succeededInspection.run, has_outputs: false },
  final_outputs: [],
  completeness: {
    ...succeededInspection.completeness,
    outputs_complete: true,
    reasons: [],
  },
};

export const historicalRun: RivetRunSummary = {
  ...succeededInspection.run,
  run_id: "run-historical",
  revision: 1,
};
