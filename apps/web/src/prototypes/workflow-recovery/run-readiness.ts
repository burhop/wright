import type { RecoveryDiagnostic, RecoveryWorkflow } from "./model";

// This is a run constraint, not a source/command constraint: disconnected
// drafts must remain editable and saveable while an engineer connects them.
export function disconnectedProcessDiagnostic(workflow: RecoveryWorkflow): RecoveryDiagnostic | null {
  const neighbors = new Map(workflow.blocks.map(block => [block.id, new Set<string>()]));
  const owners = new Map(workflow.ports.map(port => [port.id, port.ownerBlockId]));
  for (const edge of workflow.relationships) {
    const from = owners.get(edge.sourceId) ?? edge.sourceId;
    const to = owners.get(edge.targetId) ?? edge.targetId;
    if (neighbors.has(from) && neighbors.has(to)) {
      neighbors.get(from)!.add(to);
      neighbors.get(to)!.add(from);
    }
  }
  const visited = new Set<string>();
  const groups: string[][] = [];
  for (const block of workflow.blocks) {
    if (visited.has(block.id)) continue;
    const group: string[] = [];
    const pending = [block.id];
    visited.add(block.id);
    while (pending.length) {
      const id = pending.pop()!;
      group.push(id);
      for (const neighbor of neighbors.get(id)!) {
        if (!visited.has(neighbor)) { visited.add(neighbor); pending.push(neighbor); }
      }
    }
    groups.push(group);
  }
  if (groups.length <= 1) return null;
  const names = new Map(workflow.blocks.map(block => [block.id, block.title]));
  const examples = groups.slice(0, 4).map(group => `“${names.get(group[0]!)}” (${group.length} ${group.length === 1 ? "block" : "blocks"})`).join("; ");
  return {
    code: "WFR-DISCONNECTED-PROCESS", semanticId: null, line: null,
    explanation: `This workflow contains ${groups.length} disconnected groups of blocks. Run is blocked; one workflow must describe one connected process.`,
    correction: `Connect the groups into one process, or move each independent process to its own workflow. Groups: ${examples}${groups.length > 4 ? "; …" : ""}.`,
  };
}
