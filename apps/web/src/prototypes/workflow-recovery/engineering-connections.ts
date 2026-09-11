import { useEffect, useState } from "react";
import { findBlock, findPort, type RecoveryWorkflow } from "./model";
import {
  applicationPortId,
  applicationImportRepresentation,
  type ApplicationOptions,
  type ApplicationCapabilities,
} from "./ApplicationTaskOptions";
import { cadPortId, type CadOptions } from "./CadTaskOptions";
import { readJson } from "./mcp-settings";

export function engineeringConnectionIssue(
  workflow: RecoveryWorkflow,
  sourceId: string,
  targetId: string,
  caps: Record<string, ApplicationCapabilities>,
): string | null | undefined {
  const source = findPort(workflow, sourceId),
    target = findPort(workflow, targetId);
  if (!source || !target) return "Select an output and an input.";
  const producer = findBlock(workflow, source.ownerBlockId)!,
    consumer = findBlock(workflow, target.ownerBlockId)!;
  const app = readJson<ApplicationOptions | null>(
    consumer.configuration.application_resource,
    null,
  );
  const cad = readJson<CadOptions | null>(consumer.configuration.cad, null);
  if (cad && targetId === cadPortId(consumer, "input")) {
    if (source.cardinality === "many")
      return "This input needs one CAD model. Select an individual result.";
    if (
      producer.configuration.cad &&
      producer.configuration.mcp_server === consumer.configuration.mcp_server &&
      sourceId === cadPortId(producer, "model")
    )
      return null;
    return "This CAD input needs an open model from the same application. Use a supported exported workspace file when transferring between CAD applications.";
  }
  if (!app || targetId !== applicationPortId(consumer, "input"))
    return undefined;
  if (source.cardinality === "many")
    return "This input needs one result. Select a named export or individual resource.";
  const producingApp = readJson<ApplicationOptions | null>(
    producer.configuration.application_resource,
    null,
  );
  if (
    producingApp?.kind === app.kind &&
    producer.configuration.mcp_server === consumer.configuration.mcp_server &&
    sourceId === applicationPortId(producer, "result")
  )
    return null;
  const capability = caps[String(consumer.configuration.mcp_server ?? "")];
  if (!capability)
    return "Checking the receiving application's supported formats. Try again when its options load.";
  const representation = applicationImportRepresentation(producer, source);
  if (
    representation &&
    capability.import_formats?.includes(representation.format) &&
    capability.import_kinds?.includes(representation.kind)
  )
    return null;
  return capability.import_formats?.length
    ? `This application needs ${capability.import_formats.join(", ")}. Select the receiving block and use a matching export from the producer.`
    : "This server has not declared a compatible file import. Choose a resource from the same application.";
}

export function useEngineeringConnectionCapabilities(
  workflow: RecoveryWorkflow,
  sessionId?: string,
) {
  const [caps, setCaps] = useState<Record<string, ApplicationCapabilities>>({});
  const servers = [
    ...new Set(
      workflow.blocks
        .filter((b) => b.configuration.application_resource)
        .map((b) => String(b.configuration.mcp_server ?? ""))
        .filter(Boolean),
    ),
  ]
    .sort()
    .join("|");
  useEffect(() => {
    let current = true;
    setCaps({});
    if (!sessionId) return;
    for (const server of servers.split("|").filter(Boolean)) {
      const query = new URLSearchParams({
        session_id: sessionId,
        server_id: server,
      });
      void fetch(`/api/workspace/workflow-sources/application?${query}`)
        .then(async (response) => (response.ok ? response.json() : null))
        .then((value) => {
          if (current && value)
            setCaps((previous) => ({ ...previous, [server]: value }));
        })
        .catch(() => undefined);
    }
    return () => {
      current = false;
    };
  }, [sessionId, servers]);
  return caps;
}
