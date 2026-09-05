import {
  fireEvent,
  render,
  screen,
  waitFor,
  cleanup,
} from "@testing-library/react";
import { MemoryRouter } from "react-router-dom";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";
import { NativeEditor } from "./NativeEditor";
import { contract, example, savedProcess } from "./native-process.fixture";
import { applyCommand } from "./model";
import {
  nativeProcessApi,
  nativeRunApi,
  NativeProcessError,
} from "../../services/native-process";
vi.mock("../../services/native-process", async (original) => {
  const actual =
    await original<typeof import("../../services/native-process")>();
  return {
    ...actual,
    nativeProcessApi: {
      contract: vi.fn(),
      examples: vi.fn(),
      list: vi.fn(),
      get: vi.fn(),
      create: vi.fn(),
      save: vi.fn(),
      check: vi.fn(),
    },
    nativeRunApi: { history: vi.fn(), get: vi.fn() },
  };
});
// These are mocked component journeys; real React Flow/browser evidence is separate.
vi.mock("./NativeCanvas", () => ({
  NativeCanvas: ({ document }: { document: typeof example }) => (
    <div data-testid="mocked-canvas">
      {document.definition.steps.map((step) => (
        <span key={step.id}>{step.id}</span>
      ))}
    </div>
  ),
}));
beforeEach(() => {
  vi.resetAllMocks();
  vi.mocked(nativeRunApi.history).mockResolvedValue({
    runs: [],
    next_cursor: null,
  });
  vi.mocked(nativeProcessApi.contract).mockResolvedValue(contract);
  vi.mocked(nativeProcessApi.examples).mockResolvedValue({
    examples: [{ ...example, id: "concept-brief", title: "Concept brief" }],
  });
  vi.mocked(nativeProcessApi.list).mockResolvedValue({
    documents: [],
    next_cursor: null,
  });
  vi.mocked(nativeProcessApi.check).mockResolvedValue({
    structurally_valid: true,
    ready: true,
    findings: [],
  });
});
afterEach(cleanup);
async function renderExample(onDirtyChange?: (dirty: boolean) => void) {
  render(
    <MemoryRouter>
      <NativeEditor sessionId="session-one" onDirtyChange={onDirtyChange} />
    </MemoryRouter>,
  );
  await screen.findByTestId("native-example-list");
  fireEvent.change(screen.getByTestId("native-example-list"), {
    target: { value: "concept-brief" },
  });
  fireEvent.click(screen.getByTestId("native-open-example"));
  return screen;
}
describe("mocked authoring journeys", () => {
  it("keeps an invalid artifact path buffered and the valid definition unchanged until corrected", async () => {
    sessionStorage.clear();
    const withInput = applyCommand(
      example,
      {
        type: "add-step",
        operation: "artifact.input@1",
        id: "file-input",
        title: "File input",
      },
      contract,
    );
    const configured = applyCommand(
      withInput,
      {
        type: "step",
        id: "file-input",
        title: "File input",
        config: { path: "safe.txt" },
      },
      contract,
    );
    vi.mocked(nativeProcessApi.examples).mockResolvedValue({
      examples: [
        { ...configured, id: "concept-brief", title: "Concept brief" },
      ],
    });
    await renderExample();
    fireEvent.change(screen.getByTestId("native-step-list"), {
      target: { value: "file-input" },
    });
    const originalSource = (
      screen.getByTestId("native-source") as HTMLTextAreaElement
    ).value;
    fireEvent.change(screen.getByTestId("native-config-path"), {
      target: { value: "../outside.txt" },
    });
    fireEvent.click(screen.getByTestId("native-apply-step"));
    expect(screen.getByRole("alert")).toHaveTextContent(
      "confined relative file path",
    );
    expect(screen.getByTestId("native-source")).toHaveValue(originalSource);
    expect(screen.getByTestId("native-save")).toBeDisabled();
    expect(screen.getByTestId("native-history-limit")).toHaveTextContent(
      "0 available to undo",
    );
    fireEvent.change(screen.getByTestId("native-step-list"), {
      target: { value: "need-source" },
    });
    fireEvent.change(screen.getByTestId("native-step-list"), {
      target: { value: "file-input" },
    });
    expect(screen.getByTestId("native-config-path")).toHaveValue(
      "../outside.txt",
    );
    expect(screen.getByTestId("native-discard-fields")).toBeInTheDocument();
    fireEvent.change(screen.getByTestId("native-config-path"), {
      target: { value: "folder/safe.txt" },
    });
    fireEvent.click(screen.getByTestId("native-apply-step"));
    expect(
      screen.queryByTestId("native-discard-fields"),
    ).not.toBeInTheDocument();
    expect(screen.getByTestId("native-history-limit")).toHaveTextContent(
      "1 available to undo",
    );
    fireEvent.click(screen.getByTestId("native-undo"));
    expect(screen.getByTestId("native-source")).toHaveValue(originalSource);
    expect(screen.getByTestId("native-config-path")).toHaveValue("safe.txt");
  });
  it("shows the session undo limit and available undo and redo counts", async () => {
    sessionStorage.clear();
    await renderExample();
    expect(screen.getByTestId("native-history-limit")).toHaveTextContent(
      "latest 100 changes in this session",
    );
    expect(screen.getByTestId("native-undo")).toHaveAccessibleDescription(
      /older changes are discarded/,
    );
    fireEvent.change(screen.getByTestId("native-process-title"), {
      target: { value: "Changed title" },
    });
    fireEvent.click(screen.getByTestId("native-apply-title"));
    expect(screen.getByTestId("native-history-limit")).toHaveTextContent(
      "1 available to undo · 0 available to redo",
    );
    fireEvent.click(screen.getByTestId("native-undo"));
    expect(screen.getByTestId("native-history-limit")).toHaveTextContent(
      "0 available to undo · 1 available to redo",
    );
    fireEvent.click(screen.getByTestId("native-redo"));
    expect(screen.getByTestId("native-history-limit")).toHaveTextContent(
      "1 available to undo · 0 available to redo",
    );
  });
  it.each(["newer-version", "read-failure"])(
    "retains recovery and retry identity when save confirmation has %s",
    async (outcome) => {
      sessionStorage.clear();
      const dirty = vi.fn();
      await renderExample(dirty);
      vi.mocked(nativeProcessApi.create).mockImplementation(
        async (_, document) => savedProcess(document),
      );
      if (outcome === "newer-version") {
        vi.mocked(nativeProcessApi.get).mockImplementation(async (_, id) =>
          savedProcess(
            {
              ...example,
              definition: {
                ...example.definition,
                id,
                title: "Newer remote work",
              },
            },
            2,
          ),
        );
      } else {
        vi.mocked(nativeProcessApi.get).mockRejectedValue(
          new Error("Current version unavailable"),
        );
      }
      fireEvent.click(screen.getByTestId("native-save"));
      await screen.findByTestId("native-error");
      expect(dirty.mock.lastCall?.[0]).toBe(true);
      expect(
        sessionStorage.getItem("wright-native-draft-v1:session-one"),
      ).not.toBeNull();
      expect(screen.getByTestId("native-run-start")).toBeDisabled();
      const first = vi.mocked(nativeProcessApi.create).mock.calls[0];
      fireEvent.click(screen.getByTestId("native-save"));
      await waitFor(() =>
        expect(nativeProcessApi.create).toHaveBeenCalledTimes(2),
      );
      expect(vi.mocked(nativeProcessApi.create).mock.calls[1]).toEqual(first);
      expect(dirty.mock.lastCall?.[0]).toBe(true);
      expect(nativeProcessApi.save).not.toHaveBeenCalled();
    },
  );
  it("renders programmatic identities and preserves invalid field buffers across selection", async () => {
    await renderExample();
    expect(screen.getByTestId("mocked-canvas")).toHaveTextContent(
      example.definition.steps[0].id,
    );
    fireEvent.change(screen.getByTestId("native-step-list"), {
      target: { value: "need-source" },
    });
    fireEvent.change(screen.getByTestId("native-step-title"), {
      target: { value: "" },
    });
    fireEvent.click(screen.getByTestId("native-apply-step"));
    expect(screen.getByRole("alert")).toHaveTextContent("text length");
    fireEvent.change(screen.getByTestId("native-step-list"), {
      target: { value: "constraint-source" },
    });
    fireEvent.change(screen.getByTestId("native-step-list"), {
      target: { value: "need-source" },
    });
    expect(screen.getByTestId("native-step-title")).toHaveValue("");
    const source = JSON.parse(
      (screen.getByTestId("native-source") as HTMLTextAreaElement).value,
    );
    expect(source.steps[0].title).toBe(example.definition.steps[0].title);
    expect(screen.getByTestId("native-save")).toBeDisabled();
    fireEvent.click(screen.getByTestId("native-discard-fields"));
    expect(screen.getByTestId("native-save")).toBeEnabled();
  });
  it("saves the language definition and reopens the exact server response", async () => {
    await renderExample();
    vi.mocked(nativeProcessApi.create).mockImplementation(async (_, document) =>
      savedProcess(document),
    );
    vi.mocked(nativeProcessApi.get).mockImplementation(async (_, id) =>
      savedProcess({ ...example, definition: { ...example.definition, id } }),
    );
    fireEvent.click(screen.getByTestId("native-save"));
    await waitFor(() => expect(nativeProcessApi.create).toHaveBeenCalledOnce());
    await waitFor(() =>
      expect(screen.getByTestId("native-status")).toHaveTextContent(
        "Saved revision 1",
      ),
    );
    const [, posted] = vi.mocked(nativeProcessApi.create).mock.calls[0];
    expect(posted.definition.connections).toEqual(
      example.definition.connections,
    );
    expect(posted.definition).not.toHaveProperty("nodes");
    expect(posted.definition).not.toHaveProperty("presentation");
    fireEvent.click(screen.getByTestId("native-open"));
    await waitFor(() =>
      expect(screen.getByTestId("native-status")).toHaveTextContent(
        "Opened saved revision 1",
      ),
    );
  });
  it("preserves a conflicting draft and uses CAS tokens on updates", async () => {
    vi.mocked(nativeProcessApi.list).mockResolvedValue({
      documents: [
        {
          id: example.definition.id,
          title: "Saved",
          revision: 1,
          token: "1".repeat(64),
          updated_at: "",
        },
      ],
      next_cursor: null,
    });
    vi.mocked(nativeProcessApi.get).mockResolvedValue(savedProcess());
    render(
      <MemoryRouter>
        <NativeEditor sessionId="session-one" />
      </MemoryRouter>,
    );
    await screen.findByTestId("native-saved-list");
    fireEvent.change(screen.getByTestId("native-saved-list"), {
      target: { value: example.definition.id },
    });
    fireEvent.click(screen.getByTestId("native-open"));
    await waitFor(() =>
      expect(screen.getByTestId("native-status")).toHaveTextContent("Opened"),
    );
    fireEvent.change(screen.getByTestId("native-process-title"), {
      target: { value: "My retained revision" },
    });
    fireEvent.click(screen.getByTestId("native-apply-title"));
    vi.mocked(nativeProcessApi.save).mockRejectedValue(
      new NativeProcessError(
        {
          code: "NATIVE_CONFLICT",
          message: "Another writer saved first.",
          recovery: "Reload or save a copy.",
        },
        409,
      ),
    );
    fireEvent.click(screen.getByTestId("native-save"));
    await screen.findByRole("region", { name: "Save conflict" });
    expect(nativeProcessApi.save).toHaveBeenCalledWith(
      "session-one",
      expect.objectContaining({
        definition: expect.objectContaining({ title: "My retained revision" }),
      }),
      "1".repeat(64),
      expect.any(String),
    );
    expect(screen.getByTestId("native-process-title")).toHaveValue(
      "My retained revision",
    );
    fireEvent.click(screen.getByTestId("native-save-copy"));
    expect(screen.getByTestId("native-process-title")).toHaveValue(
      "My retained revision",
    );
  });
  it("requires confirmation before replacing dirty work and returns keyboard focus", async () => {
    await renderExample();
    fireEvent.click(screen.getByTestId("native-new"));
    expect(screen.getByRole("dialog")).toHaveTextContent("unsaved");
    expect(screen.getByTestId("native-stay")).toHaveFocus();
    fireEvent.keyDown(document, { key: "Tab", shiftKey: true });
    expect(screen.getByTestId("native-leave")).toHaveFocus();
    fireEvent.keyDown(document, { key: "Escape" });
    expect(screen.queryByRole("dialog")).not.toBeInTheDocument();
  });
  it("recovers unapplied fields after unmount without declaring them saved", async () => {
    await renderExample();
    fireEvent.change(screen.getByTestId("native-step-list"), {
      target: { value: "need-source" },
    });
    fireEvent.change(screen.getByTestId("native-config-value"), {
      target: { value: "Retained draft text" },
    });
    cleanup();
    render(
      <MemoryRouter>
        <NativeEditor sessionId="session-one" />
      </MemoryRouter>,
    );
    await screen.findByTestId("native-recover");
    fireEvent.click(screen.getByTestId("native-recover"));
    fireEvent.change(screen.getByTestId("native-step-list"), {
      target: { value: "need-source" },
    });
    expect(screen.getByTestId("native-config-value")).toHaveValue(
      "Retained draft text",
    );
    expect(screen.getByTestId("native-save")).toBeDisabled();
    expect(nativeProcessApi.create).not.toHaveBeenCalled();
  });
  it("reports actual readiness only after a service check and invalidates it on edit", async () => {
    await renderExample();
    fireEvent.click(screen.getByTestId("native-check"));
    await screen.findByRole("heading", { name: "Ready for execution" });
    fireEvent.change(screen.getByTestId("native-process-title"), {
      target: { value: "Changed" },
    });
    fireEvent.click(screen.getByTestId("native-apply-title"));
    expect(
      screen.queryByRole("heading", { name: "Ready for execution" }),
    ).not.toBeInTheDocument();
    expect(
      screen.getByText(/changed after its last readiness/),
    ).toBeInTheDocument();
  });
});
