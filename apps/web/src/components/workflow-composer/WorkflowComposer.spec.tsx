import { render, screen, waitFor, within } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { beforeEach, describe, expect, it, vi } from "vitest";

vi.mock("../../services/workflow-drafts", async (importOriginal) => {
  const actual =
    await importOriginal<typeof import("../../services/workflow-drafts")>();
  return {
    ...actual,
    readWorkflowDraft: vi.fn(),
    saveWorkflowDraft: vi.fn(),
    validateWorkflowDraft: vi.fn(),
  };
});

import fixture from "../../../../../packages/core/tests/fixtures/workflow_drafts/representative-workflow.json";
import {
  decodeWorkflowDraft,
  readWorkflowDraft,
  saveWorkflowDraft,
  validateWorkflowDraft,
  WorkflowDraftClientError,
} from "../../services/workflow-drafts";
import { draftSemanticIds, projectionSemanticIds } from "./draft-projection";
import type {
  DraftCanvasAdapterProps,
  DraftCanvasRenderer,
} from "./renderer-types";
import { WorkflowComposer } from "./WorkflowComposer";

const readDraft = vi.mocked(readWorkflowDraft);
const saveDraft = vi.mocked(saveWorkflowDraft);
const validateDraft = vi.mocked(validateWorkflowDraft);

function renderedSemanticIds(root: HTMLElement): string[] {
  return Array.from(root.querySelectorAll<HTMLElement>("[data-semantic-id]"))
    .map((element) => element.dataset.semanticId ?? "")
    .sort();
}

function contractRenderer(
  name: string,
  observe?: (props: DraftCanvasAdapterProps) => void,
): DraftCanvasRenderer {
  return (props) => {
    observe?.(props);
    return (
      <section
        data-testid={`fake-canvas-${name}`}
        aria-label={`${name} canvas`}
      >
        {projectionSemanticIds(props.projection).map((semanticId) => (
          <span data-semantic-id={semanticId} key={semanticId}>
            {semanticId}
          </span>
        ))}
        <button
          data-testid={`fake-select-${name}`}
          type="button"
          onClick={() =>
            props.onIntent({
              type: "select",
              semanticId: "block.define-product",
            })
          }
        >
          Select Define product
        </button>
      </section>
    );
  };
}

describe("WorkflowComposer renderer contract", () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it("renders exactly the canonical identities in both canvas and text projections", () => {
    const draft = decodeWorkflowDraft(fixture);
    render(
      <WorkflowComposer
        initialDraft={draft}
        renderer={contractRenderer("contract")}
      />,
    );

    const expected = [...draftSemanticIds(draft)];
    const canvas = screen.getByTestId("fake-canvas-contract");
    const text = screen.getByTestId("workflow-composer-text");

    expect(renderedSemanticIds(canvas)).toEqual(expected);
    expect(renderedSemanticIds(text)).toEqual(expected);
    expect(renderedSemanticIds(text)).toEqual(renderedSemanticIds(canvas));
    expect(new Set(renderedSemanticIds(text)).size).toBe(23);

    for (const phase of draft.semantic.phases) {
      const node = text.querySelector<HTMLElement>(
        `[data-semantic-id="${phase.id}"]`,
      );
      expect(node).toHaveTextContent(phase.name);
      for (const blockId of phase.block_ids)
        expect(node).toHaveTextContent(blockId);
    }
    for (const block of draft.semantic.blocks) {
      const node = text.querySelector<HTMLElement>(
        `[data-semantic-id="${block.id}"]`,
      );
      expect(node).toHaveTextContent(block.title);
      expect(node).toHaveTextContent(block.phase_id);
      for (const portId of [
        ...block.input_port_ids,
        ...block.output_port_ids,
      ]) {
        expect(node).toHaveTextContent(portId);
      }
    }
    for (const connection of draft.semantic.connections) {
      const node = text.querySelector<HTMLElement>(
        `[data-semantic-id="${connection.id}"]`,
      );
      expect(node).toHaveTextContent(connection.source_port_id);
      expect(node).toHaveTextContent(connection.target_port_id);
    }
    for (const gate of draft.semantic.gates) {
      const node = text.querySelector<HTMLElement>(
        `[data-semantic-id="${gate.id}"]`,
      );
      expect(node).toHaveTextContent(gate.owner_block_id);
      expect(node).toHaveTextContent(gate.proceed_target_block_id);
      expect(node).toHaveTextContent(gate.revise_target_block_id);
      expect(node).toHaveTextContent(gate.feedback_path_id);
    }
    for (const feedback of draft.semantic.feedback_paths) {
      const node = text.querySelector<HTMLElement>(
        `[data-semantic-id="${feedback.id}"]`,
      );
      expect(node).toHaveTextContent(feedback.from_gate_id);
      expect(node).toHaveTextContent(feedback.to_block_id);
      expect(node).toHaveTextContent(feedback.reason);
    }
    for (const artifact of draft.semantic.intended_artifacts) {
      const node = text.querySelector<HTMLElement>(
        `[data-semantic-id="${artifact.id}"]`,
      );
      expect(node).toHaveTextContent(artifact.title);
      expect(node).toHaveTextContent(artifact.produced_by_block_id);
    }
  });

  it("replaces renderers without changing semantic bytes, projection, or text", () => {
    const draft = decodeWorkflowDraft(fixture);
    const before = JSON.stringify(draft);
    const observedA = vi.fn<(props: DraftCanvasAdapterProps) => void>();
    const observedB = vi.fn<(props: DraftCanvasAdapterProps) => void>();
    const view = render(
      <WorkflowComposer
        initialDraft={draft}
        renderer={contractRenderer("a", observedA)}
      />,
    );
    const textBefore = screen.getByTestId("workflow-composer-text").textContent;
    const idsBefore = renderedSemanticIds(
      screen.getByTestId("workflow-composer-text"),
    );

    view.rerender(
      <WorkflowComposer
        initialDraft={draft}
        renderer={contractRenderer("b", observedB)}
      />,
    );

    expect(screen.queryByTestId("fake-canvas-a")).toBeNull();
    expect(screen.getByTestId("fake-canvas-b")).toBeInTheDocument();
    expect(screen.getByTestId("workflow-composer-text").textContent).toBe(
      textBefore,
    );
    expect(
      renderedSemanticIds(screen.getByTestId("workflow-composer-text")),
    ).toEqual(idsBefore);
    expect(JSON.stringify(draft)).toBe(before);
    expect(observedA.mock.calls[0]?.[0].projection).toEqual(
      observedB.mock.calls[0]?.[0].projection,
    );
  });

  it("routes renderer selection through host state without granting semantic authority", async () => {
    const user = userEvent.setup();
    const draft = decodeWorkflowDraft(fixture);
    const before = JSON.stringify(draft);
    const observed = vi.fn<(props: DraftCanvasAdapterProps) => void>();
    render(
      <WorkflowComposer
        initialDraft={draft}
        renderer={contractRenderer("select", observed)}
      />,
    );

    const firstProps = observed.mock.calls[0]?.[0];
    expect(Object.keys(firstProps ?? {}).sort()).toEqual([
      "onIntent",
      "projection",
      "selectedSemanticId",
    ]);
    expect(Object.isFrozen(firstProps?.projection)).toBe(true);
    expect(firstProps?.selectedSemanticId).toBeNull();

    await user.click(screen.getByTestId("fake-select-select"));

    expect(observed.mock.calls.at(-1)?.[0].selectedSemanticId).toBe(
      "block.define-product",
    );
    expect(
      within(screen.getByTestId("workflow-composer-inspector")).getByText(
        "block.define-product",
      ),
    ).toBeInTheDocument();
    expect(JSON.stringify(draft)).toBe(before);
    expect(
      screen.queryByRole("button", {
        name: /^(execute|run|publish|release workflow)$/i,
      }),
    ).toBeNull();
  });

  it("renders the first-party phase lanes and provides bounded zoom and selection", async () => {
    const user = userEvent.setup();
    const draft = decodeWorkflowDraft(fixture);
    render(<WorkflowComposer initialDraft={draft} />);

    const canvas = screen.getByTestId("workflow-composer-canvas");
    expect(renderedSemanticIds(canvas)).toEqual([...draftSemanticIds(draft)]);
    expect(canvas).toHaveTextContent("Directed connections");
    expect(canvas).toHaveTextContent("Feedback");
    expect(canvas).toHaveTextContent("Approval gate");
    expect(canvas).toHaveTextContent("Intended artifact");

    await user.click(
      screen.getByTestId("workflow-canvas-select-block.define-product"),
    );
    expect(screen.getByTestId("workflow-composer-inspector")).toHaveTextContent(
      "Define product",
    );
    expect(screen.getByTestId("workflow-composer-inspector")).toHaveTextContent(
      "block.define-product",
    );
    expect(
      screen.getByTestId("workflow-canvas-select-block.define-product"),
    ).toHaveAttribute("aria-pressed", "true");
    const positioned = canvas.querySelector<HTMLElement>(
      '[data-semantic-id="block.define-product"]',
    );
    expect(positioned).toHaveAttribute("data-layout-x", "320");
    expect(positioned).toHaveAttribute("data-layout-y", "0");
    expect(positioned?.style.getPropertyValue("--workflow-block-order")).toBe(
      "320",
    );

    await user.click(screen.getByTestId("workflow-canvas-zoom-in"));
    expect(screen.getByText("120%")).toBeInTheDocument();
    await user.click(screen.getByTestId("workflow-canvas-fit"));
    expect(screen.getByText("100%")).toBeInTheDocument();
  });

  it("validates, saves, closes, and reopens the exact saved draft identities", async () => {
    const user = userEvent.setup();
    const draft = decodeWorkflowDraft(fixture);
    const saved = { ...draft, revision: 2 };
    validateDraft.mockResolvedValue({
      valid: true,
      semantic_sha256: draft.semantic_sha256,
      layout_sha256: draft.layout_sha256,
      diagnostics: [],
    });
    saveDraft.mockResolvedValue({ draft: saved, etag: '"saved-etag"' });
    readDraft.mockResolvedValue({ draft: saved, etag: '"saved-etag"' });
    render(
      <WorkflowComposer initialDraft={draft} initialEtag={'"initial-etag"'} />,
    );

    await user.click(screen.getByTestId("workflow-composer-save"));
    expect(await screen.findByText("Saved revision 2.")).toBeInTheDocument();
    expect(saveDraft).toHaveBeenCalledWith(draft, '"initial-etag"');
    expect(screen.getByLabelText("Working draft authority")).toHaveTextContent(
      "Revision 2",
    );

    await user.click(screen.getByTestId("workflow-composer-close"));
    const closed = screen.getByTestId("workflow-composer-closed");
    expect(closed).toHaveTextContent(draft.semantic_sha256);
    expect(closed).toHaveTextContent(draft.layout_sha256);

    await user.click(screen.getByTestId("workflow-composer-reopen"));
    expect(
      await screen.findByTestId("workflow-composer-text"),
    ).toBeInTheDocument();
    expect(readDraft).toHaveBeenCalledWith(draft.draft_id);
    expect(screen.getByText(/Reopened revision 2/)).toBeInTheDocument();
    expect(
      renderedSemanticIds(screen.getByTestId("workflow-composer-text")),
    ).toEqual([...draftSemanticIds(draft)]);
  });

  it("recovers a stale save by reopening current state without retrying the write", async () => {
    const user = userEvent.setup();
    const draft = decodeWorkflowDraft(fixture);
    const current = { ...draft, revision: 2 };
    validateDraft.mockResolvedValue({
      valid: true,
      semantic_sha256: draft.semantic_sha256,
      layout_sha256: draft.layout_sha256,
      diagnostics: [],
    });
    saveDraft.mockRejectedValue(
      new WorkflowDraftClientError(412, "WORKFLOW_DRAFT_STALE_REVISION"),
    );
    readDraft.mockResolvedValue({ draft: current, etag: '"current-etag"' });
    render(
      <WorkflowComposer initialDraft={draft} initialEtag={'"stale-etag"'} />,
    );

    await user.click(screen.getByTestId("workflow-composer-save"));

    expect(
      await screen.findByText(/local candidate is preserved/),
    ).toBeInTheDocument();
    expect(readDraft).toHaveBeenCalledTimes(1);
    expect(saveDraft).toHaveBeenCalledTimes(1);
    expect(screen.getByLabelText("Working draft authority")).toHaveTextContent(
      "Revision 1",
    );

    await user.click(screen.getByTestId("workflow-composer-use-current"));

    expect(screen.getByLabelText("Working draft authority")).toHaveTextContent(
      "Revision 2",
    );
    expect(saveDraft).toHaveBeenCalledTimes(1);
  });

  it("builds the bounded four-block review composition from an empty draft", async () => {
    const user = userEvent.setup();
    const representative = decodeWorkflowDraft(fixture);
    const empty = decodeWorkflowDraft({
      ...representative,
      semantic_sha256: "0".repeat(64),
      layout_sha256: "0".repeat(64),
      semantic: {
        title: "Product definition draft",
        purpose: "Capture, define, review, and release one product definition.",
        phases: [
          {
            id: "phase.draft",
            name: "Draft",
            purpose: "Organize provisional workflow blocks.",
            order: 0,
            block_ids: [],
          },
        ],
        blocks: [],
        ports: [],
        connections: [],
        gates: [],
        feedback_paths: [],
        intended_artifacts: [],
      },
      layout: { schema_version: "1.0.0", positions: [] },
    });
    validateDraft.mockResolvedValue({
      valid: true,
      semantic_sha256: representative.semantic_sha256,
      layout_sha256: representative.layout_sha256,
      diagnostics: [],
    });
    saveDraft.mockImplementation(async (candidate) => ({
      draft: { ...candidate, revision: 2 },
      etag: '"saved-etag"',
    }));
    render(
      <WorkflowComposer initialDraft={empty} initialEtag={'"empty-etag"'} />,
    );

    for (const role of ["input", "work", "review", "release"] as const) {
      const button = screen.getByTestId(`workflow-composer-palette-${role}`);
      await waitFor(() => expect(button).toBeEnabled());
      await user.click(button);
    }

    await waitFor(() =>
      expect(screen.getByTestId("workflow-composer-canvas")).toHaveTextContent(
        "4 blocks · 3 phases",
      ),
    );
    expect(
      renderedSemanticIds(screen.getByTestId("workflow-composer-canvas")),
    ).toHaveLength(23);
    expect(
      renderedSemanticIds(screen.getByTestId("workflow-composer-text")),
    ).toEqual(
      renderedSemanticIds(screen.getByTestId("workflow-composer-canvas")),
    );
    expect(
      screen.getByText(/Representative four-block composition is complete/),
    ).toBeInTheDocument();

    await user.click(screen.getByTestId("workflow-composer-save"));
    expect(await screen.findByText("Saved revision 2.")).toBeInTheDocument();
    const savedCandidate = saveDraft.mock.calls[0]?.[0];
    expect(savedCandidate?.semantic.blocks).toHaveLength(4);
    expect(savedCandidate?.semantic.connections).toHaveLength(3);
    expect(savedCandidate?.semantic.gates).toHaveLength(1);
    expect(savedCandidate?.semantic.feedback_paths).toHaveLength(1);
    expect(savedCandidate?.layout.positions.map(({ y }) => y)).toEqual([
      0, 32, 64, 96,
    ]);
  });

  it("keeps the inspector validation state consistent with server diagnostics", async () => {
    const user = userEvent.setup();
    const draft = decodeWorkflowDraft(fixture);
    validateDraft.mockResolvedValue({
      valid: false,
      semantic_sha256: draft.semantic_sha256,
      layout_sha256: draft.layout_sha256,
      diagnostics: [
        {
          code: "WORKFLOW_DRAFT_CONNECTION_TYPE_INCOMPATIBLE",
          path: "/semantic/connections/0",
          affected_semantic_ids: ["connection.requirements-to-definition"],
          explanation: "The connected port value types differ.",
          correction: "Connect ports with matching declared value types.",
        },
      ],
    });
    render(
      <WorkflowComposer initialDraft={draft} initialEtag={'"draft-etag"'} />,
    );

    await user.click(screen.getByTestId("workflow-composer-validate"));

    expect(
      await screen.findByText("Validation found 1 diagnostic."),
    ).toBeInTheDocument();
    expect(screen.getByTestId("workflow-composer-inspector")).toHaveTextContent(
      "WORKFLOW_DRAFT_CONNECTION_TYPE_INCOMPATIBLE",
    );
    expect(
      screen.getByTestId("workflow-composer-inspector"),
    ).not.toHaveTextContent("Validation passed");
  });
});
