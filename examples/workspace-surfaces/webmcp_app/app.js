import { WrightSurfaceSdk } from "./wright-surface-sdk.js";

const status = document.querySelector("#status");
const line = document.querySelector("#line");
const controller = new AbortController();
const sdk = new WrightSurfaceSdk();

function setGraph({ values }) {
  if (!Array.isArray(values) || values.length < 2 || values.length > 50 || values.some((value) => !Number.isFinite(value))) {
    throw new TypeError("values must contain 2 to 50 finite numbers");
  }
  const low = Math.min(...values);
  const span = Math.max(1, Math.max(...values) - low);
  line.setAttribute("points", values.map((value, index) => `${20 + index * 600 / (values.length - 1)},${320 - (value - low) * 280 / span}`).join(" "));
  status.textContent = `Rendered ${values.length} values.`;
  return { rendered: values.length, minimum: low, maximum: Math.max(...values) };
}

const tool = {
  name: "set_graph",
  description: "Replace the values in this page's visible line graph.",
  inputSchema: {
    type: "object",
    properties: { values: { type: "array", minItems: 2, maxItems: 50, items: { type: "number" } } },
    required: ["values"], additionalProperties: false,
  },
  handler: setGraph,
  signal: controller.signal,
};

const registration = await sdk.registerTool(tool);
status.textContent = "Wright-scoped set_graph is ready.";

// Native WebMCP remains optional and non-authoritative. Never assign or polyfill this namespace.
const nativeRegister = document.modelContext?.registerTool;
if (typeof nativeRegister === "function" && document.permissionsPolicy?.allowsFeature?.("tools") !== false) {
  try {
    await nativeRegister.call(document.modelContext, {
      name: tool.name, description: tool.description, inputSchema: tool.inputSchema,
      execute: (argumentsValue) => setGraph(argumentsValue),
    });
    status.textContent += " Native WebMCP was also detected.";
  } catch {
    status.textContent += " Native registration was rejected; the Wright route remains active.";
  }
}

document.querySelector("#unregister").addEventListener("click", async () => {
  controller.abort();
  await registration.dispose();
  status.textContent = "Tool unregistered.";
});
