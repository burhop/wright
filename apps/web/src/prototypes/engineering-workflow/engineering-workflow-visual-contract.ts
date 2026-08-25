import type { CSSProperties } from "react";

import type {
  WorkflowBlockRole,
  WorkflowConnectionSemantics,
  WorkflowPhaseTone,
} from "./workflow-preview-model";

export const ENGINEERING_WORKFLOW_VISUAL_CONTRACT_VERSION = "cp2a-1";

export const workflowRoleLabels: Readonly<Record<WorkflowBlockRole, string>> = {
  input: "Input",
  "ai-task": "AI task",
  "mcp-action": "MCP action",
  artifact: "Artifact",
  decision: "Review",
  notification: "Notification",
};

export const workflowRoleIcons: Readonly<Record<WorkflowBlockRole, string>> = {
  input: "↥",
  "ai-task": "✦",
  "mcp-action": "⌘",
  artifact: "▤",
  decision: "✓",
  notification: "↗",
};

export const engineeringWorkflowVisualContract = {
  version: ENGINEERING_WORKFLOW_VISUAL_CONTRACT_VERSION,
  theme: "dark-navy-engineering",
  colors: {
    surface: "#030a14",
    input: "#159cff",
    aiTask: "#9b4dff",
    mcpAction: "#16c8c1",
    artifact: "#12c881",
    decision: "#ffb20b",
    feedback: "#ff4058",
    notification: "#76dc48",
    focus: "#8fd2ff",
  },
  roleColors: {
    input: "#159cff",
    "ai-task": "#9b4dff",
    "mcp-action": "#16c8c1",
    artifact: "#12c881",
    decision: "#ffb20b",
    notification: "#76dc48",
  } satisfies Readonly<Record<WorkflowBlockRole, string>>,
  connectionColors: {
    data: "#159cff",
    control: "#12c881",
    feedback: "#ff4058",
  } satisfies Readonly<Record<WorkflowConnectionSemantics, string>>,
  phaseColors: {
    define: "#137dc2",
    verify: "#069b9b",
    manufacture: "#7650db",
  } satisfies Readonly<Record<WorkflowPhaseTone, string>>,
  invariants: {
    colorsEncodeRoleOrStatus: true,
    phaseNamesAreConfigurable: true,
    feedbackHasNonColorCue: true,
    engineeringCategoriesDoNotSelectRuntimeServices: true,
  },
} as const;

export const engineeringWorkflowCssVariables = {
  "--ewp-blue": engineeringWorkflowVisualContract.colors.input,
  "--ewp-purple": engineeringWorkflowVisualContract.colors.aiTask,
  "--ewp-cyan": engineeringWorkflowVisualContract.colors.mcpAction,
  "--ewp-green": engineeringWorkflowVisualContract.colors.artifact,
  "--ewp-amber": engineeringWorkflowVisualContract.colors.decision,
  "--ewp-red": engineeringWorkflowVisualContract.colors.feedback,
  "--ewp-lime": engineeringWorkflowVisualContract.colors.notification,
} as CSSProperties;
