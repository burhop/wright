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

it.each([
  ["accepted spacer demo", demo],
  [
    "existing Robot Tracking Diagnosis",
    robot.replaceAll("__instance__", "robot_test"),
  ],
])("cold opens %s with document-owned connection points", (_name, source) => {
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
  expect(screen.getByLabelText("Workflow source")).toHaveValue(source);
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
