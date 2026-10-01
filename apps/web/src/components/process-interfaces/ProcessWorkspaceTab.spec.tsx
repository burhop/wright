import { fireEvent, render, screen } from "@testing-library/react";
import { beforeEach, describe, expect, it, vi } from "vitest";
import type { CommonProcessViewProps } from "./CommonProcessView";
import { createProcessWorkspaceTab } from "../../services/process-workspace-tabs";
import { ProcessWorkspaceTab } from "./ProcessWorkspaceTab";

const mocks = vi.hoisted(() => ({
  createClient: vi.fn(),
  common: vi.fn(),
  upload: vi.fn(),
}));
vi.mock("../../services/process-client", () => ({
  createWorkspaceProcessClient: mocks.createClient,
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
    mocks.createClient.mockImplementation((options) => ({
      process: options.process,
      uploadInput: mocks.upload,
    }));
  });

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
});
