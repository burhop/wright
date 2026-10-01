import { act, fireEvent, render, screen, waitFor } from "@testing-library/react";
import { describe, expect, it, vi } from "vitest";
import { ProcessClientError } from "@wright/process-client";
import { InterfaceAuthoringPanel } from "./InterfaceAuthoringPanel";
import type { InterfaceAuthoringClient } from "../../services/process-ui-authoring";
import type { InterfaceAuthoringIntent } from "../../services/process-ui-authoring-recovery";
import {authoringProcess as process, authoringCapabilities as capabilities, authoringJob as job, authoringView as built,
  authoringUi as ui, authoringRevision as revision, authoringNow as now} from "../../../tests/fixtures/process-ui-authoring";

function fixture(initial: InterfaceAuthoringIntent | null = null) {
  const client = {
    process, capabilities: vi.fn(async () => capabilities), interfaces: vi.fn(async () => [ui]),
    revisions: vi.fn(async () => [revision]), compatibility: vi.fn(async () => ({ui_id: ui.ui_id, revision_id: revision.manifest.revision_id, current_process: process, state: "compatible" as const})),
    submit: vi.fn<InterfaceAuthoringClient["submit"]>(async () => job), getJob: vi.fn(async () => built), cancel: vi.fn(async () => ({...job, state: "cancelled" as const})),
    save: vi.fn(async () => revision), activate: vi.fn(async () => ui), preview: vi.fn(), present: vi.fn(), close: vi.fn(), startReceipt: vi.fn(),
  } satisfies InterfaceAuthoringClient;
  let retained = initial;
  const store = {read: vi.fn(() => retained), write: vi.fn((value: InterfaceAuthoringIntent) => {retained = value;}), clear: vi.fn(() => {retained = null;})};
  const onOpenPreview = vi.fn(async () => {}), onOpenSaved = vi.fn(async () => {});
  const element = <InterfaceAuthoringPanel client={client} sessionId="session" viewId="view" recoveryStore={store}
    onOpenPreview={onOpenPreview} onOpenSaved={onOpenSaved}/>;
  return {client, store, onOpenPreview, onOpenSaved, element};
}
async function ready() {await waitFor(() => expect(screen.getByRole("option", {name: "Results comparison"})).toBeInTheDocument());}
function describeInterface() {
  fireEvent.change(screen.getByLabelText("How should this interface help the user?"), {target: {value: "Compare outputs and highlight findings"}});
}
const intent: InterfaceAuthoringIntent = {version: "1", process, request: {request_id: "retained-request", instruction: "Compare exact results", title: "Comparison"}};

describe("native interface authoring controls", () => {
  it("creates through Wright, shows progress and enables save only after owner preview observation", async () => {
    const f = fixture(), view = render(f.element);
    await ready(); describeInterface();
    fireEvent.click(screen.getByRole("button", {name: "Create interface"}));
    await screen.findByRole("heading", {name: "Preview ready"});
    expect(f.store.write.mock.calls[0][0].request.request_id).toEqual(f.client.submit.mock.calls[0][0].request_id);
    expect(screen.getByRole("button", {name: "Save interface"})).toBeDisabled();
    fireEvent.click(screen.getByRole("button", {name: "Open preview"}));
    await waitFor(() => expect(f.onOpenPreview).toHaveBeenCalledWith(built));
    f.client.getJob.mockResolvedValue({...built, preview: {...built.preview!, previewed_at: now}});
    fireEvent.click(screen.getByRole("button", {name: "Refresh interfaces"}));
    await waitFor(() => expect(screen.getByRole("button", {name: "Save interface"})).toBeEnabled());
    fireEvent.click(screen.getByRole("button", {name: "Save interface"}));
    await waitFor(() => expect(f.client.save).toHaveBeenCalledWith(expect.objectContaining({job}), null));
    expect(f.client.submit).toHaveBeenCalledTimes(1);
    view.unmount(); expect(f.client.cancel).not.toHaveBeenCalled();
  });

  it("reopening a known job observes it without model generation or cancellation", async () => {
    const f = fixture({...intent, job_id: "job-one"}), view = render(f.element);
    await screen.findByRole("heading", {name: "Preview ready"});
    expect(f.client.getJob).toHaveBeenCalledWith("job-one", expect.any(AbortSignal));
    expect(f.client.submit).not.toHaveBeenCalled();
    view.unmount(); expect(f.client.cancel).not.toHaveBeenCalled();
  });

  it("an uncertain request waits for explicit same-ID reconciliation", async () => {
    const f = fixture(intent), view = render(f.element);
    await ready();
    expect(f.client.submit).not.toHaveBeenCalled();
    expect(screen.getByRole("button", {name: "Create interface"})).toBeDisabled();
    fireEvent.click(screen.getByRole("button", {name: "Reconcile request"}));
    await screen.findByRole("heading", {name: "Preview ready"});
    expect(f.client.submit).toHaveBeenCalledExactlyOnceWith(intent.request);
    expect(f.store.write).toHaveBeenCalledWith({...intent, job_id: "job-one"});
    view.unmount();
  });

  it("a dropped creation reply preserves the request and does not retry automatically", async () => {
    const f = fixture(); f.client.submit.mockRejectedValueOnce(new Error("Reply lost"));
    const view = render(f.element); await ready(); describeInterface();
    fireEvent.click(screen.getByRole("button", {name: "Create interface"}));
    await screen.findByRole("button", {name: "Reconcile request"});
    const request = f.client.submit.mock.calls[0][0];
    expect(f.client.submit).toHaveBeenCalledTimes(1);
    fireEvent.click(screen.getByRole("button", {name: "Reconcile request"}));
    await screen.findByRole("heading", {name: "Preview ready"});
    expect(f.client.submit.mock.calls[1][0]).toEqual(request);
    view.unmount();
  });

  it("saved interfaces remain usable when authoring capability lookup fails", async () => {
    const f = fixture(); f.client.capabilities.mockRejectedValue(new Error("Model unavailable"));
    const view = render(f.element); await ready();
    fireEvent.change(screen.getByLabelText("Saved interface"), {target: {value: ui.ui_id}});
    await waitFor(() => expect(screen.getByRole("button", {name: "Open saved interface"})).toBeEnabled());
    fireEvent.click(screen.getByRole("button", {name: "Open saved interface"}));
    await waitFor(() => expect(f.onOpenSaved).toHaveBeenCalledWith(ui, revision));
    expect(f.client.submit).not.toHaveBeenCalled(); expect(f.client.save).not.toHaveBeenCalled();
    view.unmount();
  });

  it("incompatible saved bindings offer correction and do not open a working view", async () => {
    const f = fixture(); const reason = {code: "UI_INCOMPATIBLE", message: "Required input changed", correction: "Update the selected interface"};
    f.client.compatibility.mockResolvedValue({ui_id: ui.ui_id, revision_id: revision.manifest.revision_id, current_process: process,
      state: "incompatible", reasons: [reason]} as never);
    const view = render(f.element); await ready();
    fireEvent.change(screen.getByLabelText("Saved interface"), {target: {value: ui.ui_id}});
    await waitFor(() => expect(screen.getByRole("button", {name: "Open saved interface"})).toBeEnabled());
    fireEvent.click(screen.getByRole("button", {name: "Open saved interface"}));
    await screen.findByText("Required input changed");
    expect(f.onOpenSaved).not.toHaveBeenCalled();
    view.unmount();
  });

  it("updates the exact selected revision and records progress after explicit cancellation", async () => {
    const f = fixture(), view = render(f.element); await ready(); describeInterface();
    fireEvent.change(screen.getByLabelText("Saved interface"), {target: {value: ui.ui_id}});
    await waitFor(() => expect(screen.getByRole("button", {name: "Update selected interface"})).toBeEnabled());
    fireEvent.click(screen.getByRole("button", {name: "Update selected interface"}));
    await screen.findByRole("heading", {name: "Preview ready"});
    expect(f.client.submit).toHaveBeenCalledWith(expect.objectContaining({ui_id: ui.ui_id, base_revision: ui.active_revision}));
    f.client.getJob.mockResolvedValue({job: {...job, state: "cancelled"}, preview: null} as never);
    fireEvent.click(screen.getByRole("button", {name: "Cancel interface creation"}));
    await screen.findByRole("heading", {name: "Interface creation cancelled"});
    expect(f.client.cancel).toHaveBeenCalledExactlyOnceWith("job-one");
    view.unmount();
  });

  it("failed request persistence blocks generation and exposes an actionable recovery error", async () => {
    const f = fixture(); f.store.write.mockImplementation(() => {throw new ProcessClientError({code: "UI_INCOMPATIBLE",
      message: "Cannot retain the request locator", correction: "Restore local request storage"});});
    const view = render(f.element); await ready(); describeInterface();
    await act(async () => fireEvent.click(screen.getByRole("button", {name: "Create interface"})));
    await screen.findByText("Cannot retain the request locator");
    expect(f.client.submit).not.toHaveBeenCalled();
    view.unmount();
  });
});
