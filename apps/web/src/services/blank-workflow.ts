/** Create an empty engineering definition. Examples are an explicit choice. */
export function blankWorkflowSource(title = "Untitled workflow"): string {
  const identity = `authored_${crypto.randomUUID().replaceAll("-", "_")}`;
  return `workflow ${identity}\n  name: ${JSON.stringify(title)}\n  purpose: "Define this workflow's steps and outputs."\n  discipline: "engineering"\n  reviewed_ai_suggestions: true\nend\n`;
}
