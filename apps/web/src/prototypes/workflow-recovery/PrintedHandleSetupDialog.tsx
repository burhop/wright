import { useEffect, useId, useRef, useState } from "react";
import {
  handleProfileRoles,
  handleToolRoles,
  printedHandleSetup,
  type HandleProfileRole,
  type HandleSetupOptions,
  type HandleSetupProposal,
  type HandleSetupSelection,
  type HandleToolRole,
} from "../../services/printed-handle-setup";
import type { WorkspaceWorkflowSourceDocument } from "../../services/workspace-service";
import type { AuthoringWorkspaceFile } from "./AuthoringControls";
import type { OpenWorkspaceToolSetup } from "../../services/workspace-tool-setup";
import { providerSetupGuides } from "../../services/provider-setup-guides";
import { ProviderSetupGuide } from "../../components/workspace/ProviderSetupGuide";
import "./engineering-template-dialog.css";
import "./printed-handle-setup.css";

const toolLabels: Record<HandleToolRole, string> = {
  construction: "Construction · FreeCAD",
  geometry: "Repair and preview · Blender",
  slicer: "Slicing · Orca",
  inspection: "Independent inspection · engineering Python",
};
const toolHelp: Record<
  HandleToolRole,
  { title: string; purpose: string; guide: keyof typeof providerSetupGuides }
> = {
  construction: {
    title: "Configure the CAD tool",
    purpose: "FreeCAD constructs the solid handle from the confirmed design.",
    guide: "freecad",
  },
  geometry: {
    title: "Configure the mesh tool",
    purpose: "Blender repairs and previews the actual handle geometry.",
    guide: "blender",
  },
  slicer: {
    title: "Configure the slicing tool",
    purpose: "Orca prepares and compares the two print orientations.",
    guide: "shell",
  },
  inspection: {
    title: "Configure the inspection tool",
    purpose:
      "Engineering Python inspects the geometry and print packages independently.",
    guide: "oasis",
  },
};
const profileLabels: Record<HandleProfileRole, string> = {
  machine: "P1S 0.4 mm machine profile",
  process_original: "Original five-wall, 40% process profile",
  process_orca: "Orca-compatible process profile",
  filament: "PETG filament profile",
};
const emptyTools = (): Record<HandleToolRole, string> => ({
  construction: "",
  geometry: "",
  slicer: "",
  inspection: "",
});
const emptyProfiles = (): Record<HandleProfileRole, string> => ({
  machine: "",
  process_original: "",
  process_orca: "",
  filament: "",
});

export function PrintedHandleSetupDialog({
  document,
  sessionId,
  onListFiles,
  onClose,
  onAccepted,
  onConfigureTools,
}: {
  document: WorkspaceWorkflowSourceDocument;
  sessionId: string;
  onListFiles: () => Promise<AuthoringWorkspaceFile[]>;
  onClose: () => void;
  onAccepted: (document: WorkspaceWorkflowSourceDocument) => void;
  onConfigureTools?: OpenWorkspaceToolSetup;
}) {
  const titleId = useId();
  const dialog = useRef<HTMLDialogElement>(null);
  const generation = useRef(0);
  const configurationRequest = useRef(0);
  const draftScope = useRef("");
  const [configuring, setConfiguring] = useState(false);
  const [helpRole, setHelpRole] = useState<HandleToolRole | null>(null);
  const [refresh, setRefresh] = useState(0);
  const [options, setOptions] = useState<HandleSetupOptions | null>(null);
  const [files, setFiles] = useState<AuthoringWorkspaceFile[]>([]);
  const [tools, setTools] = useState(emptyTools);
  const [profiles, setProfiles] = useState(emptyProfiles);
  const [mount, setMount] = useState("");
  const [orientation, setOrientation] = useState<"pads_down" | "side">(
    "pads_down",
  );
  const [proposal, setProposal] = useState<HandleSetupProposal | null>(null);
  const [reviewed, setReviewed] = useState(false);
  const [state, setState] = useState<
    "loading" | "idle" | "proposing" | "accepting"
  >("loading");
  const [error, setError] = useState("");
  const busy = state !== "idle";

  useEffect(() => {
    const node = dialog.current;
    if (node && configuring) {
      node.close?.();
      node.removeAttribute("open");
    } else if (node && !node.open) {
      if (node.showModal) node.showModal();
      else node.setAttribute("open", "");
    }
  }, [configuring]);

  useEffect(() => {
    const current = ++generation.current;
    const scope = `${sessionId}:${document.workspace_id}:${document.path}:${document.storage_revision}:${document.storage_digest}`;
    const firstLoad = draftScope.current !== scope;
    setOptions(null);
    setFiles([]);
    if (firstLoad) {
      configurationRequest.current += 1;
      setConfiguring(false);
      setTools(emptyTools());
      setProfiles(emptyProfiles());
      setOrientation("pads_down");
      setHelpRole(null);
    }
    setProposal(null);
    setReviewed(false);
    setError("");
    setState("loading");
    void Promise.all([
      printedHandleSetup.options(sessionId, document),
      onListFiles(),
    ])
      .then(([loaded, listed]) => {
        if (current !== generation.current) return;
        draftScope.current = scope;
        setOptions(loaded);
        setFiles(listed.filter((file) => file.path.endsWith(".json")));
        setMount(loaded.workspace_mount);
        if (firstLoad)
          setTools(
            Object.fromEntries(
              handleToolRoles.map((role) => [
                role,
                loaded.tools[role].length === 1
                  ? loaded.tools[role][0]!.name
                  : "",
              ]),
            ) as Record<HandleToolRole, string>,
          );
      })
      .catch((reason: unknown) => {
        if (current === generation.current)
          setError(
            reason instanceof Error
              ? reason.message
              : "Setup choices could not be loaded.",
          );
      })
      .finally(() => {
        if (current === generation.current) setState("idle");
      });
    return () => {
      generation.current = current + 1;
    };
  }, [document, sessionId, onListFiles, refresh]);

  const invalidate = () => {
    setProposal(null);
    setReviewed(false);
    setError("");
  };
  const configureTool = async (role: HandleToolRole) => {
    if (!options || busy || configuring) return;
    setHelpRole(role);
    invalidate();
    if (!onConfigureTools) {
      setError(
        "MCP Tools is unavailable in this view. Use the provider guide below, or reopen this job in its workspace. Your setup selections are kept.",
      );
      return;
    }
    const current = generation.current;
    const requestId = ++configurationRequest.current;
    setConfiguring(true);
    try {
      await onConfigureTools({
        workspaceId: document.workspace_id,
        sessionId,
        sourcePath: document.path,
        sourceDigest: document.storage_digest,
        title: toolHelp[role].title,
        purpose: toolHelp[role].purpose,
        requirements: options.requirements,
        guideText: providerSetupGuides[toolHelp[role].guide],
      });
      if (current === generation.current) setRefresh((value) => value + 1);
    } catch (reason) {
      if (current === generation.current)
        setError(
          reason instanceof Error
            ? reason.message
            : "MCP Tools could not be opened. Use the provider guide and retry. Your setup selections are kept.",
        );
    } finally {
      if (requestId === configurationRequest.current) setConfiguring(false);
    }
  };
  const complete =
    !!options &&
    mount.trim().startsWith("/") &&
    handleToolRoles.every((role) =>
      options.tools[role].some((tool) => tool.name === tools[role]),
    ) &&
    handleProfileRoles.every((role) =>
      files.some((file) => file.path === profiles[role]),
    );

  const propose = async () => {
    if (!options || !complete || busy) return;
    const current = generation.current;
    invalidate();
    setState("proposing");
    const selection: HandleSetupSelection = {
      workspace_mount: mount.trim(),
      selected_orientation: orientation,
      tools: Object.fromEntries(
        handleToolRoles.map((role) => {
          const tool = options.tools[role].find(
            (item) => item.name === tools[role],
          )!;
          return [
            role,
            {
              server_id: tool.server_id,
              name: tool.name,
              schema_digest: tool.schema_digest,
            },
          ];
        }),
      ) as HandleSetupSelection["tools"],
      profiles: Object.fromEntries(
        handleProfileRoles.map((role) => [role, { path: profiles[role] }]),
      ) as HandleSetupSelection["profiles"],
    };
    try {
      const prepared = await printedHandleSetup.propose(
        sessionId,
        document,
        selection,
      );
      if (current !== generation.current) return;
      if (
        prepared.workflow_id !== options.workflow_id ||
        prepared.recipe.id !== options.recipe.id ||
        prepared.recipe.version !== options.recipe.version ||
        prepared.recipe.digest !== options.recipe.digest
      )
        throw new Error(
          "The setup recipe or workflow changed. Refresh setup before accepting a proposal.",
        );
      setProposal(prepared);
    } catch (reason) {
      if (current === generation.current)
        setError(
          reason instanceof Error
            ? reason.message
            : "The setup proposal could not be prepared.",
        );
    } finally {
      if (current === generation.current) setState("idle");
    }
  };
  const accept = async () => {
    if (!proposal || !reviewed || busy) return;
    const current = generation.current;
    setState("accepting");
    setError("");
    try {
      const accepted = await printedHandleSetup.accept(
        sessionId,
        document,
        proposal,
      );
      if (current === generation.current) onAccepted(accepted);
    } catch (reason) {
      if (current === generation.current) {
        setReviewed(false);
        setProposal(null);
        setError(
          reason instanceof Error
            ? reason.message
            : "The revision could not be accepted. Reopen the saved source before trying again.",
        );
      }
    } finally {
      if (current === generation.current) setState("idle");
    }
  };

  return (
    <dialog
      ref={dialog}
      className="engineering-template-dialog printed-handle-setup"
      aria-labelledby={titleId}
      data-testid="printed-handle-setup-dialog"
      onCancel={(event) => {
        event.preventDefault();
        if (!busy) onClose();
      }}
    >
      <header>
        <div>
          <p className="engineering-template-dialog__eyebrow">
            Replace a broken drawer handle
          </p>
          <h2 id={titleId}>Set up this job</h2>
        </div>
        <button
          type="button"
          className="engineering-template-dialog__close"
          aria-label="Close handle setup"
          disabled={busy}
          onClick={onClose}
        >
          ×
        </button>
      </header>
      <div className="printed-handle-setup__body">
        <p>
          Bind the supplied handle process to your workspace. Inspect the
          proposed revision before accepting it; then use the working view to
          check inputs and start work.
        </p>
        <p>
          Setup makes no model or engineering-tool calls. It does not qualify
          native applications or approve an engineering review.
        </p>
        {state === "loading" && (
          <p role="status">Loading current setup choices…</p>
        )}
        {error && <p role="alert">{error}</p>}
        {helpRole && (
          <ProviderSetupGuide
            text={providerSetupGuides[toolHelp[helpRole].guide]}
          />
        )}
        <button
          type="button"
          className="recovery-button recovery-button--secondary"
          disabled={busy}
          onClick={() => setRefresh((value) => value + 1)}
        >
          Refresh choices
        </button>
        {options && (
          <>
            <h3>Tools and native configuration</h3>
            <p data-testid="handle-setup-recipe">
              Setup recipe: {options.recipe.id} · version{" "}
              {options.recipe.version}
            </p>
            <ul>
              {options.requirements.map((requirement, index) => (
                <li key={index}>{requirement}</li>
              ))}
            </ul>
            <p>
              Available tools are discovered in this workspace. Their presence
              does not prove that the native operation or shared file mount is
              qualified.
            </p>
            <fieldset disabled={busy}>
              <legend>Selected capabilities</legend>
              {handleToolRoles.map((role) => (
                <div key={role}>
                  <label>
                    {toolLabels[role]}
                    <select
                      data-testid={`handle-setup-tool-${role}`}
                      value={tools[role]}
                      onChange={(event) => {
                        invalidate();
                        setTools({ ...tools, [role]: event.target.value });
                      }}
                    >
                      <option value="">Choose an enabled tool</option>
                      {options.tools[role].map((tool) => (
                        <option
                          key={`${tool.server_id}:${tool.name}`}
                          value={tool.name}
                        >
                          {tool.server_name ?? tool.server_id} ·{" "}
                          {tool.title ?? tool.tool_name}
                        </option>
                      ))}
                    </select>
                  </label>
                  {!options.tools[role].length && (
                    <div>
                      <p>
                        No matching tool is available. {toolHelp[role].purpose}
                      </p>
                      <button
                        type="button"
                        className="recovery-button recovery-button--secondary"
                        onClick={() => void configureTool(role)}
                      >
                        {toolHelp[role].title}
                      </button>
                    </div>
                  )}
                </div>
              ))}
              <label>
                Required managed workspace path in the selected providers
                <input
                  data-testid="handle-setup-mount"
                  value={mount}
                  readOnly
                />
              </label>
              <p>
                Configure every selected provider to access this workspace at
                this exact absolute path. This recipe requires the managed
                workspace path; Wright does not infer mount equivalence.
              </p>
            </fieldset>
            <fieldset disabled={busy}>
              <legend>Exact P1S / PETG profiles</legend>
              <p>
                The assignment retains a 0.4 mm nozzle, 0.20 mm layers, five
                walls and 40% infill. Add the exported JSON profiles to this
                workspace, then refresh choices.
              </p>
              {handleProfileRoles.map((role) => (
                <label key={role}>
                  {profileLabels[role]}
                  <select
                    data-testid={`handle-setup-profile-${role}`}
                    value={profiles[role]}
                    onChange={(event) => {
                      invalidate();
                      setProfiles({ ...profiles, [role]: event.target.value });
                    }}
                  >
                    <option value="">Choose a workspace JSON file</option>
                    {files.map((file) => (
                      <option key={file.path} value={file.path}>
                        {file.path}
                      </option>
                    ))}
                  </select>
                </label>
              ))}
              <p>
                The compatible process profile must retain the original settings
                with only the documented Orca automatic support-wall mapping.
                The proposal pins the exact file copies for inspection.
              </p>
              <label>
                Final package orientation
                <select
                  data-testid="handle-setup-orientation"
                  value={orientation}
                  onChange={(event) => {
                    invalidate();
                    setOrientation(event.target.value as "pads_down" | "side");
                  }}
                >
                  <option value="pads_down">Pads down</option>
                  <option value="side">Side</option>
                </select>
              </label>
              <p>
                Both orientations are compared. A changed selection needs a new
                accepted revision and affected output checks.
              </p>
            </fieldset>
            <details>
              <summary>Recipe and exact tool identities</summary>
              <code>{options.recipe.digest}</code>
              <pre>
                {JSON.stringify(
                  handleToolRoles.map((role) => ({
                    role,
                    tool:
                      options.tools[role].find(
                        (tool) => tool.name === tools[role],
                      ) ?? null,
                  })),
                  null,
                  2,
                )}
              </pre>
            </details>
            <button
              type="button"
              className="recovery-button recovery-button--primary"
              data-testid="handle-setup-propose"
              disabled={busy || !complete}
              onClick={() => void propose()}
            >
              {state === "proposing"
                ? "Preparing proposal…"
                : "Prepare setup proposal"}
            </button>
          </>
        )}
        {proposal && (
          <section
            aria-label="Review handle setup proposal"
            data-testid="handle-setup-proposal"
          >
            <h3>Inspect the proposed revision</h3>
            <p>
              This replaces the saved starter definition at{" "}
              <code>{document.path}</code>. The workflow identity and original
              template provenance are retained. Existing run evidence stays
              separate.
            </p>
            <p>
              Native qualification, model access and current run readiness
              remain to be checked. The final handoff is a manually reviewed
              local simulation; no printer connection or print is included.
            </p>
            <details open>
              <summary>Preparation summary</summary>
              <pre>{JSON.stringify(proposal.summary, null, 2)}</pre>
            </details>
            <details>
              <summary>Compare saved and proposed source</summary>
              <label>
                Saved source
                <textarea readOnly rows={12} value={document.source} />
              </label>
              <label>
                Proposed source
                <textarea readOnly rows={12} value={proposal.source} />
              </label>
              <p>
                Proposed source SHA-256: <code>{proposal.source_digest}</code>
              </p>
            </details>
            <details>
              <summary>
                Exact dependency manifest ({proposal.dependencies.length} files)
              </summary>
              <ul>
                {proposal.dependencies.map((file) => (
                  <li key={file.path}>
                    <code>{file.path}</code>
                    <br />
                    {file.size_bytes} bytes · <code>{file.sha256}</code>
                  </li>
                ))}
              </ul>
            </details>
            <label className="printed-handle-setup__confirmation">
              <input
                type="checkbox"
                data-testid="handle-setup-reviewed"
                checked={reviewed}
                disabled={busy}
                onChange={(event) => setReviewed(event.target.checked)}
              />
              I have inspected the proposed process, selected tools and exact
              input files.
            </label>
          </section>
        )}
      </div>
      <footer>
        <button
          type="button"
          className="recovery-button recovery-button--secondary"
          disabled={busy}
          onClick={onClose}
        >
          Close
        </button>
        {proposal && <button
          type="button"
          className="recovery-button recovery-button--primary"
          data-testid="handle-setup-accept"
          disabled={busy || !proposal || !reviewed}
          onClick={() => void accept()}
        >
          {state === "accepting"
            ? "Accepting revision…"
            : "Accept prepared revision"}
        </button>}
      </footer>
    </dialog>
  );
}
