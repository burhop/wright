import type { RecoveryBlock, RecoveryWorkflow } from "./model";
import type { RecoveryCommand } from "./command-system";
import { stableKey } from "./recovery-authoring";

export function TaskOutputFiles({
  block,
  workflow,
  readOnly,
  onApply,
}: {
  block: RecoveryBlock;
  workflow: RecoveryWorkflow;
  readOnly: boolean;
  onApply: (commands: RecoveryCommand[]) => boolean;
}) {
  const ports = workflow.ports.filter(
    (port) =>
      block.outputPortIds.includes(port.id) &&
      port.typeId === "type.file.workspace",
  );
  if (!ports.length) return null;
  let mapping: Record<string, string>;
  try {
    const value = JSON.parse(
      String(block.configuration.expected_file_ports ?? "{}"),
    );
    if (
      !value ||
      typeof value !== "object" ||
      Array.isArray(value) ||
      Object.values(value).some((path) => typeof path !== "string")
    )
      throw new Error("Invalid mapping");
    mapping = value;
  } catch {
    return (
      <p role="alert">
        Output filenames could not be read. Correct expected_file_ports in
        Source before editing them here.
      </p>
    );
  }
  const expected = String(block.configuration.expected_files ?? "")
    .split("\n")
    .filter(Boolean);
  const change = (key: string, path: string) => {
    if (readOnly) return;
    const next = { ...mapping };
    if (path) next[key] = path;
    else delete next[key];
    const retained = expected.filter(
      (file) => file !== mapping[key] || Object.values(next).includes(file),
    );
    onApply([
      {
        kind: "set_block_configuration",
        blockId: block.id,
        key: "expected_file_ports",
        value: JSON.stringify(next),
      },
      {
        kind: "set_block_configuration",
        blockId: block.id,
        key: "expected_files",
        value: [...new Set([...retained, ...Object.values(next)])].join("\n"),
      },
    ]);
  };
  const updateAdditional = (raw: string, normalize: boolean) => {
    if (readOnly) return;
    const extras = normalize
      ? raw
          .split("\n")
          .map((path) => path.trim())
          .filter(Boolean)
      : [raw];
    const files = [...Object.values(mapping), ...extras];
    const value = (normalize ? [...new Set(files)] : files).join("\n");
    if (value === block.configuration.expected_files) return;
    onApply([
      {
        kind: "set_block_configuration",
        blockId: block.id,
        key: "expected_files",
        value,
      },
    ]);
  };
  return (
    <section className="recovery-task-output-files" aria-label="Output files">
      <h3>Output files</h3>
      <p>
        Files this step must produce. Its tool arguments or instructions must
        write to these workspace paths.
      </p>
      {ports.map((port) => {
        const key = stableKey(port.id);
        const value = mapping[key] ?? "";
        const message = !value.trim()
          ? "A filename is needed before this step can run."
          : value.length > 256 ||
              /[\\:%]/.test(value) ||
              value
                .split("/")
                .some(
                  (part) => !part || part.startsWith(".") || /[ .]$/.test(part),
                )
            ? "Use a path inside this workspace, with / between folders."
            : !expected.includes(value)
              ? "This filename is not listed as required. Edit it here to include it."
              : "";
        return (
          <label key={port.id}>
            {port.name}
            <input
              value={value}
              aria-label={port.name}
              readOnly={readOnly}
              aria-invalid={Boolean(message)}
              placeholder="Folder and filename inside this workspace"
              onChange={(event) => change(key, event.target.value)}
            />
            {message && <small>{message}</small>}
          </label>
        );
      })}
      <details>
        <summary>Additional required files</summary>
        <label>
          Other files to check
          <textarea
            aria-label="Other files to check"
            rows={2}
            readOnly={readOnly}
            value={String(block.configuration.expected_files ?? "")
              .split("\n")
              .filter((path) => !Object.values(mapping).includes(path))
              .join("\n")}
            onChange={(event) => updateAdditional(event.target.value, false)}
            onBlur={(event) => updateAdditional(event.target.value, true)}
          />
        </label>
      </details>
      <small>
        These are tool-created files, separate from the AI response. Existing
        run-specific paths are preserved.
      </small>
    </section>
  );
}
