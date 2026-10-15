import {
  fireEvent,
  render,
  screen,
  waitFor,
  within,
} from "@testing-library/react";
import { afterEach, expect, it, vi } from "vitest";
const mocks = vi.hoisted(() => ({ interfaces: vi.fn() }));
vi.mock("../../services/process-ui-authoring", () => ({
  createInterfaceAuthoringClient: () => ({ interfaces: mocks.interfaces }),
}));
import { WorkflowBundleDialog } from "./WorkflowBundleDialog";
import { workflowBundles } from "../../services/workflow-bundles";
import { workspaceService } from "../../services/workspace-service";
import type { WorkspaceWorkflowSourceDocument } from "../../services/workspace-service";
const document = {
  workspace_id: "workspace",
  path: "workflows/example.workflow.wflow",
  storage_digest: "a".repeat(64),
} as WorkspaceWorkflowSourceDocument;
const bundle = {
  schema_version: "wright.workflow-bundle/1",
  source: "exact saved source",
};
const inspection = {
  bundle_digest: "b".repeat(64),
  can_import: true,
  can_run: false as const,
  diagnostics: [
    {
      code: "provider_setup",
      severity: "warning" as const,
      message: "Configure the independent provider locally.",
    },
  ],
  external_dependencies: [{ category: "provider", identity: "independent" }],
  requirements: [],
};
afterEach(() => {
  vi.restoreAllMocks();
  vi.unstubAllGlobals();
  mocks.interfaces.mockReset();
});
function upload() {
  const file = new File([JSON.stringify({ bundle })], "workflow.json", {
    type: "application/json",
  });
  Object.defineProperty(file, "text", {
    value: async () => JSON.stringify({ bundle }),
  });
  fireEvent.change(screen.getByTestId("workflow-transfer-upload"), {
    target: { files: [file] },
  });
}
it("uses the injected transfer owner without falling back to the web transport", async () => {
  const webInspect = vi.spyOn(workflowBundles, "inspect");
  const transfer = {
    export: vi.fn(),
    inspect: vi.fn().mockResolvedValue(inspection),
    import: vi.fn().mockResolvedValue({
      source: {
        ...document,
        path: "workflows/imported-process.workflow.wflow",
      },
      imported_paths: [],
      inspection,
    }),
  };
  const onImported = vi.fn();
  render(
    <WorkflowBundleDialog
      document={document}
      sessionId="session"
      onClose={vi.fn()}
      onImported={onImported}
      transfer={transfer}
    />,
  );
  upload();
  await waitFor(() =>
    expect(screen.getByTestId("workflow-transfer-inspect")).not.toBeDisabled(),
  );
  fireEvent.click(screen.getByTestId("workflow-transfer-inspect"));
  await screen.findByText("Definition can be imported");
  fireEvent.click(screen.getByTestId("workflow-transfer-import"));
  await waitFor(() => expect(onImported).toHaveBeenCalledOnce());
  expect(transfer.inspect).toHaveBeenCalledOnce();
  expect(transfer.import).toHaveBeenCalledOnce();
  expect(webInspect).not.toHaveBeenCalled();
});
it("requires uploaded definition inspection before explicit import and rechecks after destination edits", async () => {
  const inspect = vi
    .spyOn(workflowBundles, "inspect")
    .mockResolvedValue(inspection);
  const apply = vi.spyOn(workflowBundles, "import").mockResolvedValue({
    source: { ...document, path: "workflows/different.workflow.wflow" },
    imported_paths: [],
    inspection,
  });
  const onImported = vi.fn();
  render(
    <WorkflowBundleDialog
      document={document}
      sessionId="session"
      onClose={vi.fn()}
      onImported={onImported}
    />,
  );
  expect(inspect).not.toHaveBeenCalled();
  expect(apply).not.toHaveBeenCalled();
  expect(screen.getByTestId("workflow-transfer-inspect")).toBeDisabled();
  upload();
  await waitFor(() =>
    expect(screen.getByTestId("workflow-transfer-inspect")).not.toBeDisabled(),
  );
  fireEvent.click(screen.getByTestId("workflow-transfer-inspect"));
  await screen.findByText("Definition can be imported");
  expect(screen.getByText(/Running this workflow still requires/)).toBeTruthy();
  expect(apply).not.toHaveBeenCalled();
  fireEvent.change(screen.getByTestId("workflow-transfer-destination"), {
    target: { value: "workflows/different.workflow.wflow" },
  });
  expect(screen.queryByTestId("workflow-transfer-import")).toBeNull();
  fireEvent.click(screen.getByTestId("workflow-transfer-inspect"));
  await screen.findByText("Definition can be imported");
  fireEvent.click(screen.getByTestId("workflow-transfer-import"));
  await waitFor(() =>
    expect(apply).toHaveBeenCalledExactlyOnceWith(
      "session",
      bundle,
      "workflows/different.workflow.wflow",
      inspection.bundle_digest,
    ),
  );
  await waitFor(() =>
    expect(onImported).toHaveBeenCalledExactlyOnceWith(
      "workflows/different.workflow.wflow",
    ),
  );
});
it("keeps import disabled when the backend reports a definition defect", async () => {
  vi.spyOn(workflowBundles, "inspect").mockResolvedValue({
    ...inspection,
    can_import: false,
  });
  const apply = vi.spyOn(workflowBundles, "import");
  render(
    <WorkflowBundleDialog
      document={document}
      sessionId="session"
      onClose={vi.fn()}
      onImported={vi.fn()}
    />,
  );
  upload();
  await waitFor(() =>
    expect(screen.getByTestId("workflow-transfer-inspect")).not.toBeDisabled(),
  );
  fireEvent.click(screen.getByTestId("workflow-transfer-inspect"));
  await screen.findByText("Import needs correction");
  expect(screen.getByTestId("workflow-transfer-import")).toBeDisabled();
  expect(apply).not.toHaveBeenCalled();
});
it("exports only selected files and active interfaces on the exact saved revision", async () => {
  vi.spyOn(
    workspaceService,
    "getWorkspaceWorkflowInputFiles",
  ).mockResolvedValue([
    { path: "images/reference.png", name: "reference.png" },
    { path: "runs/history.json", name: "history.json" },
  ]);
  mocks.interfaces.mockResolvedValue([
    {
      ui_id: "ui-current",
      title: "Current interface",
      archived: false,
      active_revision: "r1",
      process: { source_digest: document.storage_digest },
    },
    {
      ui_id: "ui-old",
      title: "Old interface",
      archived: false,
      active_revision: "r1",
      process: { source_digest: "c".repeat(64) },
    },
  ]);
  const exportFile = vi
    .spyOn(workflowBundles, "export")
    .mockResolvedValue({ bundle, bundle_digest: inspection.bundle_digest });
  Object.defineProperty(URL, "createObjectURL", {
    configurable: true,
    value: vi.fn(() => "blob:transfer"),
  });
  Object.defineProperty(URL, "revokeObjectURL", {
    configurable: true,
    value: vi.fn(),
  });
  vi.spyOn(HTMLAnchorElement.prototype, "click").mockImplementation(
    () => undefined,
  );
  render(
    <WorkflowBundleDialog
      document={document}
      sessionId="session"
      onClose={vi.fn()}
      onImported={vi.fn()}
    />,
  );
  fireEvent.change(screen.getByTestId("workflow-transfer-mode"), {
    target: { value: "bundle" },
  });
  fireEvent.click(screen.getByTestId("workflow-transfer-list-assets"));
  await screen.findByLabelText("images/reference.png");
  expect(screen.queryByText("runs/history.json")).toBeNull();
  expect(screen.queryByLabelText("Old interface")).toBeNull();
  fireEvent.click(screen.getByLabelText("images/reference.png"));
  fireEvent.click(screen.getByLabelText("Current interface"));
  fireEvent.click(screen.getByTestId("workflow-transfer-export"));
  await waitFor(() =>
    expect(exportFile).toHaveBeenCalledExactlyOnceWith(
      "session",
      document.path,
      document.storage_digest,
      "bundle",
      ["images/reference.png"],
      ["ui-current"],
    ),
  );
  await screen.findByText(/Download requested. Check your downloads/);
});

it("names exact dependencies beside their findings and keeps diagnostic codes in details", async () => {
  vi.spyOn(workflowBundles, "inspect").mockResolvedValue({
    ...inspection,
    diagnostics: [
      {
        code: "external_dependency",
        severity: "warning",
        message: "Prepare this dependency before starting.",
        dependency: "references/design.png",
      },
      {
        code: "local_qualification_required",
        severity: "warning",
        message: "Qualify the local binding before running.",
        dependency: "thermal-analysis",
      },
      {
        code: "bundle_import_invalid",
        severity: "error",
        message: "Choose a fresh destination.",
        dependency: null,
      },
    ],
    can_import: false,
  });
  const apply = vi.spyOn(workflowBundles, "import");
  render(
    <WorkflowBundleDialog
      document={document}
      sessionId="session"
      onClose={vi.fn()}
      onImported={vi.fn()}
    />,
  );
  upload();
  await waitFor(() =>
    expect(screen.getByTestId("workflow-transfer-inspect")).not.toBeDisabled(),
  );
  fireEvent.click(screen.getByTestId("workflow-transfer-inspect"));
  await screen.findByText("Import needs correction");
  const findings = screen.getAllByTestId("workflow-transfer-diagnostic");
  expect(findings).toHaveLength(3);
  expect(within(findings[0]!).getByText("references/design.png")).toBeVisible();
  expect(findings[0]).toHaveTextContent(
    "Prepare this dependency before starting.",
  );
  expect(findings[0]).not.toHaveTextContent("external_dependency");
  expect(within(findings[1]!).getByText("thermal-analysis")).toBeVisible();
  expect(findings[1]).toHaveTextContent(
    "Qualify the local binding before running.",
  );
  expect(findings[2]).toHaveTextContent("Needs correction");
  expect(findings[2]).not.toHaveTextContent("For:");
  const details = screen.getByTestId(
    "workflow-transfer-dependencies-toggle",
  ).parentElement!;
  expect(details).not.toHaveAttribute("open");
  fireEvent.click(screen.getByTestId("workflow-transfer-dependencies-toggle"));
  expect(details).toHaveTextContent("external_dependency");
  expect(screen.getByTestId("workflow-transfer-import")).toBeDisabled();
  expect(apply).not.toHaveBeenCalled();
});
