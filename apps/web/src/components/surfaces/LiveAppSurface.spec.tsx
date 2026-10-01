import { StrictMode } from "react";
import { act, fireEvent, render, screen } from "@testing-library/react";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";
import { LiveAppSurface } from "./LiveAppSurface";
import type { SurfaceDescriptor } from "../../services/surfaces/surface-contract";
import type { PresentationLaunch } from "../../services/surfaces/surface-client";

const mocks = vi.hoisted(() => ({create: vi.fn(), close: vi.fn(), preference: vi.fn(), operate: vi.fn(), external: vi.fn()}));
vi.mock("../../services/host-adapter", () => ({hostAdapter: {validateIssuedPreviewUrl: (value: string) => value, openExternal: mocks.external}}));
vi.mock("../../services/surfaces/surface-client", () => ({createPresentation: mocks.create, closePresentation: mocks.close,
  getPresentationPreference: mocks.preference, operateLiveApp: mocks.operate}));
vi.mock("../../services/surfaces/focus-manager", () => ({installElectronReturnAccelerator: () => () => {}}));
vi.mock("./LiveAppControls", () => ({LiveAppControls: () => <div data-testid="generic-runtime-controls"/>}));
vi.mock("./SurfaceToolbar", () => ({SurfaceToolbar: (props: {onOpen: (kind: string) => void}) =>
  <button onClick={() => props.onOpen("panel")}>Open generic panel</button>}));
const now = "2026-10-01T12:00:00Z";
const descriptor: SurfaceDescriptor = {schemaVersion: 1, surfaceId: "surface-one", workspaceId: "workspace",
  source: {kind: "live_app", sourceId: "process.ui-one.revision-one", sourceVersion: "a".repeat(64), manifestId: "process.ui-one.revision-one"},
  title: "Results", lifecycle: "ready", instance: {instanceId: "instance-one", generation: 1, sharing: "isolated"},
  presentations: [{kind: "panel", eligible: true}], capabilities: [], revision: 2, createdAt: now, updatedAt: now};
const launch: PresentationLaunch = {presentationId: "presentation-one", instanceId: "instance-one", generation: 1,
  kind: "panel", absoluteBootstrapUrl: "http://s-presentation-one.localhost:8000/bootstrap?token=issued", expiresAt: now};

describe("existing presenter with native-owned process presentation", () => {
  beforeEach(() => {vi.clearAllMocks(); vi.useFakeTimers(); mocks.preference.mockResolvedValue({remembered: false, kind: "panel"});
    mocks.create.mockResolvedValue(launch); mocks.close.mockResolvedValue(undefined);});
  afterEach(() => {vi.runOnlyPendingTimers(); vi.useRealTimers();});

  it("mounts the exact native launch and skips generic preferences, grants and runtime commands", () => {
    const close = vi.fn(async () => {}), connect = vi.fn(() => vi.fn());
    const view = render(<LiveAppSurface descriptor={descriptor} sessionId="native-session" onFocusMode={() => {}}
      managedPresentation={{launch, close, connect}}/>);
    const frame = view.container.querySelector("iframe")!;
    expect(frame.src).toBe(launch.absoluteBootstrapUrl);
    expect(frame.getAttribute("sandbox")).toBe("allow-scripts allow-forms allow-same-origin");
    expect(connect).toHaveBeenCalledWith(frame, expect.any(Function));
    expect(mocks.preference).not.toHaveBeenCalled();
    expect(mocks.create).not.toHaveBeenCalled();
    expect(mocks.operate).not.toHaveBeenCalled();
    expect(screen.queryByTestId("generic-runtime-controls")).not.toBeInTheDocument();
    view.unmount();
    act(() => vi.runOnlyPendingTimers());
    expect(close).toHaveBeenCalledTimes(1);
    expect(mocks.close).not.toHaveBeenCalled();
  });

  it("a StrictMode remount retains the issued view and real tab close disposes it once", () => {
    const close = vi.fn(async () => {}), disconnect = vi.fn();
    const view = render(<StrictMode><LiveAppSurface descriptor={descriptor} sessionId="native-session" onFocusMode={() => {}}
      managedPresentation={{launch, close, connect: () => disconnect}}/></StrictMode>);
    act(() => vi.advanceTimersByTime(1));
    expect(close).not.toHaveBeenCalled();
    expect(view.container.querySelectorAll("iframe")).toHaveLength(1);
    view.unmount();
    act(() => vi.advanceTimersByTime(1));
    expect(close).toHaveBeenCalledTimes(1);
    expect(disconnect).toHaveBeenCalledTimes(2);
  });

  it("leaves maximization to the workspace when no focus callback exists", () => {
    const view = render(<LiveAppSurface descriptor={descriptor} sessionId="native-session"
      managedPresentation={{launch, close: vi.fn(async () => {})}}/>);
    expect(screen.queryByTestId("surface-enter-focus")).not.toBeInTheDocument();
    view.unmount();
  });

  it("explicit close uses the process owner and contains its failure without generic fallback", async () => {
    const close = vi.fn(async () => {throw new Error("View cleanup needs reconciliation");});
    const view = render(<LiveAppSurface descriptor={descriptor} sessionId="native-session" onFocusMode={() => {}}
      managedPresentation={{launch, close}}/>);
    await act(async () => fireEvent.click(screen.getByText("Close interface view")));
    expect(screen.getByRole("alert")).toHaveTextContent("View cleanup needs reconciliation");
    expect(view.container.querySelector("iframe")).toBeInTheDocument();
    expect(mocks.close).not.toHaveBeenCalled();
    view.unmount();
  });

  it("preserves the ordinary managed app controls and native preference/create owner", async () => {
    const view = render(<LiveAppSurface descriptor={{...descriptor, source: {...descriptor.source, sourceId: "ordinary.app"}}}
      sessionId="session" onFocusMode={() => {}}/>);
    expect(screen.getByTestId("generic-runtime-controls")).toBeInTheDocument();
    await act(async () => fireEvent.click(screen.getByText("Open generic panel")));
    expect(mocks.preference).toHaveBeenCalledTimes(1);
    expect(mocks.create).toHaveBeenCalledWith("surface-one", "workspace", "session", "panel",
      {rememberPreference: false, isolatedAcknowledged: true});
    expect(view.container.querySelector("iframe")).toBeInTheDocument();
    view.unmount();
  });
});
