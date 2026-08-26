import { chromium } from "playwright";

import { runHeadlessFourBlockChain } from "./headless-four-block-runner.mjs";
import {
  compileMountingPlateSpecToBrepArguments,
  mountingPlateExpectedFeatureIds,
  mountingPlateGenerationInstructions,
  mountingPlateInspectionAccepted,
  parseMountingPlateSpec,
} from "./mounting-plate-brep-fixture.mjs";

const apiBase = process.env.WRIGHT_API_BASE ?? "http://127.0.0.1:8000";

const request = {
  prompt:
    "Create a 100 x 60 x 8 mm editable mounting plate with four 8 mm through holes whose centers are 10 mm from the nearest X and Z edges.",
  attachments: [],
};

const generationPrompt = `You are Step 2 of a headless four-block engineering workflow. Do not call tools.

Step 1 design request:
${request.prompt}

${mountingPlateGenerationInstructions()}`;

async function jsonRequest(path, init = {}) {
  const response = await fetch(`${apiBase}${path}`, init);
  if (!response.ok) {
    throw new Error(
      `${path} failed (${response.status}): ${await response.text()}`,
    );
  }
  return response.json();
}

function postJson(path, body) {
  return jsonRequest(path, {
    method: "POST",
    headers: { "content-type": "application/json" },
    body: JSON.stringify(body),
  });
}

function tokensFromSse(text) {
  let output = "";
  for (const frame of text.split(/\r?\n\r?\n/)) {
    const event = /^event:\s*(.+)$/m.exec(frame)?.[1]?.trim();
    const data = /^data:\s*(.+)$/m.exec(frame)?.[1]?.trim();
    if (event === "error") {
      const payload = data ? JSON.parse(data) : {};
      throw new Error(payload.message ?? "AI stream failed");
    }
    if (event === "tool") {
      throw new Error("The no-tools AI boundary emitted a tool call");
    }
    if (event === "token" && data) {
      output += JSON.parse(data).text ?? "";
    }
  }
  return output;
}

function toolText(result) {
  const text = result?.content?.find(({ type }) => type === "text")?.text;
  if (typeof text !== "string") throw new Error("MCP returned no text result");
  return JSON.parse(text);
}

let sessionId = null;
let surfaceBrowser = null;
let panel = null;

try {
  const session = await postJson("/api/agent/sessions/new", {});
  sessionId = session.session_id;
  const models = await jsonRequest("/api/agent/models");
  const provider = models.current_provider;
  const model = models.current_model;
  if (!provider || !model) throw new Error("Wright has no current AI model");

  const run = await runHeadlessFourBlockChain({
    request,
    onStep(step) {
      process.stderr.write(`${step.block}: ${step.status}\n`);
    },
    async validateInput(value) {
      if (!value.prompt.trim()) throw new Error("A prompt is required");
      return {
        output: value,
        evidence: {
          promptCharacters: value.prompt.length,
          attachmentCount: value.attachments.length,
        },
      };
    },
    async generate() {
      const response = await fetch(`${apiBase}/api/agent/chat`, {
        method: "POST",
        headers: { "content-type": "application/json" },
        body: JSON.stringify({
          session_id: sessionId,
          message: generationPrompt,
          thinking_level: "low",
          provider,
          model,
          require_model_lock: true,
          tool_policy: "none",
        }),
      });
      if (!response.ok) {
        throw new Error(`AI request failed (${response.status})`);
      }
      const specification = parseMountingPlateSpec(
        tokensFromSse(await response.text()),
      );
      return {
        output: specification,
        evidence: {
          provider,
          model,
          toolPolicy: "none",
          outputContract: "mounting-plate-spec/0.1",
        },
      };
    },
    async invoke(specification) {
      const argumentsValue =
        compileMountingPlateSpecToBrepArguments(specification);
      panel = await postJson("/api/workspace/brep/panel", {
        session_id: sessionId,
      });
      const panelUrl = new URL(panel.control_url);
      if (!["127.0.0.1", "localhost"].includes(panelUrl.hostname)) {
        throw new Error("BREP returned a non-loopback control surface");
      }
      surfaceBrowser = await chromium.launch({ headless: true });
      const page = await surfaceBrowser.newPage();
      await page.goto(panel.control_url, {
        waitUntil: "domcontentloaded",
        timeout: 60_000,
      });

      for (let attempt = 0; attempt < 40; attempt += 1) {
        panel = await postJson("/api/workspace/brep/panel", {
          session_id: sessionId,
        });
        if (panel.connected) break;
        await new Promise((resolve) => setTimeout(resolve, 250));
      }
      if (!panel.connected) throw new Error("BREP surface did not connect");

      const result = await postJson("/api/workspace/brep/tool", {
        session_id: sessionId,
        tool_name: "brep.model.apply_history",
        arguments: argumentsValue,
      });
      const applied = toolText(result);
      if (applied.featureCount !== mountingPlateExpectedFeatureIds.length) {
        throw new Error(`BREP applied ${applied.featureCount ?? 0} features`);
      }
      return {
        output: applied,
        evidence: {
          serverId: panel.server_id,
          tool: "brep.model.apply_history",
          featureCount: applied.featureCount,
          mappedArguments: argumentsValue,
        },
      };
    },
    async evaluate(applied) {
      const observations = [];
      for (let attempt = 1; attempt <= 3; attempt += 1) {
        const result = await postJson("/api/workspace/brep/tool", {
          session_id: sessionId,
          tool_name: "brep.model.inspect",
          arguments: {},
        });
        const inspected = toolText(result);
        const history = JSON.parse(inspected.historyJson);
        observations.push({
          attempt,
          stateFeatureCount: inspected.state?.featureCount,
          historyFeatureCount: history.features?.length,
          ids: history.features?.map(({ inputParams }) => inputParams?.id),
          workflowSmokeId: history.metadata?.workflowSmokeId,
        });
      }
      const accepted = observations.every(mountingPlateInspectionAccepted);
      if (!accepted) {
        throw new Error(
          "BREP inspection did not consistently return the applied model; another control surface may be competing for commands",
        );
      }
      return {
        output: {
          accepted,
          meaning:
            "BREP accepted the history and returned consistent inspect evidence; engineering correctness was not evaluated.",
        },
        evidence: { appliedFeatureCount: applied.featureCount, observations },
      };
    },
  });

  process.stdout.write(`${JSON.stringify(run, null, 2)}\n`);
} finally {
  if (surfaceBrowser) await surfaceBrowser.close().catch(() => undefined);
  if (sessionId) {
    await fetch(`${apiBase}/api/agent/sessions/${sessionId}`, {
      method: "DELETE",
    }).catch(() => undefined);
  }
}
