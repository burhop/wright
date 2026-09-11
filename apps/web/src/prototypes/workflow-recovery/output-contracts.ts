import {
  findBlock,
  findPort,
  type RecoveryBlock,
  type RecoveryDiagnostic,
  type RecoveryWorkflow,
} from "./model";

interface ExportContract {
  id?: string;
  port?: string;
  format?: string;
  path?: string;
  name?: string;
}
const key = (id: string) =>
  id
    .slice(id.indexOf(".") + 1)
    .replace(/[^a-zA-Z0-9]+/g, "_")
    .toLowerCase();
export function exportFormatLabel(format: string): string {
  return (
    (
      {
        screenshot_jpeg: "JPEG preview",
        screenshot_png: "PNG preview",
        flat_dxf: "Flat pattern (DXF)",
        flat_parasolid: "Flat pattern (Parasolid)",
        parasolid: "Parasolid",
      } as Record<string, string>
    )[format.toLowerCase()] ?? format.toUpperCase().replaceAll("_", " ")
  );
}

export function exportPortId(
  block: RecoveryBlock,
  workflow: RecoveryWorkflow,
  output: { id?: string; port?: string },
  family: "cad" | "application",
) {
  const existing = workflow.ports.find(
    (port) =>
      port.ownerBlockId === block.id &&
      port.direction === "output" &&
      (key(port.id) === output.port || port.id === output.port),
  );
  return (
    existing?.id ??
    `port.${block.id.slice(6)}-${family}-${output.id ?? output.port ?? "export"}`
  );
}

export function configuredOutputs(
  block: RecoveryBlock,
  workflow?: RecoveryWorkflow,
) {
  const contracts = new Map<string, { format: string; name: string }>();
  for (const setting of ["cad", "application_resource"] as const) {
    let value: { kind?: string; exports?: ExportContract[] };
    try {
      value = JSON.parse(String(block.configuration[setting]));
    } catch {
      continue;
    }
    if (!value || typeof value !== "object") continue;
    const family = setting === "cad" ? "cad" : "application";
    const modelId =
      workflow?.ports.find(
        (port) =>
          port.ownerBlockId === block.id &&
          port.direction === "output" &&
          port.typeId === "type.geometry.brep",
      )?.id ??
      `port.${block.id.slice(6)}-${family}-${setting === "cad" ? "model" : "result"}`;
    contracts.set(key(modelId), {
      format: `resource:${block.configuration.mcp_server}:${value.kind ?? "cad_model"}`,
      name:
        setting === "cad" || value.kind === "cad_model"
          ? "CAD model"
          : "Application result",
    });
    for (const output of Array.isArray(value.exports) ? value.exports : []) {
      if (!output || typeof output.format !== "string") continue;
      const port =
        output.port ??
        (output.id
          ? key(`port.${block.id.slice(6)}-${family}-${output.id}`)
          : "");
      if (port)
        contracts.set(port, {
          format: output.format.toLowerCase(),
          name: output.format
            ? exportFormatLabel(output.format)
            : "Unconfigured export",
        });
    }
  }
  return contracts;
}

export function outputConsumers(
  workflow: RecoveryWorkflow,
  portId: string,
): string[] {
  return [
    ...new Set(
      workflow.relationships
        .filter((edge) => edge.kind === "data" && edge.sourceId === portId)
        .map(
          (edge) =>
            findBlock(
              workflow,
              findPort(workflow, edge.targetId)?.ownerBlockId ?? null,
            )?.title,
        )
        .filter((title): title is string => Boolean(title)),
    ),
  ];
}

/** Stable connected outputs are promises, even when both formats are files.
 * Explicitly disconnect before repurposing an output; adding one is safe.
 * This also covers source edits and reviewed AI command batches. */
export function validateOutputChanges(
  before: RecoveryWorkflow,
  after: RecoveryWorkflow,
): RecoveryDiagnostic[] {
  const diagnostics: RecoveryDiagnostic[] = [];
  for (const producer of before.blocks) {
    const next = findBlock(after, producer.id);
    if (!next) continue; // Deleting a whole block already reviews its connections.
    const previous = configuredOutputs(producer, before),
      updated = configuredOutputs(next, after);
    for (const portId of producer.outputPortIds) {
      const contract = previous.get(key(portId));
      if (!contract || contract.format === updated.get(key(portId))?.format)
        continue;
      const consumers = before.relationships
        .filter((edge) => edge.kind === "data" && edge.sourceId === portId)
        .map((edge) => findPort(before, edge.targetId)?.ownerBlockId)
        .filter((id): id is string => Boolean(id && findBlock(after, id)));
      if (!consumers.length) continue;
      const names = [
        ...new Set(consumers.map((id) => findBlock(after, id)!.title)),
      ].join(", ");
      diagnostics.push({
        code: "WFR-CONNECTED-OUTPUT-CHANGE",
        semanticId: producer.id,
        line: null,
        explanation: `${producer.title}: ${contract.name} is used by ${names}. This change would replace or remove their connected output.`,
        correction: `Keep ${contract.name} and add another export, or disconnect the affected inputs first, then change the output and reconnect compatible blocks. No change was applied.`,
      });
    }
  }
  return diagnostics;
}

const extensions: Record<string, string> = {
  step: "step",
  stp: "stp",
  flat_dxf: "dxf",
  parasolid: "x_t",
  flat_parasolid: "x_t",
  parasolid_text: "x_t",
  parasolid_binary: "x_b",
  iges: "igs",
  screenshot_jpeg: "jpg",
  screenshot_png: "png",
};
export function exportFilename(path: string, format: string): string {
  const extension = extensions[format.toLowerCase()] ?? format.toLowerCase();
  return (
    (path || "export").replace(/\.[^/.\\]+$/, "") +
    (extension ? `.${extension}` : "")
  );
}
