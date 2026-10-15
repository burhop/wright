import { useEffect, useRef, useState } from "react";
import {
  workflowBundles,
  parseWorkflowBundleFile,
  type WorkflowBundleInspection,
  type WorkflowBundleClient,
} from "../../services/workflow-bundles";
import {
  workspaceService,
  type WorkspaceWorkflowSourceDocument,
} from "../../services/workspace-service";
import { createInterfaceAuthoringClient } from "../../services/process-ui-authoring";
import type { ProcessUI } from "@wright/process-client";
import "./workflow-recovery.css";

export function WorkflowBundleDialog({
  document,
  sessionId,
  onClose,
  onImported,
  transfer = workflowBundles,
  listFiles,
  listInterfaces,
  onOpenDestination,
}: {
  document: WorkspaceWorkflowSourceDocument;
  sessionId: string;
  onClose: () => void;
  onImported: (path: string) => void | Promise<void>;
  onOpenDestination?: (path: string) => Promise<void>;
  transfer?: WorkflowBundleClient;
  listFiles?: () => Promise<Array<{ path: string; name: string }>>;
  listInterfaces?: () => Promise<readonly ProcessUI[]>;
}) {
  const [mode, setMode] = useState<"source" | "bundle">("source");
  const [files, setFiles] = useState<Array<{ path: string; name: string }>>([]);
  const [uis, setUis] = useState<Array<{ id: string; title: string }>>([]);
  const [references, setReferences] = useState<string[]>([]);
  const [selectedUis, setSelectedUis] = useState<string[]>([]);
  const [bundle, setBundle] = useState<Record<string, unknown> | null>(null);
  const [destination, setDestination] = useState(
    "workflows/imported-process.workflow.wflow",
  );
  const [report, setReport] = useState<WorkflowBundleInspection | null>(null);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState("");
  const [message, setMessage] = useState("");
  const [attemptedDestination, setAttemptedDestination] = useState<
    string | null
  >(null);
  const requestRevision = useRef(0);
  const dialogRef = useRef<HTMLElement>(null);
  useEffect(() => {
    const opener =
      window.document.activeElement instanceof HTMLElement
        ? window.document.activeElement
        : null;
    dialogRef.current
      ?.querySelector<HTMLButtonElement>(
        'button[aria-label="Close workflow transfer"]',
      )
      ?.focus();
    return () => opener?.focus();
  }, []);
  const perform = async (operation: () => Promise<void>) => {
    setBusy(true);
    setError("");
    setMessage("");
    try {
      await operation();
    } catch (error) {
      setError(
        error instanceof Error ? error.message : "Workflow transfer failed.",
      );
    } finally {
      setBusy(false);
    }
  };
  const changeDestination = (path: string) => {
    requestRevision.current++;
    setDestination(path);
    setReport(null);
  };
  const download = async () => {
    const exported = await transfer.export(
      sessionId,
      document.path,
      document.storage_digest,
      mode,
      mode === "bundle" ? references : [],
      mode === "bundle" ? selectedUis : [],
    );
    const url = URL.createObjectURL(
      new Blob([JSON.stringify(exported, null, 2)], {
        type: "application/json",
      }),
    );
    const link = window.document.createElement("a");
    link.href = url;
    link.download = `${document.path.split("/").at(-1)}.wright-workflow.json`;
    window.document.body.append(link);
    link.click();
    link.remove();
    window.setTimeout(() => URL.revokeObjectURL(url), 0);
    setMessage(
      "Download requested. Check your downloads for the workflow transfer. Saved instructions are included; execution and approvals are not transferred.",
    );
  };
  return (
    <div
      className="recovery-modal-backdrop workflow-recovery-modal-theme"
      onKeyDown={(event) => {
        if (event.key === "Escape" && !busy) onClose();
      }}
    >
      <section
        ref={dialogRef}
        className="recovery-modal recovery-modal--instructions"
        role="dialog"
        aria-modal="true"
        aria-labelledby="workflow-transfer-title"
        data-testid="workflow-transfer-dialog"
        onKeyDown={(event) => {
          if (event.key !== "Tab") return;
          const controls = [
            ...(dialogRef.current?.querySelectorAll<HTMLElement>(
              'button:not(:disabled), input:not(:disabled), select:not(:disabled), summary, [tabindex="0"]',
            ) ?? []),
          ];
          const first = controls[0];
          const last = controls.at(-1);
          if (event.shiftKey && window.document.activeElement === first) {
            event.preventDefault();
            last?.focus();
          } else if (
            !event.shiftKey &&
            window.document.activeElement === last
          ) {
            event.preventDefault();
            first?.focus();
          }
        }}
      >
        <header>
          <div>
            <span>WORKFLOW FILES</span>
            <h2 id="workflow-transfer-title">Export or import a workflow</h2>
          </div>
          <button
            type="button"
            aria-label="Close workflow transfer"
            data-testid="workflow-transfer-close"
            disabled={busy}
            onClick={onClose}
          >
            ×
          </button>
        </header>
        <div className="wright-instruction-editor">
          <p>
            Transfer a saved process definition and its instructions. Import
            checks dependencies; it does not approve engineering results, start
            a run or grant external-action authority.
          </p>
          <h3>Export {document.path.split("/").at(-1)}</h3>
          <label>
            Transfer contents
            <select
              data-testid="workflow-transfer-mode"
              value={mode}
              disabled={busy}
              onChange={(event) => setMode(event.target.value as typeof mode)}
            >
              <option value="source">Source and dependency manifest</option>
              <option value="bundle">
                Bundle with selected reference files and interfaces
              </option>
            </select>
          </label>
          {mode === "bundle" && (
            <>
              <button
                type="button"
                className="recovery-button recovery-button--secondary"
                data-testid="workflow-transfer-list-assets"
                disabled={busy}
                onClick={() =>
                  void perform(async () => {
                    const outcomes = await Promise.allSettled([
                      listFiles
                        ? listFiles()
                        : workspaceService.getWorkspaceWorkflowInputFiles(
                            sessionId,
                            document.workspace_id,
                          ),
                      listInterfaces
                        ? listInterfaces()
                        : createInterfaceAuthoringClient(
                            {
                              workspace_id: document.workspace_id,
                              source_path: document.path,
                              source_digest: document.storage_digest,
                            },
                            sessionId,
                          ).interfaces(),
                    ]);
                    if (outcomes[0].status === "fulfilled")
                      setFiles(
                        outcomes[0].value.filter(
                          (file) =>
                            !/^(runs|node_modules|workflows)\//i.test(
                              file.path,
                            ),
                        ),
                      );
                    if (outcomes[1].status === "fulfilled")
                      setUis(
                        outcomes[1].value
                          .filter(
                            (ui) =>
                              !ui.archived &&
                              !!ui.active_revision &&
                              ui.process.source_digest ===
                                document.storage_digest,
                          )
                          .map((ui) => ({ id: ui.ui_id, title: ui.title })),
                      );
                    const failures = outcomes.filter(
                      (outcome) => outcome.status === "rejected",
                    );
                    if (failures.length)
                      throw new Error(
                        "Some selectable files or interfaces could not be loaded. Source transfer remains available; retry the list before selecting unavailable items.",
                      );
                  })
                }
              >
                Load available reference files and interfaces
              </button>
              <fieldset>
                <legend>Reference files to include</legend>
                {files.length ? (
                  files.map((file) => (
                    <label key={file.path}>
                      <input
                        type="checkbox"
                        data-testid={`workflow-transfer-file-${file.path}`}
                        disabled={busy}
                        checked={references.includes(file.path)}
                        onChange={(event) =>
                          setReferences(
                            event.target.checked
                              ? [...references, file.path]
                              : references.filter((path) => path !== file.path),
                          )
                        }
                      />
                      {file.path}
                    </label>
                  ))
                ) : (
                  <p>
                    No reference files selected. Load available files to choose
                    them.
                  </p>
                )}
              </fieldset>
              <fieldset>
                <legend>Saved working interfaces to include</legend>
                {uis.length ? (
                  uis.map((ui) => (
                    <label key={ui.id}>
                      <input
                        type="checkbox"
                        data-testid={`workflow-transfer-ui-${ui.id}`}
                        disabled={busy}
                        checked={selectedUis.includes(ui.id)}
                        onChange={(event) =>
                          setSelectedUis(
                            event.target.checked
                              ? [...selectedUis, ui.id]
                              : selectedUis.filter((id) => id !== ui.id),
                          )
                        }
                      />
                      {ui.title}
                    </label>
                  ))
                ) : (
                  <p>
                    No saved interfaces selected. Only interfaces bound to this
                    exact revision are eligible.
                  </p>
                )}
              </fieldset>
              <p>
                Validation profile snapshots are included when available.
                Imported interfaces need a local rebuild and review before use.
              </p>
            </>
          )}
          <button
            type="button"
            className="recovery-button recovery-button--primary"
            data-testid="workflow-transfer-export"
            disabled={busy}
            onClick={() => void perform(download)}
          >
            Download workflow transfer
          </button>
          <h3>Import into this workspace</h3>
          <label>
            Workflow transfer file
            <input
              type="file"
              accept=".json,application/json"
              data-testid="workflow-transfer-upload"
              disabled={busy}
              onChange={(event) => {
                const file = event.target.files?.[0];
                if (!file) return;
                requestRevision.current++;
                setReport(null);
                setBundle(null);
                void perform(async () => {
                  if (file.size > 20 * 1024 * 1024)
                    throw new Error(
                      "Choose a workflow transfer file within 20 MiB.",
                    );
                  setBundle(parseWorkflowBundleFile(await file.text()));
                });
              }}
            />
          </label>
          <label>
            Destination workflow file
            <input
              data-testid="workflow-transfer-destination"
              value={destination}
              disabled={busy}
              onChange={(event) => changeDestination(event.target.value)}
            />
          </label>
          <button
            type="button"
            className="recovery-button recovery-button--secondary"
            data-testid="workflow-transfer-inspect"
            disabled={busy || !bundle}
            onClick={() =>
              void perform(async () => {
                if (!bundle) return;
                const revision = requestRevision.current;
                const inspection = await transfer.inspect(
                  sessionId,
                  bundle,
                  destination,
                );
                if (revision === requestRevision.current) setReport(inspection);
              })
            }
          >
            Inspect before importing
          </button>
          {report && (
            <section aria-label="Workflow import inspection">
              <h3>
                {report.can_import
                  ? "Definition can be imported"
                  : "Import needs correction"}
              </h3>
              <p>
                Running this workflow still requires local setup and readiness
                checks.
              </p>
              <ul
                className="workflow-transfer-diagnostics"
                aria-label="Import findings"
              >
                {report.diagnostics.map((diagnostic, index) => (
                  <li key={index} data-testid="workflow-transfer-diagnostic">
                    <strong>
                      {diagnostic.severity === "error"
                        ? "Needs correction"
                        : "Setup required"}
                    </strong>
                    {diagnostic.dependency && (
                      <p>
                        For: <span>{diagnostic.dependency}</span>
                      </p>
                    )}
                    <p>{diagnostic.message}</p>
                  </li>
                ))}
              </ul>
              <details>
                <summary data-testid="workflow-transfer-dependencies-toggle">
                  External dependencies and requirements
                </summary>
                <pre>
                  {JSON.stringify(
                    {
                      diagnostics: report.diagnostics,
                      external_dependencies: report.external_dependencies,
                      requirements: report.requirements,
                    },
                    null,
                    2,
                  )}
                </pre>
              </details>
              <button
                type="button"
                className="recovery-button recovery-button--primary"
                data-testid="workflow-transfer-import"
                disabled={busy || !report.can_import || !bundle}
                onClick={() =>
                  void perform(async () => {
                    if (!bundle || !report.can_import) return;
                    setAttemptedDestination(destination);
                    const imported = await transfer.import(
                      sessionId,
                      bundle,
                      destination,
                      report.bundle_digest,
                    );
                    if (
                      imported.source.workspace_id !== document.workspace_id ||
                      imported.source.path !== destination
                    )
                      throw new Error(
                        "Wright returned an imported workflow for a different workspace or path.",
                      );
                    setMessage(
                      `Imported ${imported.source.path}. Local setup and reviews remain required.`,
                    );
                    setReport(null);
                    await onImported(imported.source.path);
                  })
                }
              >
                Import inspected definition
              </button>
            </section>
          )}
          {error && <p role="alert">{error}</p>}
          {error && attemptedDestination && onOpenDestination && (
            <button
              type="button"
              disabled={busy}
              onClick={() =>
                void perform(() => onOpenDestination(attemptedDestination))
              }
            >
              Open saved destination
            </button>
          )}
          {message && <p role="status">{message}</p>}
        </div>
      </section>
    </div>
  );
}
