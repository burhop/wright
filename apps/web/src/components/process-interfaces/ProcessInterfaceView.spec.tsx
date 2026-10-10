import { StrictMode } from "react";
import {
  act,
  fireEvent,
  render,
  screen,
  waitFor,
} from "@testing-library/react";
import { describe, expect, it, vi } from "vitest";
import { ProcessClientError } from "@wright/process-client";
import type {
  InterfaceAuthoringClient,
  ProcessInterfacePresentation,
} from "../../services/process-ui-authoring";
import type { LiveAppSurfaceProps } from "../surfaces/LiveAppSurface";
import { ProcessInterfaceView } from "./ProcessInterfaceView";
import {
  authoringProcess as process,
  authoringUiId as ui_id,
  authoringRevisionId as revision_id,
  authoringView as built,
  authoringPresentation as presentation,
} from "../../../tests/fixtures/process-ui-authoring";

const surface = vi.hoisted(() => vi.fn());
vi.mock("../surfaces/LiveAppSurface", () => ({
  LiveAppSurface: (props: LiveAppSurfaceProps) => {
    surface(props);
    return <div data-testid="issued-interface-fixture" />;
  },
}));
function fixture() {
  const client = {
    process,
    compatibility: vi.fn<InterfaceAuthoringClient["compatibility"]>(
      async () => ({
        ui_id,
        revision_id,
        current_process: process,
        state: "compatible",
      }),
    ),
    present: vi.fn<InterfaceAuthoringClient["present"]>(
      async () => presentation,
    ),
    preview: vi.fn<InterfaceAuthoringClient["preview"]>(async () => ({
      ...presentation,
      binding: { ...presentation.binding, read_only: true },
    })),
    getJob: vi.fn<InterfaceAuthoringClient["getJob"]>(async () => built),
    close: vi.fn<InterfaceAuthoringClient["close"]>(async () => {}),
    capabilities: vi.fn(),
    interfaces: vi.fn(),
    importedInterfaces: vi.fn(),
    revisions: vi.fn(),
    submit: vi.fn(),
    cancel: vi.fn(),
    save: vi.fn(),
    activate: vi.fn(),
    startReceipt: vi.fn(async () => null),
  } satisfies InterfaceAuthoringClient;
  const props = {
    client,
    locator: { kind: "working" as const, ui_id, revision_id },
    sessionId: "session",
    viewId: "view",
    onUseCommon: vi.fn(),
  };
  return { client, props };
}
const flushClose = () =>
  act(async () => {
    await new Promise((resolve) => setTimeout(resolve, 5));
  });

describe("native process interface view lifetime", () => {
  it.each(["working", "preview"] as const)(
    "a restored %s locator for a removed interface retains common fallback without execution",
    async (kind) => {
      const f = fixture();
      const missing = new ProcessClientError({
        code: "UI_INCOMPATIBLE",
        message: "This saved interface is no longer available.",
        correction: "Use the common working view.",
      });
      f.client.compatibility.mockRejectedValue(missing);
      f.client.getJob.mockRejectedValue(missing);
      const view = render(
        <ProcessInterfaceView
          {...f.props}
          runId="run-one"
          locator={
            kind === "preview"
              ? { kind, ui_id, revision_id, job_id: "job-one" }
              : f.props.locator
          }
        />,
      );
      await screen.findByText(missing.reason.message);
      expect(
        screen.queryByTestId("issued-interface-fixture"),
      ).not.toBeInTheDocument();
      fireEvent.click(
        screen.getByRole("button", { name: "Use common working view" }),
      );
      expect(f.props.onUseCommon).toHaveBeenCalledOnce();
      expect(f.client.present).not.toHaveBeenCalled();
      expect(f.client.preview).not.toHaveBeenCalled();
      expect(f.client.submit).not.toHaveBeenCalled();
      expect(f.client.cancel).not.toHaveBeenCalled();
      view.unmount();
      await flushClose();
      expect(f.client.close).not.toHaveBeenCalled();
    },
  );
  it.each(["working", "preview"] as const)(
    "page departure closes only the exact %s presentation once",
    async (kind) => {
      const f = fixture(),
        view = render(
          <StrictMode>
            <ProcessInterfaceView
              {...f.props}
              locator={
                kind === "preview"
                  ? { kind, ui_id, revision_id, job_id: "job-one" }
                  : f.props.locator
              }
            />
          </StrictMode>,
        );
      await screen.findByTestId("issued-interface-fixture");
      const expected =
        kind === "preview"
          ? {
              ...presentation,
              binding: { ...presentation.binding, read_only: true },
            }
          : presentation;
      act(() =>
        window.dispatchEvent(
          new PageTransitionEvent("pagehide", { persisted: false }),
        ),
      );
      expect(f.client.close).toHaveBeenCalledExactlyOnceWith(expected, {
        keepalive: true,
      });
      act(() =>
        window.dispatchEvent(
          new PageTransitionEvent("pagehide", { persisted: false }),
        ),
      );
      view.unmount();
      await flushClose();
      expect(f.client.close).toHaveBeenCalledTimes(1);
      expect(f.client.submit).not.toHaveBeenCalled();
      expect(f.client.cancel).not.toHaveBeenCalled();
    },
  );

  it("does not revoke a view retained in the browser's back-forward cache", async () => {
    const f = fixture(),
      view = render(<ProcessInterfaceView {...f.props} />);
    await screen.findByTestId("issued-interface-fixture");
    act(() =>
      window.dispatchEvent(
        new PageTransitionEvent("pagehide", { persisted: true }),
      ),
    );
    expect(f.client.close).not.toHaveBeenCalled();
    expect(screen.getByTestId("issued-interface-fixture")).toBeVisible();
    view.unmount();
    await flushClose();
    expect(f.client.close).toHaveBeenCalledExactlyOnceWith(presentation);
  });

  it("releases a late opening reply after departure without mounting it or duplicating cleanup", async () => {
    const f = fixture();
    let resolve!: (value: ProcessInterfacePresentation) => void;
    f.client.present.mockImplementation(
      () =>
        new Promise((done) => {
          resolve = done;
        }),
    );
    const view = render(<ProcessInterfaceView {...f.props} />);
    await waitFor(() => expect(f.client.present).toHaveBeenCalledTimes(1));
    act(() =>
      window.dispatchEvent(
        new PageTransitionEvent("pagehide", { persisted: false }),
      ),
    );
    expect(f.client.close).not.toHaveBeenCalled();
    await act(async () => resolve(presentation));
    expect(f.client.close).toHaveBeenCalledExactlyOnceWith(presentation, {
      keepalive: true,
    });
    expect(
      screen.queryByTestId("issued-interface-fixture"),
    ).not.toBeInTheDocument();
    view.unmount();
    await flushClose();
    expect(f.client.close).toHaveBeenCalledTimes(1);
  });

  it("reports departure cleanup failure without cancelling or restarting the run", async () => {
    const f = fixture(),
      failure = vi.fn();
    f.client.close.mockRejectedValue(new Error("unavailable"));
    window.addEventListener("wright-process-ui-close-failed", failure);
    const view = render(<ProcessInterfaceView {...f.props} />);
    try {
      await screen.findByTestId("issued-interface-fixture");
      await act(async () =>
        window.dispatchEvent(
          new PageTransitionEvent("pagehide", { persisted: false }),
        ),
      );
      expect(failure).toHaveBeenCalledTimes(1);
      expect((failure.mock.calls[0][0] as CustomEvent).detail).toEqual({
        viewId: "view",
      });
      expect(f.client.submit).not.toHaveBeenCalled();
      expect(f.client.cancel).not.toHaveBeenCalled();
    } finally {
      view.unmount();
      await flushClose();
      window.removeEventListener("wright-process-ui-close-failed", failure);
    }
  });

  it("opens one issued view across StrictMode and closing does not submit or cancel work", async () => {
    const f = fixture(),
      view = render(
        <StrictMode>
          <ProcessInterfaceView {...f.props} />
        </StrictMode>,
      );
    await screen.findByTestId("issued-interface-fixture");
    expect(f.client.present).toHaveBeenCalledTimes(1);
    expect(f.client.compatibility).toHaveBeenCalledExactlyOnceWith(
      ui_id,
      revision_id,
    );
    expect(f.client.present).toHaveBeenCalledWith(
      ui_id,
      revision_id,
      expect.stringMatching(/^presentation-/),
      undefined,
    );
    expect(f.client.close).not.toHaveBeenCalled();
    const mounted = surface.mock.calls.at(-1)![0] as LiveAppSurfaceProps;
    expect(mounted.managedPresentation?.launch).toBe(presentation.launch);
    expect(mounted.managedPresentation?.closeOnUnmount).toBe(false);
    view.unmount();
    await flushClose();
    expect(f.client.close).toHaveBeenCalledExactlyOnceWith(presentation);
    expect(f.client.submit).not.toHaveBeenCalled();
    expect(f.client.cancel).not.toHaveBeenCalled();
  });

  it("closes a late open reply after the tab has closed", async () => {
    const f = fixture();
    let resolve!: (value: ProcessInterfacePresentation) => void;
    f.client.present.mockImplementation(
      () =>
        new Promise((done) => {
          resolve = done;
        }),
    );
    const view = render(<ProcessInterfaceView {...f.props} />);
    await waitFor(() => expect(f.client.present).toHaveBeenCalledTimes(1));
    view.unmount();
    await flushClose();
    await act(async () => resolve(presentation));
    expect(f.client.close).toHaveBeenCalledExactlyOnceWith(presentation);
  });

  it("preview opens only its verified job revision and retains exact attached run context", async () => {
    const f = fixture(),
      view = render(
        <ProcessInterfaceView
          {...f.props}
          runId="run-one"
          locator={{ kind: "preview", ui_id, revision_id, job_id: "job-one" }}
        />,
      );
    await screen.findByTestId("issued-interface-fixture");
    expect(f.client.getJob).toHaveBeenCalledExactlyOnceWith("job-one");
    expect(f.client.preview).toHaveBeenCalledWith(
      "job-one",
      expect.stringMatching(/^presentation-/),
      "run-one",
    );
    expect(f.client.present).not.toHaveBeenCalled();
    view.unmount();
    await flushClose();
  });

  it("a preview job for another revision cannot be opened", async () => {
    const f = fixture();
    f.client.getJob.mockResolvedValue({
      ...built,
      preview: {
        ...built.preview!,
        manifest: {
          ...built.preview!.manifest,
          revision_id: "revision-" + "c".repeat(32),
        },
      },
    });
    const view = render(
      <ProcessInterfaceView
        {...f.props}
        locator={{ kind: "preview", ui_id, revision_id, job_id: "job-one" }}
      />,
    );
    await screen.findByRole("alert");
    expect(f.client.preview).not.toHaveBeenCalled();
    view.unmount();
    await flushClose();
    expect(f.client.close).not.toHaveBeenCalled();
  });

  it("incompatible bindings retain the common view without opening an app", async () => {
    const f = fixture();
    f.client.compatibility.mockResolvedValue({
      ui_id,
      revision_id,
      current_process: process,
      state: "incompatible",
      reasons: [
        {
          code: "UI_INCOMPATIBLE",
          message: "Required result changed",
          correction: "Update the interface",
        },
      ],
    });
    const view = render(<ProcessInterfaceView {...f.props} />);
    await screen.findByText("Required result changed");
    fireEvent.click(
      screen.getByRole("button", { name: "Use common working view" }),
    );
    expect(f.props.onUseCommon).toHaveBeenCalledOnce();
    expect(f.client.present).not.toHaveBeenCalled();
    view.unmount();
    await flushClose();
  });

  it("changing run context replaces presentation only, with no new model or process request", async () => {
    const f = fixture(),
      view = render(<ProcessInterfaceView {...f.props} />);
    await screen.findByTestId("issued-interface-fixture");
    view.rerender(<ProcessInterfaceView {...f.props} runId="run-two" />);
    await waitFor(() => expect(f.client.present).toHaveBeenCalledTimes(2));
    await flushClose();
    expect(f.client.present.mock.calls[1]).toEqual([
      ui_id,
      revision_id,
      expect.any(String),
      "run-two",
    ]);
    expect(f.client.present.mock.calls[1][2]).not.toBe(
      f.client.present.mock.calls[0][2],
    );
    expect(f.client.close).toHaveBeenCalledTimes(1);
    expect(f.client.submit).not.toHaveBeenCalled();
    view.unmount();
    await flushClose();
    expect(f.client.close).toHaveBeenCalledTimes(2);
  });
});
