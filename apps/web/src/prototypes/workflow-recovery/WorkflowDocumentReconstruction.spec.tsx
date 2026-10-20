import { NativeWorkflowPanel } from "../desktop-panel/NativeWorkflowPanel";
import {
  NativeSourceClient,
  type NativeSourceCall,
} from "../desktop-panel/native-source-client";
import type { WorkspaceWorkflowSourceDocument } from "../../services/workspace-service";
import { afterEach, beforeAll, expect, it, vi } from "vitest";
import {
  cleanup,
  fireEvent,
  render,
  screen,
  waitFor,
} from "@testing-library/react";
import { WorkflowRecoveryConcept } from "./WorkflowRecoveryConcept";
import demo from "./fixtures/codex-spacer-comparison.workflow.wflow?raw";
import robot from "../../../../../packages/workspace_service/src/workspace_service/engineering_workflow_templates/templates/robot-tracking-diagnosis.workflow.wflow?raw";
import { canonicalDefinitionBytes } from "./canonical-wire";
import {
  parseRecoverySourceDocument,
  parseRecoveryAuthoringSource,
  formatRecoveryAuthoringSource,
  validateRecoveryAuthoringRoundTrip,
} from "./recovery-authoring";

beforeAll(() =>
  vi.stubGlobal(
    "ResizeObserver",
    class {
      observe = vi.fn();
      unobserve = vi.fn();
      disconnect = vi.fn();
    },
  ),
);
afterEach(cleanup);

it.each(
  [
    ["accepted spacer demo", demo],
    [
      "existing Robot Tracking Diagnosis",
      robot.replaceAll("__instance__", "robot_test"),
    ],
  ].flatMap(([name, source]) => {
    const lf = source.replace(/\r\n/g, "\n");
    return [
      [`${name} (LF)`, lf],
      [`${name} (CRLF)`, lf.replace(/\n/g, "\r\n")],
    ];
  }),
)("cold opens %s with document-owned connection points", (_name, source) => {
  const save = vi.fn();
  render(
    <WorkflowRecoveryConcept
      workflowSource={source}
      definitionRevision={1}
      onSave={save}
    />,
  );
  expect(screen.queryByText("Workflow file needs correction.")).toBeNull();
  fireEvent.click(screen.getByTestId("workflow-recovery-view-code"));
  // Textarea display normalizes CRLF; parsing below still uses exact input.
  expect(screen.getByLabelText("Workflow source")).toHaveValue(
    source.replace(/\r\n/g, "\n"),
  );
  expect(save).not.toHaveBeenCalled();
  const parsed = parseRecoverySourceDocument(source, 1);
  expect(parsed.ok, JSON.stringify(parsed.diagnostics)).toBe(true);
  expect(validateRecoveryAuthoringRoundTrip(parsed.workflow!).ok).toBe(true);
  const formatted = formatRecoveryAuthoringSource(parsed.workflow!).text;
  const reopened = parseRecoverySourceDocument(formatted, 1);
  expect(reopened.ok, JSON.stringify(reopened.diagnostics)).toBe(true);
  expect(canonicalDefinitionBytes(reopened.workflow!, true)).toBe(
    canonicalDefinitionBytes(parsed.workflow!, true),
  );
});

it("still rejects a changed kind or moved port against its own accepted document", () => {
  const accepted = parseRecoverySourceDocument(demo, 1).workflow!;
  const wrongKind = demo.replace(
    '"key":"report_out","name":"report_out","kind":"engineering_document"',
    '"key":"report_out","name":"report_out","kind":"manufacturing_report"',
  );
  expect(
    parseRecoveryAuthoringSource(wrongKind, accepted).diagnostics.some(
      (d) => d.code === "WFR-SOURCE-PORT-KIND",
    ),
  ).toBe(true);
  const wrongOwner = demo
    .replace('"key":"comparison_out"', '"key":"report_out"')
    .replace(
      '"key":"report_out","name":"report_out"',
      '"key":"other_out","name":"report_out"',
    );
  expect(
    parseRecoveryAuthoringSource(wrongOwner, accepted).diagnostics.some(
      (d) => d.code === "WFR-SOURCE-PORT-OWNER",
    ),
  ).toBe(true);
});

it("keeps an invalid source editable and saves only an explicit valid correction", async () => {
  const invalid = demo.replace(
    '"kind":"structured_result"',
    '"kind":"unknown_kind"',
  );
  const save = vi.fn().mockResolvedValue({
    source: demo,
    definition_revision: 2,
    storage_digest: "a".repeat(64),
  });
  render(
    <WorkflowRecoveryConcept
      workflowSource={invalid}
      definitionRevision={1}
      onSave={save}
    />,
  );
  const button = screen.getByRole("button", { name: "Save corrected source" });
  expect(button).toBeDisabled();
  fireEvent.change(screen.getByLabelText("Workflow source"), {
    target: { value: demo },
  });
  expect(save).not.toHaveBeenCalled();
  fireEvent.click(button);
  await waitFor(() =>
    expect(screen.queryByText("Workflow file needs correction.")).toBeNull(),
  );
  expect(save).toHaveBeenCalledExactlyOnceWith(
    demo,
    expect.objectContaining({ semanticRevision: 1 }),
  );
});

it("reconciles an uncertain correction through a read without repeating its write", async () => {
  const invalid = "invalid source";
  const save = vi.fn().mockRejectedValue(new Error("lost acknowledgement"));
  const read = vi.fn().mockResolvedValue({
    source: demo,
    definition_revision: 2,
    storage_digest: "a".repeat(64),
  });
  render(
    <WorkflowRecoveryConcept
      workflowSource={invalid}
      definitionRevision={1}
      onSave={save}
      onReadStoredSource={read}
    />,
  );
  fireEvent.change(screen.getByLabelText("Workflow source"), {
    target: { value: demo },
  });
  fireEvent.click(
    screen.getByRole("button", { name: "Save corrected source" }),
  );
  await screen.findByRole("button", { name: "Read saved workflow" });
  expect(
    screen.getByRole("button", { name: "Save corrected source" }),
  ).toBeDisabled();
  fireEvent.click(screen.getByRole("button", { name: "Read saved workflow" }));
  await waitFor(() =>
    expect(screen.queryByText("Workflow file needs correction.")).toBeNull(),
  );
  expect(save).toHaveBeenCalledOnce();
  expect(read).toHaveBeenCalledOnce();
});

it("preserves raw correction edits through the existing inert draft callback before accepting source", () => {
  const changed = vi.fn(),
    save = vi.fn();
  render(
    <WorkflowRecoveryConcept
      workflowSource="invalid source"
      onDraftChange={changed}
      onSave={save}
    />,
  );
  fireEvent.change(screen.getByLabelText("Workflow source"), {
    target: { value: "retained raw correction" },
  });
  expect(changed).toHaveBeenLastCalledWith(
    {
      source: "retained raw correction",
      applied_source: "invalid source",
      layout: null,
      view: "code",
    },
    true,
  );
  expect(save).not.toHaveBeenCalled();
});
it("restores an explicitly resumed correction draft without accepting or running it", () => {
  const save = vi.fn(),
    dirty = vi.fn();
  render(
    <WorkflowRecoveryConcept
      workflowSource="invalid source"
      initialDraft={{
        source: "retained raw correction",
        applied_source: "invalid source",
        layout: null,
        view: "code",
      }}
      onSave={save}
      onUnsavedChange={dirty}
    />,
  );
  expect(screen.getByLabelText("Workflow source")).toHaveValue(
    "retained raw correction",
  );
  expect(dirty).toHaveBeenCalledWith(true);
  expect(save).not.toHaveBeenCalled();
});
it("adopts only the exact reconciled source in native workspace context without replaying an uncertain save", async () => {
  const initial: WorkspaceWorkflowSourceDocument = {
    workspace_id: "workspace",
    path: "workflows/recovery.workflow.wflow",
    source: "invalid source",
    storage_revision: 1,
    storage_digest: "a".repeat(64),
    definition_revision: 1,
    metadata_authority: "wright_host",
    size_bytes: 14,
  };
  let stored = initial,
    observed: WorkspaceWorkflowSourceDocument | undefined;
  const call = vi.fn<NativeSourceCall>(async (name, args) => {
    if (name === "wright_workflow_read")
      return { content: [], structuredContent: { ...(observed ?? stored) } };
    stored = {
      ...initial,
      source: String(args.source),
      storage_revision: 2,
      storage_digest: "b".repeat(64),
      definition_revision: 2,
      layout: {
        ...(args.layout as NonNullable<
          WorkspaceWorkflowSourceDocument["layout"]
        >),
        semanticRevision: 2,
        layoutRevision: 1,
      },
      layout_revision: 1,
      size_bytes: String(args.source).length,
    };
    throw Error("Lost save acknowledgement");
  });
  const client = new NativeSourceClient(
    { workspaceId: "workspace", sessionId: "session", path: initial.path },
    call,
  );
  await client.read();
  const accepted = vi.fn();
  render(
    <NativeWorkflowPanel
      initial={initial}
      client={client}
      workspaceName="Recovery"
      onAccepted={accepted}
    />,
  );
  fireEvent.change(screen.getByLabelText("Workflow source"), {
    target: { value: demo },
  });
  fireEvent.click(
    screen.getByRole("button", { name: "Save corrected source" }),
  );
  const read = await screen.findByRole("button", {
    name: "Read saved workflow",
  });
  observed = initial;
  fireEvent.click(read);
  await screen.findByText(/The saved correction is still unconfirmed/);
  await waitFor(() => expect(read).toBeEnabled());
  expect(accepted).not.toHaveBeenCalled();
  expect(
    screen.getByRole("button", { name: "Save corrected source" }),
  ).toBeDisabled();
  observed = {
    ...stored,
    layout: { ...stored.layout!, viewport: { x: 11, y: 0, zoom: 1 } },
  };
  fireEvent.click(read);
  await screen.findByText(/The saved correction is still unconfirmed/);
  await waitFor(() => expect(read).toBeEnabled());
  expect(accepted).not.toHaveBeenCalled();
  expect(
    screen.getByRole("button", { name: "Save corrected source" }),
  ).toBeDisabled();
  observed = undefined;
  fireEvent.click(read);
  await waitFor(() =>
    expect(screen.queryByText("Workflow file needs correction.")).toBeNull(),
  );
  expect(accepted).toHaveBeenCalledExactlyOnceWith(stored);
  expect(
    call.mock.calls.filter(([name]) => name === "wright_workflow_save"),
  ).toHaveLength(1);
});
