import { act, fireEvent, render, screen, waitFor } from "@testing-library/react";
import { describe, expect, it, vi } from "vitest";
import { ProcessClientError } from "@wright/process-client";
import { InterfaceAuthoringPanel } from "./InterfaceAuthoringPanel";
import type { InterfaceAuthoringClient } from "../../services/process-ui-authoring";
import type { InterfaceAuthoringIntent } from "../../services/process-ui-authoring-recovery";
import {authoringProcess as process, authoringCapabilities as capabilities, authoringJob as job, authoringView as built,
  authoringUi as ui, authoringRevision as revision, authoringNow as now} from "../../../tests/fixtures/process-ui-authoring";

function fixture(initial: InterfaceAuthoringIntent | null = null, initialJobId?: string) {
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
    initialUiId={initialJobId ? ui.ui_id : undefined} initialJobId={initialJobId}
    onOpenPreview={onOpenPreview} onOpenSaved={onOpenSaved}/>;
  return {client, store, onOpenPreview, onOpenSaved, element};
}
async function ready() {await waitFor(() => expect(screen.getByRole("option", {name: "Results comparison"})).toBeInTheDocument());}
function describeInterface() {
  fireEvent.change(screen.getByLabelText("How should this interface help the user?"), {target: {value: "Compare outputs and highlight findings"}});
}
const intent: InterfaceAuthoringIntent = {version: "1", process, request: {request_id: "retained-request", instruction: "Compare exact results", title: "Comparison"}};

describe("native interface authoring controls", () => {
  it("keeps the actual trace and request identity in creation details without generation", async () => {
    const f = fixture({...intent, job_id: job.job_id});
    f.client.getJob.mockResolvedValue({...built, trace_id: "trace-recorded-one"} as never);
    const view = render(f.element);
    const details = (await screen.findByText("Creation details")).closest("details");
    expect(details).not.toHaveAttribute("open");
    expect(details).toHaveTextContent("Trace: trace-recorded-one");
    expect(details).toHaveTextContent(`Request: ${job.request_id}`);
    expect(f.client.submit).not.toHaveBeenCalled();
    view.unmount();
    expect(f.client.cancel).not.toHaveBeenCalled();
  });

  it("discloses missing historical trace identity without guessing one", async () => {
    const f = fixture({...intent, job_id: job.job_id});
    const view = render(f.element);
    const details = (await screen.findByText("Creation details")).closest("details");
    expect(details).toHaveTextContent("Trace identity is unavailable for this record.");
    expect(f.client.submit).not.toHaveBeenCalled();
    view.unmount();
  });

  it.each([
    ["queued", "Waiting to create the interface"],
    ["resolving", "Preparing Wright's interface instructions"],
    ["generating", "Creating the interface"],
    ["validating", "Checking interface bindings"],
    ["building", "Building the preview"],
    ["preview_ready", "Preview ready"],
    ["saved", "Interface saved"],
    ["failed", "Interface needs attention"],
    ["cancelled", "Interface creation cancelled"],
  ] as const)("presents backend %s progress without submitting or replaying work", async (state, label) => {
    const f = fixture({...intent, job_id: job.job_id});
    const hasPreview = state === "preview_ready" || state === "saved";
    const diagnostics = state === "failed" ? [{code: "UI_INCOMPATIBLE", message: "Required result binding changed", correction: "Update the interface bindings"}] : [];
    f.client.getJob.mockResolvedValue({...built, job: {...job, state, diagnostics}, preview: hasPreview ? built.preview : null} as never);
    const view = render(f.element);
    const region = await screen.findByRole("region", {name: "Interface creation progress"});
    expect(region).toHaveAttribute("aria-live", "polite");
    expect(screen.getByRole("heading", {name: label})).toBeInTheDocument();
    if (state === "failed") {
      expect(screen.getByRole("alert")).toHaveTextContent("Required result binding changed");
      expect(screen.getByRole("alert")).toHaveTextContent("Update the interface bindings");
    }
    if (!hasPreview) expect(screen.queryByRole("button", {name: "Open preview"})).not.toBeInTheDocument();
    if (["saved", "failed", "cancelled"].includes(state)) {
      expect(screen.queryByRole("button", {name: "Cancel interface creation"})).not.toBeInTheDocument();
    } else {
      expect(screen.getByRole("button", {name: "Cancel interface creation"})).toBeEnabled();
      expect(screen.getByRole("button", {name: "Create interface"})).toBeDisabled();
    }
    expect(f.client.submit).not.toHaveBeenCalled();
    expect(f.client.save).not.toHaveBeenCalled();
    expect(f.client.cancel).not.toHaveBeenCalled();
    view.unmount();
    expect(f.client.cancel).not.toHaveBeenCalled();
  });

  it("keeps saved reuse available when declared creation capability is unavailable", async () => {
    const f = fixture();
    f.client.capabilities.mockResolvedValue({...capabilities, available: false, compiler_reason: {
      code: "CAPABILITY_UNAVAILABLE", message: "Interface creation is unavailable", correction: "Use a saved interface or configure authoring",
    }});
    const view = render(f.element);
    await ready(); describeInterface();
    expect(screen.getByRole("alert")).toHaveTextContent("Use a saved interface or configure authoring");
    expect(screen.getByRole("button", {name: "Create interface"})).toBeDisabled();
    fireEvent.change(screen.getByLabelText("Saved interface"), {target: {value: ui.ui_id}});
    await waitFor(() => expect(screen.getByRole("button", {name: "Open saved interface"})).toBeEnabled());
    expect(screen.getByRole("button", {name: "Update selected interface"})).toBeDisabled();
    fireEvent.click(screen.getByRole("button", {name: "Open saved interface"}));
    await waitFor(() => expect(f.onOpenSaved).toHaveBeenCalledExactlyOnceWith(ui, revision));
    expect(f.client.submit).not.toHaveBeenCalled();
    view.unmount();
  });

  it("refreshes a failed job observation without repeating generation", async () => {
    const f = fixture({...intent, job_id: job.job_id});
    f.client.getJob.mockRejectedValueOnce(new Error("Observer disconnected"));
    const view = render(f.element);
    await screen.findByRole("button", {name: "Refresh job status"});
    expect(screen.getByText(/The backend job keeps its own state/)).toBeInTheDocument();
    expect(f.client.submit).not.toHaveBeenCalled();
    fireEvent.click(screen.getByRole("button", {name: "Refresh job status"}));
    await screen.findByRole("heading", {name: "Preview ready"});
    expect(f.client.getJob).toHaveBeenCalledTimes(2);
    expect(f.client.submit).not.toHaveBeenCalled();
    expect(f.client.cancel).not.toHaveBeenCalled();
    view.unmount();
  });

  it("does not block available creation when the independent saved list fails", async () => {
    const f = fixture();
    f.client.interfaces.mockRejectedValue(new Error("Saved list unavailable"));
    const view = render(f.element);
    describeInterface();
    await screen.findByRole("alert");
    await waitFor(() => expect(screen.getByRole("button", {name: "Create interface"})).toBeEnabled());
    expect(f.client.submit).not.toHaveBeenCalled();
    view.unmount();
  });

  it("keeps exact field names independent of saved option text", async () => {
    const f = fixture(), view = render(f.element);
    await ready();
    expect(screen.getByRole("textbox", {name: "Interface title"})).toBe(screen.getByLabelText("Interface title", {exact: true}));
    expect(screen.getByRole("textbox", {name: "How should this interface help the user?"})).toBe(screen.getByLabelText("How should this interface help the user?", {exact: true}));
    const select = screen.getByRole("combobox", {name: "Saved interface"});
    expect(select).toBe(screen.getByLabelText("Saved interface", {exact: true}));
    fireEvent.change(select, {target: {value: ui.ui_id}});
    await waitFor(() => expect(screen.getByRole("combobox", {name: "Saved revision"})).toHaveValue(revision.manifest.revision_id));
    expect(screen.getByLabelText("Saved interface", {exact: true})).toBe(select);
    view.unmount();
  });
  it("shows creation readiness while a separate saved-interface read is pending", async () => {
    const f = fixture();
    let resolveSaved!: (value: (typeof ui)[]) => void;
    f.client.interfaces.mockImplementation(
      () =>
        new Promise((resolve) => {
          resolveSaved = resolve;
        }),
    );
    const view = render(f.element);
    expect(screen.getByRole("status")).toHaveTextContent(
      "Checking interface creation availability",
    );
    describeInterface();
    await waitFor(() =>
      expect(
        screen.getByRole("button", { name: "Create interface" }),
      ).toBeEnabled(),
    );
    expect(
      screen.queryByText("Checking interface creation availability…"),
    ).not.toBeInTheDocument();
    resolveSaved([ui]);
    await ready();
    view.unmount();
  });
  it("preserves a chosen earlier revision when a background refresh reports a new active revision", async () => {
    const f = fixture();
    const newer = {...revision, manifest: {...revision.manifest, revision_id: "revision-newer"}};
    f.client.revisions.mockResolvedValue([newer, revision]);
    const view = render(f.element); await ready();
    fireEvent.change(screen.getByLabelText("Saved interface"), {target: {value: ui.ui_id}});
    await waitFor(() => expect(screen.getByLabelText("Saved revision")).toHaveValue(revision.manifest.revision_id));
    f.client.interfaces.mockResolvedValue([{...ui, active_revision: newer.manifest.revision_id}]);
    fireEvent.click(screen.getByRole("button", {name: "Refresh interfaces"}));
    await waitFor(() => expect(screen.getByRole("button", {name: "Use this revision"})).toBeEnabled());
    expect(screen.getByLabelText("Saved revision")).toHaveValue(revision.manifest.revision_id);
    fireEvent.click(screen.getByRole("button", {name: "Use this revision"}));
    await waitFor(() => expect(f.client.activate).toHaveBeenCalledWith(ui.ui_id, revision.manifest.revision_id, newer.manifest.revision_id));
    view.unmount();
  });

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

  it("restores preview-tab save controls from its exact job without a local creation intent", async () => {
    const f = fixture(null, job.job_id);
    f.client.getJob.mockResolvedValue({...built, preview: {...built.preview!, previewed_at: now}});
    const view = render(f.element);
    await screen.findByRole("heading", {name: "Preview ready"});
    expect(screen.getByRole("button", {name: "Create interface"})).toBeDisabled();
    expect(screen.getByRole("button", {name: "Save interface"})).toBeEnabled();
    fireEvent.click(screen.getByRole("button", {name: "Save interface"}));
    await waitFor(() => expect(f.client.save).toHaveBeenCalledExactlyOnceWith(expect.objectContaining({job}), null));
    expect(f.client.getJob).toHaveBeenCalledWith(job.job_id, expect.any(AbortSignal));
    expect(f.client.submit).not.toHaveBeenCalled();
    expect(f.store.write).not.toHaveBeenCalled();
    view.unmount();
    expect(f.client.cancel).not.toHaveBeenCalled();
  });

  it("rejects a restored preview whose job identifies a different interface", async () => {
    const f = fixture(null, job.job_id);
    f.client.getJob.mockResolvedValue({...built, preview: {...built.preview!, manifest: {...built.preview!.manifest, ui_id: "ui-other"}}});
    const view = render(f.element);
    await screen.findByRole("alert");
    expect(screen.queryByRole("button", {name: "Save interface"})).not.toBeInTheDocument();
    expect(f.client.submit).not.toHaveBeenCalled();
    expect(f.client.save).not.toHaveBeenCalled();
    view.unmount();
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
