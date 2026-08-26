import { agentService } from "../../../services/agent-service";
import { hostAdapter } from "../../../services/host-adapter";
import {
  API_BASE,
  workspaceService,
  type BrepPanelSession,
} from "../../../services/workspace-service";

import type {
  DiagnosticExactMcpBinding,
  DiagnosticMcpRunSession,
  DiagnosticMcpRuntimeAdapter,
} from "./diagnostic-four-block-executor";
import {
  compileMountingPlateSpecToBrepArguments,
  mountingPlateExpectedFeatureIds,
  mountingPlateGenerationInstructions,
  mountingPlateInspectionAccepted,
  parseMountingPlateSpec,
} from "../evaluation/mounting-plate-brep-fixture.mjs";

const EXPECTED_TOOL = "brep.model.apply_history";
const INSPECT_TOOL = "brep.model.inspect";

interface RetainedBrepOutput {
  frame: HTMLIFrameElement;
  sessionId: string;
  definition: unknown;
}

const retainedBrepOutputs = new Map<string, RetainedBrepOutput>();

function hideBrepOutput(frame: HTMLIFrameElement): void {
  frame.setAttribute("aria-hidden", "true");
  frame.style.width = "1px";
  frame.style.height = "1px";
  frame.style.opacity = "0";
  frame.style.pointerEvents = "none";
  frame.style.inset = "0 auto auto 0";
  frame.style.zIndex = "-1";
}

interface BrepToolResponse {
  content?: Array<{ type?: string; text?: string }>;
}

function parseToolText(result: BrepToolResponse): Record<string, unknown> {
  const text = result.content?.find(({ type }) => type === "text")?.text;
  if (typeof text !== "string") throw new Error("MCP returned no text result.");
  const value: unknown = JSON.parse(text);
  if (!value || typeof value !== "object" || Array.isArray(value)) {
    throw new Error("MCP returned an invalid result object.");
  }
  return value as Record<string, unknown>;
}

function asRecord(value: unknown, message: string): Record<string, unknown> {
  if (!value || typeof value !== "object" || Array.isArray(value)) {
    throw new Error(message);
  }
  return value as Record<string, unknown>;
}

async function callBrepTool(
  sessionId: string,
  toolName: string,
  argumentsValue: unknown,
): Promise<BrepToolResponse> {
  const response = await hostAdapter.fetch(
    `${API_BASE}/api/workspace/brep/tool`,
    {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        session_id: sessionId,
        tool_name: toolName,
        arguments: argumentsValue,
      }),
    },
  );
  if (!response.ok) {
    const body = (await response.json().catch(() => ({}))) as {
      detail?: unknown;
    };
    throw new Error(
      typeof body.detail === "string"
        ? body.detail
        : `MCP call failed (${response.status}).`,
    );
  }
  return response.json();
}

function mountControlSurface(controlUrl: string): Promise<HTMLIFrameElement> {
  const url = new URL(controlUrl);
  if (url.hostname !== "127.0.0.1" && url.hostname !== "localhost") {
    throw new Error("BREP returned a non-loopback control surface.");
  }
  const frame = document.createElement("iframe");
  frame.title = "BREP diagnostic control surface";
  frame.setAttribute("aria-hidden", "true");
  frame.style.position = "fixed";
  frame.style.width = "1px";
  frame.style.height = "1px";
  frame.style.opacity = "0";
  frame.style.pointerEvents = "none";
  frame.style.inset = "0 auto auto 0";
  frame.style.zIndex = "-1";
  frame.src = controlUrl;
  document.body.append(frame);
  return new Promise((resolve, reject) => {
    const timeout = window.setTimeout(() => {
      frame.remove();
      reject(new Error("BREP control surface did not load within 60 seconds."));
    }, 60_000);
    frame.addEventListener(
      "load",
      () => {
        window.clearTimeout(timeout);
        resolve(frame);
      },
      { once: true },
    );
    frame.addEventListener(
      "error",
      () => {
        window.clearTimeout(timeout);
        frame.remove();
        reject(new Error("BREP control surface failed to load."));
      },
      { once: true },
    );
  });
}

function createBrepRunSession(
  binding: DiagnosticExactMcpBinding,
): DiagnosticMcpRunSession {
  if (binding.tool.name !== EXPECTED_TOOL) {
    throw new Error(
      `This bounded diagnostic adapter supports ${EXPECTED_TOOL}, not ${binding.tool.name}.`,
    );
  }

  let sessionId: string | null = null;
  let panel: BrepPanelSession | null = null;
  let controlFrame: HTMLIFrameElement | null = null;
  let retainedOutputId: string | null = null;
  let modelDefinition: unknown = null;

  async function ensureControlSurface(): Promise<string> {
    if (!sessionId) {
      sessionId = (await agentService.createSession()).sessionId;
    }
    if (!controlFrame) {
      panel = await workspaceService.openBrepPanel(sessionId);
      controlFrame = await mountControlSurface(panel.control_url);
      for (let attempt = 0; attempt < 40; attempt += 1) {
        panel = await workspaceService.openBrepPanel(sessionId);
        if (panel.connected) return sessionId;
        await new Promise((resolve) => window.setTimeout(resolve, 250));
      }
      throw new Error(
        "BREP control surface did not connect to its MCP server.",
      );
    }
    return sessionId;
  }

  return {
    responseInstructions() {
      return mountingPlateGenerationInstructions();
    },
    parseGeneratedOutput(text) {
      return parseMountingPlateSpec(text);
    },
    async invoke(argumentsValue) {
      const activeSessionId = await ensureControlSurface();
      const toolArguments = compileMountingPlateSpecToBrepArguments(
        parseMountingPlateSpec(JSON.stringify(argumentsValue)),
      );
      modelDefinition = toolArguments;
      const applied = parseToolText(
        await callBrepTool(activeSessionId, EXPECTED_TOOL, toolArguments),
      );
      if (applied.featureCount !== mountingPlateExpectedFeatureIds.length) {
        throw new Error(
          `BREP reported ${String(applied.featureCount ?? 0)} applied features; expected ${mountingPlateExpectedFeatureIds.length}.`,
        );
      }
      return {
        output: applied,
        evidence: {
          serverId: panel?.server_id,
          tool: EXPECTED_TOOL,
          featureCount: applied.featureCount,
          mappedArguments: toolArguments,
        },
      };
    },
    async evaluate(toolResult) {
      const activeSessionId = await ensureControlSurface();
      const observations: Array<{
        attempt: number;
        stateFeatureCount: unknown;
        historyFeatureCount: unknown;
        ids: unknown;
        workflowSmokeId: unknown;
      }> = [];
      for (let attempt = 1; attempt <= 3; attempt += 1) {
        const inspected = parseToolText(
          await callBrepTool(activeSessionId, INSPECT_TOOL, {}),
        );
        const historyJson = inspected.historyJson;
        if (typeof historyJson !== "string") {
          throw new Error("BREP inspection returned no history JSON.");
        }
        const history = asRecord(
          JSON.parse(historyJson),
          "BREP history is invalid.",
        );
        const features = Array.isArray(history.features)
          ? history.features
          : [];
        const state = asRecord(
          inspected.state,
          "BREP inspection returned no state.",
        );
        const metadata = asRecord(
          history.metadata,
          "BREP history has no metadata.",
        );
        observations.push({
          attempt,
          stateFeatureCount: state.featureCount,
          historyFeatureCount: features.length,
          ids: features.map(
            (feature) =>
              asRecord(
                asRecord(feature, "BREP returned an invalid feature.")
                  .inputParams,
                "BREP returned a feature without inputs.",
              ).id,
          ),
          workflowSmokeId: metadata.workflowSmokeId,
        });
      }
      const accepted = observations.every(mountingPlateInspectionAccepted);
      if (!accepted) {
        throw new Error(
          "BREP inspection was inconsistent. Another BREP control surface may be competing for commands; close other BREP views, reset, and run again.",
        );
      }
      retainedOutputId = `brep-model-${activeSessionId}`;
      return {
        output: {
          accepted: true,
          meaning:
            "BREP accepted the history and returned three consistent inspections. Engineering correctness was not evaluated.",
          outputs: [
            {
              outputId: retainedOutputId,
              title: "Four-hole mounting plate",
              kind: "model",
              description:
                "Live BREP model created from one plate and four through-hole features.",
              format: "BREP parametric history",
              durability: "session",
              producer: {
                block: "mcp",
                serverId: panel?.server_id,
                toolName: EXPECTED_TOOL,
              },
              actions: [
                {
                  actionId: "view",
                  kind: "view",
                  label: "View in BREP",
                  available: true,
                },
                {
                  actionId: "download-definition",
                  kind: "download",
                  label: "Download model definition",
                  available: true,
                },
              ],
            },
          ],
        },
        evidence: { toolResult, observations },
      };
    },
    async dispose() {
      if (retainedOutputId && controlFrame && sessionId && modelDefinition) {
        hideBrepOutput(controlFrame);
        retainedBrepOutputs.set(retainedOutputId, {
          frame: controlFrame,
          sessionId,
          definition: modelDefinition,
        });
        controlFrame = null;
        sessionId = null;
        return;
      }
      controlFrame?.remove();
      controlFrame = null;
      if (sessionId) {
        const disposableSessionId = sessionId;
        sessionId = null;
        await agentService
          .deleteSession(disposableSessionId)
          .catch(() => undefined);
      }
    },
  };
}

/**
 * Test-fixture adapter only. The workflow executor remains MCP-generic; this
 * adapter documents the host/application contract needed by the selected BREP
 * test and may be discarded after the prototype.
 */
export const brepDiagnosticMcpRuntimeAdapter: DiagnosticMcpRuntimeAdapter = {
  supports(binding) {
    return binding.tool.name === EXPECTED_TOOL;
  },
  createRun: createBrepRunSession,
  async performOutputAction(output, action) {
    const retained = retainedBrepOutputs.get(output.outputId);
    if (!retained) {
      throw new Error(
        "This session output is no longer available. Run the workflow again to recreate it.",
      );
    }
    if (action.actionId === "view") {
      const { frame } = retained;
      frame.removeAttribute("aria-hidden");
      frame.title = output.title;
      frame.style.inset = "98px 36px 36px";
      frame.style.width = "calc(100vw - 72px)";
      frame.style.height = "calc(100vh - 134px)";
      frame.style.opacity = "1";
      frame.style.pointerEvents = "auto";
      frame.style.zIndex = "101";
      return {
        kind: "embedded",
        close() {
          hideBrepOutput(frame);
        },
      };
    }
    if (action.actionId === "download-definition") {
      const blob = new Blob([JSON.stringify(retained.definition, null, 2)], {
        type: "application/json",
      });
      const url = URL.createObjectURL(blob);
      const anchor = document.createElement("a");
      anchor.href = url;
      anchor.download = "four-hole-mounting-plate.brep-history.json";
      anchor.click();
      URL.revokeObjectURL(url);
      return {
        kind: "completed",
        message: "The BREP model definition download started.",
      };
    }
    throw new Error(`Unsupported output action: ${action.actionId}`);
  },
  async releaseOutputs(outputs) {
    await Promise.all(
      outputs.map(async ({ outputId }) => {
        const retained = retainedBrepOutputs.get(outputId);
        if (!retained) return;
        retainedBrepOutputs.delete(outputId);
        retained.frame.remove();
        await agentService
          .deleteSession(retained.sessionId)
          .catch(() => undefined);
      }),
    );
  },
};
