import {
  exportFormatLabel,
  outputConsumers,
  exportFilename,
  exportPortId,
  configuredOutputs,
} from "./output-contracts";
import { useEffect, useState } from "react";
import type { RecoveryCommand } from "./command-system";
import {
  findBlock,
  findPort,
  type RecoveryBlock,
  type RecoveryWorkflow,
} from "./model";
import { sourceKey } from "./prompt-settings";
import { readJson } from "./mcp-settings";

export interface CadOptions {
  source: "new" | "workspace" | "session" | "upstream";
  file?: string;
  document_id?: string;
  from_port?: string;
  edit_mode: "in_place" | "copy";
  copy_path: string;
  save_native: boolean;
  native_path: string;
  policy: "indexed" | "overwrite";
  exports: {
    id: string;
    port?: string;
    format: string;
    path: string;
    policy: "indexed" | "overwrite";
  }[];
}
interface CadCapabilities {
  supported: boolean;
  formats: string[];
  provider_name?: string;
  can_list: boolean;
  can_open: boolean;
  can_save: boolean;
  can_create: boolean;
  documents?: {
    documentId: string;
    displayName: string;
    isDirty: boolean;
    fullPath?: string;
  }[];
}
export const cadPortId = (block: RecoveryBlock, role: string) =>
  `port.${block.id.slice(6)}-cad-${role}`;
export function cadCommands(
  block: RecoveryBlock,
  workflow: RecoveryWorkflow,
  value: CadOptions | null,
): RecoveryCommand[] {
  const modelPort =
    workflow.ports.find(
      (port) =>
        port.ownerBlockId === block.id &&
        port.direction === "output" &&
        port.typeId === "type.geometry.brep",
    )?.id ?? cadPortId(block, "model");
  const managed = configuredOutputs(block, workflow);
  const wanted = value
    ? [
        { id: modelPort, name: "CAD model", typeId: "type.geometry.brep" },
        // Keep legacy file addresses; new blocks expose one model result.
        ...(findPort(workflow, cadPortId(block, "native")) &&
        (value.save_native ||
          value.source === "new" ||
          value.edit_mode === "copy")
          ? [
              {
                id: cadPortId(block, "native"),
                name: "Native model file",
                typeId: "type.file.workspace",
              },
            ]
          : []),
        ...value.exports.map((e, i) => ({
          id: exportPortId(block, workflow, e, "cad"),
          name: `Export file ${i + 1}`,
          typeId: "type.file.workspace",
        })),
      ]
    : [];
  const commands: RecoveryCommand[] = [];
  for (const port of workflow.ports.filter(
    (p) =>
      p.ownerBlockId === block.id &&
      p.direction === "output" &&
      (p.id.startsWith(cadPortId(block, "")) || managed.has(sourceKey(p.id))) &&
      !wanted.some((w) => w.id === p.id),
  )) {
    commands.push(
      ...workflow.relationships
        .filter((e) => e.sourceId === port.id)
        .map((e) => ({ kind: "disconnect" as const, relationshipId: e.id })),
      { kind: "delete_port", portId: port.id },
    );
  }
  for (const port of wanted.filter((p) => !findPort(workflow, p.id)))
    commands.push({
      kind: "add_port",
      port: {
        ...port,
        ownerBlockId: block.id,
        direction: "output",
        required: false,
        cardinality: "optional",
        artifactContractId: null,
        description:
          port.typeId === "type.geometry.brep"
            ? "The identified open CAD document, including unsaved changes."
            : "Verified file produced by this step in the workspace.",
      },
    });
  if (value?.source !== "upstream")
    commands.push(
      ...workflow.relationships
        .filter((e) => e.targetId === cadPortId(block, "input"))
        .map((e) => ({ kind: "disconnect" as const, relationshipId: e.id })),
    );
  commands.push({
    kind: "set_block_configuration",
    blockId: block.id,
    key: "cad",
    value: value
      ? JSON.stringify({
          ...value,
          native_port: sourceKey(cadPortId(block, "native")),
          exports: value.exports.map((e) => ({
            ...e,
            port: sourceKey(exportPortId(block, workflow, e, "cad")),
          })),
        })
      : "",
  });
  return commands;
}
export function CadTaskOptions({
  block,
  workflow,
  sessionId,
  readOnly,
  onApply,
  modelTypes = [],
}: {
  modelTypes?: { label: string; extension: string }[];
  block: RecoveryBlock;
  workflow: RecoveryWorkflow;
  sessionId?: string;
  readOnly: boolean;
  onApply: (commands: RecoveryCommand[]) => boolean;
}) {
  const [pendingExport, setPendingExport] = useState<{
    id: string;
    format: string;
  } | null>(null);
  const [caps, setCaps] = useState<CadCapabilities | null>(null),
    [error, setError] = useState(""),
    [busy, setBusy] = useState(false);
  const [files, setFiles] = useState<{ path: string; name: string }[]>([]);
  const server = String(block.configuration.mcp_server ?? "");
  const cad = readJson<CadOptions | null>(block.configuration.cad, null);
  if (cad)
    cad.exports = cad.exports.map((ex, index) => ({
      ...ex,
      id: ex.id || `legacy-${ex.port ?? index}`,
    }));
  useEffect(() => {
    let current = true;
    setCaps(null);
    setError("");
    if (sessionId && server && !block.configuration.application_resource)
      void fetch(
        `/api/workspace/workflow-sources/cad?${new URLSearchParams({ session_id: sessionId, server_id: server })}`,
      )
        .then(async (r) => {
          if (!r.ok)
            throw new Error(
              "CAD options could not be loaded. Check this server in Tool Registry.",
            );
          return r.json();
        })
        .then((c) => {
          if (current) setCaps(c);
        })
        .catch((e) => {
          if (current && cad) setError(e.message);
        });
    return () => {
      current = false;
    };
  }, [sessionId, server, Boolean(block.configuration.application_resource)]);
  async function refreshDocuments() {
    setBusy(true);
    setError("");
    try {
      const r = await fetch(
        `/api/workspace/workflow-sources/cad?${new URLSearchParams({ session_id: sessionId ?? "", server_id: server, documents: "true" })}`,
      );
      if (!r.ok)
        throw new Error(
          "Could not list open models. Start the configured CAD application and refresh.",
        );
      setCaps(await r.json());
    } catch (e) {
      setError(String(e));
    } finally {
      setBusy(false);
    }
  }
  async function refreshFiles() {
    try {
      const r = await fetch(
        `/api/workspace/workflow-sources/input-files?session_id=${encodeURIComponent(sessionId ?? "")}`,
      );
      if (!r.ok) throw new Error("Could not list workspace files.");
      setFiles((await r.json()).files);
    } catch (e) {
      setError(String(e));
    }
  }
  if (block.configuration.application_resource || (!caps?.supported && !cad))
    return null;
  const update = (patch: Partial<CadOptions>) => {
    if (cad) onApply(cadCommands(block, workflow, { ...cad, ...patch }));
  };
  const descendants = new Set([block.id]);
  for (let i = 0; i < workflow.blocks.length; i++)
    for (const e of workflow.relationships) {
      const a = findPort(workflow, e.sourceId)?.ownerBlockId,
        b = findPort(workflow, e.targetId)?.ownerBlockId;
      if (a && b && descendants.has(a)) descendants.add(b);
    }
  const candidates = workflow.ports.filter(
    (p) =>
      p.direction === "output" &&
      p.typeId === "type.geometry.brep" &&
      !descendants.has(p.ownerBlockId) &&
      findBlock(workflow, p.ownerBlockId)?.configuration.mcp_server === server,
  );
  const connected = workflow.relationships.find(
    (e) => e.targetId === cadPortId(block, "input"),
  );
  function chooseModel(sourceId: string) {
    if (!cad) return;
    const id = cadPortId(block, "input");
    const commands: RecoveryCommand[] = connected
      ? [{ kind: "disconnect", relationshipId: connected.id }]
      : [];
    if (sourceId) {
      if (!findPort(workflow, id))
        commands.push({
          kind: "add_port",
          port: {
            id,
            ownerBlockId: block.id,
            direction: "input",
            name: "CAD model",
            typeId: "type.geometry.brep",
            required: false,
            cardinality: "optional",
            artifactContractId: null,
            description: "Continue editing the upstream open document.",
          },
        });
      commands.push({
        kind: "connect",
        relationship: {
          id: `rel.${block.id.slice(6)}-cad-model`,
          kind: "data",
          sourceId,
          targetId: id,
          label: "CAD model",
          condition: null,
        },
      });
    }
    onApply([
      ...commands,
      ...cadCommands(block, workflow, { ...cad, from_port: sourceKey(id) }),
    ]);
  }
  const pending = cad?.exports.find((ex) => ex.id === pendingExport?.id);
  const changeFormat = (ex: CadOptions["exports"][number], format: string) => {
    if (format === ex.format) return;
    if (
      outputConsumers(workflow, exportPortId(block, workflow, ex, "cad")).length
    ) {
      setPendingExport({ id: ex.id, format });
      return;
    }
    update({
      exports: cad!.exports.map((x) =>
        x.id === ex.id
          ? { ...x, format, path: exportFilename(x.path, format) }
          : x,
      ),
    });
  };
  return (
    <section data-testid="workflow-recovery-cad-options">
      <label className="recovery-prompt-editor__checkbox">
        <input
          type="checkbox"
          checked={Boolean(cad)}
          disabled={readOnly}
          onChange={(e) =>
            onApply([
              ...cadCommands(
                block,
                workflow,
                e.target.checked
                  ? {
                      source: "new",
                      edit_mode: "in_place",
                      copy_path: "model-copy.psm",
                      save_native: true,
                      native_path: "model.psm",
                      policy: "indexed",
                      exports: [],
                    }
                  : null,
              ),
              ...(e.target.checked
                ? [
                    {
                      kind: "set_block_configuration" as const,
                      blockId: block.id,
                      key: "save_output",
                      value: false,
                    },
                  ]
                : []),
            ])
          }
        />
        Work with a CAD model
      </label>
      {cad && (
        <>
          <label>
            Model to work on
            <select
              data-testid="workflow-recovery-cad-source"
              disabled={readOnly}
              value={cad.source}
              onChange={(e) => {
                const source = e.target.value as CadOptions["source"];
                update({ source });
                if (source === "session") void refreshDocuments();
                if (source === "workspace") void refreshFiles();
              }}
            >
              <option value="new" disabled={caps?.can_create === false}>
                Create a new model
              </option>
              <option value="workspace" disabled={caps?.can_open === false}>
                File in this workspace
              </option>
              <option value="session" disabled={caps?.can_list === false}>
                Open in {caps?.provider_name ?? "CAD"}
              </option>
              <option value="upstream">CAD model from another block</option>
            </select>
          </label>
          {cad.source === "workspace" && (
            <label>
              Workspace CAD file
              <select
                data-testid="workflow-recovery-cad-file"
                disabled={readOnly}
                value={cad.file ?? ""}
                onFocus={() => {
                  if (!files.length) void refreshFiles();
                }}
                onChange={(e) => update({ file: e.target.value })}
              >
                <option value="">Choose a workspace file</option>
                {cad.file && !files.some((f) => f.path === cad.file) && (
                  <option>{cad.file}</option>
                )}
                {files.map((f) => (
                  <option key={f.path} value={f.path}>
                    {f.path}
                  </option>
                ))}
              </select>
              <button
                type="button"
                disabled={readOnly}
                onClick={() => void refreshFiles()}
              >
                Refresh files
              </button>
            </label>
          )}
          {cad.source === "session" && (
            <label>
              Open model
              <select
                data-testid="workflow-recovery-cad-document"
                disabled={readOnly || busy}
                value={cad.document_id ?? ""}
                onChange={(e) => update({ document_id: e.target.value })}
              >
                <option value="">Choose an open model</option>
                {cad.document_id &&
                  !caps?.documents?.some(
                    (d) => d.documentId === cad.document_id,
                  ) && (
                    <option value={cad.document_id}>
                      Previously selected model · refresh to check
                    </option>
                  )}
                {caps?.documents?.map((d) => (
                  <option key={d.documentId} value={d.documentId}>
                    {d.displayName}
                    {d.isDirty ? " · unsaved changes" : ""}
                  </option>
                ))}
              </select>
              <button
                type="button"
                disabled={readOnly || busy}
                onClick={() => void refreshDocuments()}
              >
                {busy ? "Loading…" : "Refresh open models"}
              </button>
            </label>
          )}
          {cad.source === "upstream" && (
            <label>
              CAD model from
              <select
                data-testid="workflow-recovery-cad-from"
                disabled={readOnly}
                value={connected?.sourceId ?? ""}
                onChange={(e) => chooseModel(e.target.value)}
              >
                <option value="">Choose an upstream CAD model</option>
                {candidates.map((p) => (
                  <option key={p.id} value={p.id}>
                    {findBlock(workflow, p.ownerBlockId)?.title} · {p.name}
                  </option>
                ))}
              </select>
            </label>
          )}
          {cad.source !== "new" && (
            <>
              <label>
                Edit
                <select
                  disabled={readOnly}
                  value={cad.edit_mode}
                  onChange={(e) =>
                    update({
                      edit_mode: e.target.value as CadOptions["edit_mode"],
                      ...(e.target.value === "copy"
                        ? { save_native: true }
                        : {}),
                    })
                  }
                >
                  <option value="in_place">The selected model</option>
                  <option value="copy" disabled={caps?.can_save === false}>
                    A working copy
                  </option>
                </select>
              </label>
              {cad.edit_mode === "copy" && (
                <label>
                  Working copy filename
                  <input
                    data-testid="workflow-recovery-cad-copy-path"
                    readOnly={readOnly}
                    value={cad.copy_path}
                    onChange={(e) => update({ copy_path: e.target.value })}
                  />
                  <small>
                    Includes current unsaved changes. The original stays open
                    and unchanged.
                  </small>
                </label>
              )}
            </>
          )}
          <h3>CAD model</h3>
          {cad.source === "new" && modelTypes.length > 0 && (
            <label>
              Model type
              <select
                data-testid="workflow-recovery-cad-model-type"
                disabled={readOnly}
                value={cad.native_path.split(".").at(-1) ?? ""}
                onChange={(e) =>
                  update({
                    native_path: exportFilename(
                      cad.native_path,
                      e.target.value,
                    ),
                    copy_path: exportFilename(cad.copy_path, e.target.value),
                  })
                }
              >
                <option value="">Choose a model type</option>
                {modelTypes.map((type) => (
                  <option key={type.extension} value={type.extension}>
                    {type.label}
                  </option>
                ))}
              </select>
            </label>
          )}
          <label className="recovery-prompt-editor__checkbox">
            <input
              type="checkbox"
              checked={
                cad.save_native ||
                cad.source === "new" ||
                cad.edit_mode === "copy"
              }
              disabled={
                readOnly || cad.source === "new" || cad.edit_mode === "copy"
              }
              onChange={(e) => update({ save_native: e.target.checked })}
            />
            Save native model
          </label>
          {(cad.save_native ||
            cad.source === "new" ||
            cad.edit_mode === "copy") && (
            <>
              {(cad.source === "new" || cad.edit_mode !== "copy") && (
                <label>
                  Native model filename
                  <input
                    data-testid="workflow-recovery-cad-native-path"
                    readOnly={readOnly}
                    value={cad.native_path}
                    onChange={(e) => update({ native_path: e.target.value })}
                  />
                </label>
              )}
              <label>
                If the native file exists
                <select
                  disabled={readOnly}
                  value={cad.policy}
                  onChange={(e) =>
                    update({ policy: e.target.value as CadOptions["policy"] })
                  }
                >
                  <option value="indexed">Create an indexed file</option>
                  <option value="overwrite">Overwrite existing file</option>
                </select>
              </label>
            </>
          )}
          <h3>Exports</h3>
          {pending && pendingExport && (
            <section
              className="recovery-export-impact"
              role="alert"
              aria-label="Connected output change"
            >
              <p>
                {outputConsumers(
                  workflow,
                  exportPortId(block, workflow, pending, "cad"),
                ).join(", ")}{" "}
                uses {exportFormatLabel(pending.format)}. Keep that output for
                the existing connections, or disconnect those inputs before
                changing its format.
              </p>
              <button
                type="button"
                disabled={
                  readOnly || !pendingExport.format || cad.exports.length >= 12
                }
                onClick={() => {
                  if (
                    onApply(
                      cadCommands(block, workflow, {
                        ...cad,
                        exports: [
                          ...cad.exports,
                          {
                            ...pending,
                            port: undefined,
                            id: `export-${crypto.randomUUID().slice(0, 8)}`,
                            format: pendingExport.format,
                            path: exportFilename(
                              pending.path,
                              pendingExport.format,
                            ),
                            policy: "indexed",
                          },
                        ],
                      }),
                    )
                  )
                    setPendingExport(null);
                }}
              >
                Add {exportFormatLabel(pendingExport.format)} and keep{" "}
                {exportFormatLabel(pending.format)}
              </button>
              <button type="button" onClick={() => setPendingExport(null)}>
                Keep {exportFormatLabel(pending.format)}
              </button>
            </section>
          )}
          {cad.exports.map((ex, index) => (
            <fieldset key={ex.id}>
              <legend>Export {index + 1}</legend>
              <label>
                Format
                <select
                  data-testid={`workflow-recovery-cad-export-format-${index}`}
                  disabled={readOnly}
                  value={ex.format}
                  onChange={(e) => changeFormat(ex, e.target.value)}
                >
                  <option value="">Choose a server format</option>
                  {ex.format && !caps?.formats.includes(ex.format) && (
                    <option value={ex.format}>{ex.format} · unavailable</option>
                  )}
                  {caps?.formats.map((f) => (
                    <option key={f}>{f}</option>
                  ))}
                </select>
              </label>
              <label>
                Export filename
                <input
                  data-testid={`workflow-recovery-cad-export-path-${index}`}
                  readOnly={readOnly}
                  value={ex.path}
                  onChange={(e) =>
                    update({
                      exports: cad.exports.map((x) =>
                        x.id === ex.id ? { ...x, path: e.target.value } : x,
                      ),
                    })
                  }
                />
              </label>
              <label>
                If the export exists
                <select
                  disabled={readOnly}
                  value={ex.policy}
                  onChange={(e) =>
                    update({
                      exports: cad.exports.map((x) =>
                        x.id === ex.id
                          ? {
                              ...x,
                              policy: e.target.value as CadOptions["policy"],
                            }
                          : x,
                      ),
                    })
                  }
                >
                  <option value="indexed">Create an indexed file</option>
                  <option value="overwrite">Overwrite existing file</option>
                </select>
              </label>
              {outputConsumers(
                workflow,
                exportPortId(block, workflow, ex, "cad"),
              ).length > 0 && (
                <small>
                  Used by{" "}
                  {outputConsumers(
                    workflow,
                    exportPortId(block, workflow, ex, "cad"),
                  ).join(", ")}
                  . Disconnect those inputs before removing this export.
                </small>
              )}
              <button
                type="button"
                disabled={
                  readOnly ||
                  outputConsumers(
                    workflow,
                    exportPortId(block, workflow, ex, "cad"),
                  ).length > 0
                }
                onClick={() =>
                  update({ exports: cad.exports.filter((x) => x.id !== ex.id) })
                }
              >
                Remove export {index + 1}
              </button>
            </fieldset>
          ))}
          <button
            type="button"
            data-testid="workflow-recovery-cad-add-export"
            disabled={
              readOnly || !caps?.formats.length || cad.exports.length >= 12
            }
            onClick={() =>
              update({
                exports: [
                  ...cad.exports,
                  {
                    id: `export-${crypto.randomUUID().slice(0, 8)}`,
                    format: "",
                    path: "",
                    policy: "indexed",
                  },
                ],
              })
            }
          >
            Add export
          </button>
          <small>
            The CAD model connection passes the open document. File outputs are
            saved in this workspace.
          </small>
        </>
      )}
      {error && <p role="alert">{error}</p>}
    </section>
  );
}
