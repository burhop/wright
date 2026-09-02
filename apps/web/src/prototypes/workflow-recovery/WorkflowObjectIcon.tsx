import type { CSSProperties, ReactNode } from "react";
import { AUTHORING_TEMPLATES } from "./authoring-objects";
import { recoveryAuthoringSectionKind, type RecoveryWorkflow } from "./model";

/** Presentation only: use the current canonical operation, not its title or ID. */
export function recoveryBlockIconKinds(workflow: RecoveryWorkflow): Readonly<Record<string, string>> {
  const ports = new Map(workflow.ports.map((port) => [port.id, port]));
  return Object.fromEntries(workflow.blocks.map((block) => {
    const inputs = block.inputPortIds.map((id) => ports.get(id)?.typeId ?? "");
    const outputs = block.outputPortIds.map((id) => ports.get(id)?.typeId ?? "");
    const types = [...inputs, ...outputs];
    const includes = (values: readonly string[], term: string) => values.some((value) => value.includes(term));
    let kind: string;
    if (recoveryAuthoringSectionKind(block) === "input") {
      kind = includes(outputs, "image") ? "image"
        : block.configuration.input_mode === "workspace-file" || includes(outputs, "file.workspace") ? "file"
          : includes(outputs, "context") ? "context" : "text";
    } else {
      const template = AUTHORING_TEMPLATES.find((item) => item.id === block.configuration.authoring_template && item.executionKind === block.executionKind);
      if (template && template.group !== "input") {
        const groupIcons = { document: "llm-document", tool: "mcp-tools", check3d: "3d-check", drawing: "drawing", fdm: "fdm", more: block.executionKind === "human" ? "review" : "more" };
        kind = groupIcons[template.group];
      } else if (block.executionKind === "human") kind = "review";
      else if (block.kind === "approval") kind = block.executionKind === "ai_capable" ? "llm-document" : "review";
      else if (includes(outputs, "file.step") || includes(outputs, "package.")) kind = "output";
      else if (includes(types, "drawing")) kind = "drawing";
      else if (includes(outputs, "toolpath")) kind = "fdm";
      else if (includes(inputs, "geometry") && includes(outputs, "report")) kind = "3d-check";
      else if (includes(outputs, "geometry")) kind = "model";
      else kind = block.executionKind === "ai_capable" ? "llm-document" : "mcp-tools";
    }
    return [block.id, kind];
  }));
}

/** Decorative, code-native symbols shared by the object rail and the diagram. */
export function WorkflowObjectIcon({ kind, className = "", style }: { readonly kind: string; readonly className?: string; readonly style?: CSSProperties }) {
  const paths: Record<string, ReactNode> = {
    input: <><path d="M14 4h6v16h-6M3 12h12m-4-4 4 4-4 4" /></>,
    text: <><path d="M4 5h16M12 5v15M8 20h8M4 5v3m16-3v3" /></>,
    image: <><rect x="3" y="3" width="18" height="18" rx="2" /><circle cx="8" cy="8" r="1.5" /><path d="m4 18 5-6 4 3 3-4 5 7" /></>,
    context: <><path d="M5 3h10l4 4v14H5zM15 3v5h4M8 12h8m-8 4h8" /></>,
    "llm-document": <><path d="M4 3h10l4 4v5M14 3v5h4M4 3v18h9M7 12h5m-5 4h4M18 14l1.3 2.7L22 18l-2.7 1.3L18 22l-1.3-2.7L14 18l2.7-1.3z" /></>,
    "mcp-tools": <><path d="m4 4 5 5m6 6 5 5M3 3l3 1-2 2zM21 3l-3 3-3-3a6 6 0 0 0-6 8l-6 6a2.8 2.8 0 0 0 4 4l6-6a6 6 0 0 0 8-6z" /></>,
    model: <><path d="m12 2 9 5v10l-9 5-9-5V7zM3 7l9 5 9-5M12 12v10M7.5 4.5l9 5" /></>,
    "3d-check": <><path d="m10 2 8 4.5v5M10 2 2 6.5v9L10 20M2 6.5 10 11l8-4.5M10 11v9M18 12l4 2v4l-4 4-4-4v-4z" /><path d="m16 17 1.5 1.5L20 16" /></>,
    drawing: <><rect x="3" y="3" width="18" height="18" rx="1" /><path d="M6 16 10 8l6 6M6 18h12M7 6h10m-7 2v10M17 6v10" /></>,
    fdm: <><path d="m12 2 9 5-9 5-9-5zM3 12l9 5 9-5M3 17l9 5 9-5" /></>,
    review: <><path d="M2 12s3.5-7 10-7 10 7 10 7-3.5 7-10 7S2 12 2 12z" /><circle cx="12" cy="12" r="3" /></>,
    output: <><path d="M12 3v12m-4-4 4 4 4-4M4 16v5h16v-5" /></>,
    more: <>{[5, 12, 19].flatMap((x) => [5, 12, 19].map((y) => <circle key={`${x}-${y}`} cx={x} cy={y} r="1" fill="currentColor" />))}</>,
  };
  const aliases: Record<string, string> = { file: "context", llm: "llm-document", document: "llm-document", tool: "mcp-tools", tools: "mcp-tools", mcp: "mcp-tools", check3d: "3d-check", check: "3d-check", "3d": "3d-check", inputs: "input" };
  const resolvedKind = aliases[kind] ?? kind;
  return <svg className={`recovery-object-icon ${className}`} data-icon-kind={paths[resolvedKind] ? resolvedKind : "context"} style={style} width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round" aria-hidden="true" focusable="false">{paths[resolvedKind] ?? paths.context}</svg>;
}
