import { describe, expect, it } from "vitest";

import { cloneWorkflow, initialWorkflow } from "./model";
import { parseRecoveryAuthoringSource } from "./recovery-authoring";

const ids = [
  "printed-replacement-part",
  "raspberry-pi-enclosure",
  "sheet-metal-supplier-handoff",
  "lightweight-equipment-bracket",
  "sensor-interface-pcb",
  "parametric-drill-jig",
  "robot-tracking-diagnosis",
  "heat-spreader-sizing",
  "sensor-fan-harness",
  "water-heater-sizing",
];
const sources = import.meta.glob(
  "../../../../../packages/workspace_service/src/workspace_service/engineering_workflow_templates/templates/*.workflow.wflow",
  { eager: true, query: "?raw", import: "default" },
) as Record<string, string>;

describe("packaged engineering workflow sources", () => {
  it.each(ids)("%s opens in the canonical workflow editor", (id) => {
    const [, source] =
      Object.entries(sources).find(([path]) =>
        path.endsWith(`/${id}.workflow.wflow`),
      ) ?? [];
    expect(source, `missing packaged source for ${id}`).toBeTruthy();
    if (!source) throw new Error(`missing packaged source for ${id}`);
    const instanceSource = source.replaceAll("__instance__", "templatecatalog");
    const base = cloneWorkflow(initialWorkflow);
    base.workflowId = "workflow.templatecatalog";
    base.revision = 1;
    base.parentRevision = null;
    const parsed = parseRecoveryAuthoringSource(instanceSource, base);
    expect(
      parsed.diagnostics,
      JSON.stringify(parsed.diagnostics, null, 2),
    ).toEqual([]);
    expect(parsed.ok).toBe(true);
    expect(parsed.workflow?.metadata.title).toBeTruthy();
  });
});
