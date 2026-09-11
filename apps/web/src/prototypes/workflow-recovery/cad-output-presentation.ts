import type { RecoveryWorkflow } from "./model";
import { sourceKey } from "./prompt-settings";

/** Read-time compatibility projection. Never changes source, port IDs or edges. */
export function cadOutputPresentation(workflow: RecoveryWorkflow) {
  const hidden = new Set<string>();
  const labels: Record<string, string> = {};
  const groups: Record<string, string> = {};
  for (const block of workflow.blocks) {
    if (!block.configuration.cad && !block.configuration.application_resource)
      continue;
    let config: {
      native_port?: string;
      native_path?: string;
      exports?: Array<{
        port?: string;
        id?: string;
        format: string;
        path?: string;
        name?: string;
      }>;
    };
    try {
      config = JSON.parse(
        String(
          block.configuration.cad || block.configuration.application_resource,
        ),
      );
    } catch {
      continue;
    }
    for (const port of workflow.ports.filter(
      (p) => p.ownerBlockId === block.id && p.direction === "output",
    )) {
      if (sourceKey(port.id) === config.native_port) {
        // Retain a visible, precisely addressed representation for old edges.
        if (!workflow.relationships.some((e) => e.sourceId === port.id))
          hidden.add(port.id);
        else {
          labels[port.id] = "Saved model file";
          groups[port.id] = "Model file";
        }
      }
      const ex = config.exports?.find((e) => e.port === sourceKey(port.id));
      if (ex) {
        labels[port.id] =
          ex.path || ex.name || ex.format.toUpperCase() || "Choose export";
        groups[port.id] = "Exports";
      }
    }
  }
  return { hidden, labels, groups };
}
