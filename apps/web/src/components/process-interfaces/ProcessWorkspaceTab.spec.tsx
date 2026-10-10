import { fireEvent, render, screen, waitFor } from "@testing-library/react";
import { beforeEach, describe, expect, it, vi } from "vitest";
import type { CommonProcessViewProps } from "./CommonProcessView";
import { createProcessWorkspaceTab } from "../../services/process-workspace-tabs";
import { ProcessWorkspaceTab } from "./ProcessWorkspaceTab";
import type { InterfaceAuthoringPanelProps } from "./InterfaceAuthoringPanel";
import type { ProcessInterfaceViewProps } from "./ProcessInterfaceView";
import {
  authoringView,
  authoringUi,
  authoringRevision,
} from "../../../tests/fixtures/process-ui-authoring";
import { blankWorkflowSource } from "../../services/blank-workflow";

const mocks = vi.hoisted(() => ({
  createClient: vi.fn(),
  common: vi.fn(),
  upload: vi.fn(),
  createAuthoring: vi.fn(),
  authoring: vi.fn(),
  interfaceView: vi.fn(),
  readSource: vi.fn(),
}));
vi.mock("../../services/workspace-service", () => ({
  workspaceService: { getWorkspaceWorkflowSource: mocks.readSource },
}));
vi.mock("../../services/process-client", () => ({
  createWorkspaceProcessClient: mocks.createClient,
}));
vi.mock("../../services/process-ui-authoring", () => ({
  createInterfaceAuthoringClient: mocks.createAuthoring,
}));
vi.mock("./InterfaceAuthoringPanel", () => ({
  InterfaceAuthoringPanel: (props: InterfaceAuthoringPanelProps) => {
    mocks.authoring(props);
    return <div data-testid="authoring-host-fixture" />;
  },
}));
vi.mock("./ProcessInterfaceView", () => ({
  ProcessInterfaceView: (props: ProcessInterfaceViewProps) => {
    mocks.interfaceView(props);
    return <button onClick={props.onUseCommon}>Use common fixture</button>;
  },
}));
vi.mock("./CommonProcessView", () => ({
  CommonProcessView: (props: CommonProcessViewProps) => {
    mocks.common(props);
    return (
      <div data-testid="common-view-host-fixture">
        <button onClick={() => props.onRunAttached?.("accepted-run")}>
          Attach fixture run
        </button>
        <button onClick={() => props.onPrepareAnother?.()}>
          Prepare another fixture
        </button>
      </div>
    );
  },
}));

const process = {
  workspace_id: "workspace-one",
  source_path: "workflows/one.workflow.wflow",
  source_digest: "a".repeat(64),
};
const tab = createProcessWorkspaceTab(process, { viewId: "view-one" });
const lastCommon = () =>
  mocks.common.mock.calls.at(-1)![0] as CommonProcessViewProps;

describe("trusted process tab host", () => {
  beforeEach(() => {
    vi.clearAllMocks();
    mocks.readSource.mockResolvedValue(undefined);
    mocks.createAuthoring.mockImplementation((process) => ({ process }));
    mocks.createClient.mockImplementation((options) => ({
      process: options.process,
      uploadInput: mocks.upload,
    }));
  });

  it("uses the accepted workflow title for presentation without starting or attaching a run", async () => {
    mocks.readSource.mockResolvedValue({
      workspace_id: process.workspace_id,
      path: process.source_path,
      storage_digest: process.source_digest,
      source: blankWorkflowSource("Focus-wheel design review"),
    });
    const onRunAttached = vi.fn(),
      onPrepareAnother = vi.fn();
    render(
      <ProcessWorkspaceTab
        tab={tab}
        sessionId="session"
        onRunAttached={onRunAttached}
        onPrepareAnother={onPrepareAnother}
      />,
    );
    await waitFor(() =>
      expect(lastCommon().title).toBe("Focus-wheel design review"),
    );
    expect(mocks.readSource).toHaveBeenCalledExactlyOnceWith(
      "session",
      process.source_path,
    );
    expect(onRunAttached).not.toHaveBeenCalled();
    expect(onPrepareAnother).not.toHaveBeenCalled();
  });

  it.each(["workspace", "path", "revision"])(
    "does not use title metadata from another %s",
    async (mismatch) => {
      mocks.readSource.mockResolvedValue({
        workspace_id:
          mismatch === "workspace" ? "elsewhere" : process.workspace_id,
        path:
          mismatch === "path" ? "workflows/other.wflow" : process.source_path,
        storage_digest:
          mismatch === "revision" ? "b".repeat(64) : process.source_digest,
        source: blankWorkflowSource("Wrong revision title"),
      });
      render(
        <ProcessWorkspaceTab
          tab={tab}
          sessionId="session"
          onRunAttached={vi.fn()}
          onPrepareAnother={vi.fn()}
        />,
      );
      await waitFor(() => expect(mocks.readSource).toHaveBeenCalled());
      expect(lastCommon().title).toBe(tab.name);
    },
  );

  it("binds the common view to the host session and saved source without a mount action", () => {
    const onRunAttached = vi.fn();
    const onPrepareAnother = vi.fn();
    render(
      <ProcessWorkspaceTab
        tab={tab}
        sessionId="host-session"
        onRunAttached={onRunAttached}
        onPrepareAnother={onPrepareAnother}
      />,
    );
    expect(mocks.createClient).toHaveBeenCalledExactlyOnceWith({
      process,
      sessionId: "host-session",
      navigate: expect.any(Function),
    });
    expect(lastCommon().runId).toBeUndefined();
    expect(lastCommon().sessionId).toBe("host-session");
    expect(onRunAttached).not.toHaveBeenCalled();
    expect(onPrepareAnother).not.toHaveBeenCalled();
  });

  it("memoizes the client across equivalent restored metadata and run attachment", () => {
    const callbacks = { onRunAttached: vi.fn(), onPrepareAnother: vi.fn() };
    const view = render(
      <ProcessWorkspaceTab tab={tab} sessionId="session" {...callbacks} />,
    );
    const client = lastCommon().client;
    view.rerender(
      <ProcessWorkspaceTab
        tab={{
          ...tab,
          processView: {
            ...tab.processView,
            process: { ...process },
            run_id: "run-one",
          },
        }}
        sessionId="session"
        {...callbacks}
      />,
    );
    expect(lastCommon().client).toBe(client);
    expect(lastCommon().runId).toBe("run-one");
    expect(mocks.createClient).toHaveBeenCalledTimes(1);
  });

  it("rebinds the client when the host session or source revision changes", () => {
    const callbacks = { onRunAttached: vi.fn(), onPrepareAnother: vi.fn() };
    const view = render(
      <ProcessWorkspaceTab tab={tab} sessionId="session-one" {...callbacks} />,
    );
    const client = lastCommon().client;
    view.rerender(
      <ProcessWorkspaceTab tab={tab} sessionId="session-two" {...callbacks} />,
    );
    expect(lastCommon().client).not.toBe(client);
    const second = lastCommon().client;
    view.rerender(
      <ProcessWorkspaceTab
        tab={{
          ...tab,
          processView: {
            ...tab.processView,
            process: { ...process, source_digest: "b".repeat(64) },
          },
        }}
        sessionId="session-two"
        {...callbacks}
      />,
    );
    expect(lastCommon().client).not.toBe(second);
  });

  it("routes exact attachment and explicit preparation through the native host", () => {
    const onRunAttached = vi.fn();
    const onPrepareAnother = vi.fn();
    render(
      <ProcessWorkspaceTab
        tab={tab}
        sessionId="session"
        onRunAttached={onRunAttached}
        onPrepareAnother={onPrepareAnother}
      />,
    );
    fireEvent.click(screen.getByText("Attach fixture run"));
    expect(onRunAttached).toHaveBeenCalledExactlyOnceWith(
      tab.path,
      process,
      "accepted-run",
    );
    fireEvent.click(screen.getByText("Prepare another fixture"));
    expect(onPrepareAnother).toHaveBeenCalledExactlyOnceWith(process);
  });

  it("opens the workflow through the current workspace callback", () => {
    const onOpenDefinition = vi.fn();
    render(
      <ProcessWorkspaceTab
        tab={tab}
        sessionId="session"
        onRunAttached={vi.fn()}
        onPrepareAnother={vi.fn()}
        onOpenDefinition={onOpenDefinition}
      />,
    );
    fireEvent.click(screen.getByRole("button", { name: "Open workflow" }));
    expect(onOpenDefinition).toHaveBeenCalledExactlyOnceWith(process);
  });

  it("provides scoped uploads and representations while undeclared navigation stays unavailable", () => {
    render(
      <ProcessWorkspaceTab
        tab={tab}
        sessionId="session"
        onRunAttached={vi.fn()}
        onPrepareAnother={vi.fn()}
      />,
    );
    expect(lastCommon().canReadRepresentations).toBe(true);
    expect(lastCommon().canNavigate).toBe(false);
    expect(lastCommon().onUpload).toBeTypeOf("function");
  });
  it("uses the declared input identifier for uploads through the stable scoped client", async () => {
    render(
      <ProcessWorkspaceTab
        tab={tab}
        sessionId="session"
        onRunAttached={vi.fn()}
        onPrepareAnother={vi.fn()}
      />,
    );
    const file = new File(["data"], "requirements.txt");
    await lastCommon().onUpload!(file, {
      input_id: "requirements",
      title: "Requirements",
      required: true,
      binding_kind: "file",
      block_id: "requirements",
      port_id: "out",
      value_schema: {},
    });
    expect(mocks.upload).toHaveBeenCalledExactlyOnceWith("requirements", file);
    expect(mocks.createClient).toHaveBeenCalledTimes(1);
  });
  it("routes authorized navigation through the current host without replacing the client", async () => {
    const first = vi.fn(async () => undefined),
      next = vi.fn(async () => undefined);
    const callbacks = { onRunAttached: vi.fn(), onPrepareAnother: vi.fn() };
    const view = render(
      <ProcessWorkspaceTab
        tab={tab}
        sessionId="session"
        {...callbacks}
        onNavigate={first}
      />,
    );
    const client = lastCommon().client;
    const resolution = {
      process,
      target: { kind: "block" as const, block_id: "geometry" },
    };
    const options = mocks.createClient.mock.calls[0][0];
    await options.navigate(process, resolution.target, resolution);
    expect(first).toHaveBeenCalledExactlyOnceWith(process, resolution);
    view.rerender(
      <ProcessWorkspaceTab
        tab={tab}
        sessionId="session"
        {...callbacks}
        onNavigate={next}
      />,
    );
    expect(lastCommon().client).toBe(client);
    await options.navigate(process, resolution.target, resolution);
    expect(next).toHaveBeenCalledExactlyOnceWith(process, resolution);
    expect(first).toHaveBeenCalledTimes(1);
    expect(lastCommon().canNavigate).toBe(true);
    expect(mocks.createClient).toHaveBeenCalledTimes(1);
  });

  it("opening authoring controls does not open a preview or invoke generation", async () => {
    const onOpenInterface = vi.fn();
    render(
      <ProcessWorkspaceTab
        tab={tab}
        sessionId="session"
        onRunAttached={vi.fn()}
        onPrepareAnother={vi.fn()}
        onOpenInterface={onOpenInterface}
      />,
    );
    expect(
      screen.queryByTestId("authoring-host-fixture"),
    ).not.toBeInTheDocument();
    expect(
      screen.getByRole("button", { name: "Create or choose interface" }),
    ).toHaveAttribute("aria-expanded", "false");
    fireEvent.click(
      screen.getByRole("button", { name: "Create or choose interface" }),
    );
    expect(
      screen.getByRole("button", { name: "Hide interface controls" }),
    ).toHaveAttribute("aria-expanded", "true");
    expect(screen.getByTestId("authoring-host-fixture")).toBeInTheDocument();
    expect(onOpenInterface).not.toHaveBeenCalled();
    expect(mocks.createAuthoring).toHaveBeenCalledExactlyOnceWith(
      process,
      "session",
    );
    const props = mocks.authoring.mock.calls.at(
      -1,
    )![0] as InterfaceAuthoringPanelProps;
    await props.onOpenPreview(authoringView);
    expect(onOpenInterface).toHaveBeenCalledWith(
      process,
      {
        kind: "preview",
        ui_id: authoringUi.ui_id,
        revision_id: authoringRevision.manifest.revision_id,
        job_id: authoringView.job.job_id,
      },
      authoringUi.title,
      undefined,
    );
    await props.onOpenSaved(authoringUi, authoringRevision);
    expect(onOpenInterface).toHaveBeenLastCalledWith(
      process,
      {
        kind: "working",
        ui_id: authoringUi.ui_id,
        revision_id: authoringRevision.manifest.revision_id,
      },
      authoringUi.title,
      undefined,
    );
  });

  it("switching to the common view keeps the same source and run in the existing tab", () => {
    const locator = {
      kind: "working" as const,
      ui_id: authoringUi.ui_id,
      revision_id: authoringRevision.manifest.revision_id,
    };
    const saved = createProcessWorkspaceTab(process, {
      viewId: "view-saved",
      runId: "recorded-run",
      interface: locator,
    });
    render(
      <ProcessWorkspaceTab
        tab={saved}
        sessionId="session"
        onRunAttached={vi.fn()}
        onPrepareAnother={vi.fn()}
        onOpenInterface={vi.fn()}
      />,
    );
    expect(
      screen.queryByTestId("common-view-host-fixture"),
    ).not.toBeInTheDocument();
    const props = mocks.interfaceView.mock.calls.at(
      -1,
    )![0] as ProcessInterfaceViewProps;
    expect(props.locator).toEqual(locator);
    expect(props.runId).toBe("recorded-run");
    fireEvent.click(screen.getByText("Use common fixture"));
    expect(lastCommon().client.process).toEqual(process);
    expect(lastCommon().runId).toBe("recorded-run");
    fireEvent.click(
      screen.getByRole("button", { name: "Return to interface" }),
    );
    expect(
      screen.queryByTestId("common-view-host-fixture"),
    ).not.toBeInTheDocument();
  });

  it("restores preview controls with the locator's job and UI identity", () => {
    const locator = {
      kind: "preview" as const,
      ui_id: authoringUi.ui_id,
      revision_id: authoringRevision.manifest.revision_id,
      job_id: authoringView.job.job_id,
    };
    const preview = createProcessWorkspaceTab(process, {
      viewId: "view-preview",
      runId: "recorded-run",
      interface: locator,
    });
    render(
      <ProcessWorkspaceTab
        tab={preview}
        sessionId="session"
        onRunAttached={vi.fn()}
        onPrepareAnother={vi.fn()}
        onOpenInterface={vi.fn()}
      />,
    );
    fireEvent.click(
      screen.getByRole("button", { name: "Create or choose interface" }),
    );
    const props = mocks.authoring.mock.calls.at(
      -1,
    )![0] as InterfaceAuthoringPanelProps;
    expect(props.initialUiId).toBe(locator.ui_id);
    expect(props.initialJobId).toBe(locator.job_id);
  });
});
