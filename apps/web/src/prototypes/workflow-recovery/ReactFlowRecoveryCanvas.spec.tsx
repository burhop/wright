import { fireEvent, render, screen } from "@testing-library/react";
import { beforeAll, describe, expect, it, vi } from "vitest";

import type { DraftProjection } from "../../components/workflow-composer/draft-projection";
import { cloneLayout, initialLayout, initialRunProjection, initialWorkflow, toDraftProjection } from "./model";
import { ReactFlowRecoveryCanvas, RecoveryCanvasRuntimeProvider } from "./ReactFlowRecoveryCanvas";

class MockResizeObserver {
  observe = vi.fn();
  unobserve = vi.fn();
  disconnect = vi.fn();
}

beforeAll(() => {
  vi.stubGlobal("ResizeObserver", MockResizeObserver);
});

function runtime(run = initialRunProjection(initialWorkflow, "a".repeat(64), "2026-08-31T00:00:00Z")) {
  return {
    run,
    runSubject: { workflowId: run.workflowId, workflowRevision: run.workflowRevision, semanticSha256: run.semanticSha256 },
    proposedBlockIds: new Set<string>(),
    portArtifactIds: Object.fromEntries(initialWorkflow.ports.filter((port) => port.artifactContractId).map((port) => [port.id, port.artifactContractId!])),
    relationshipLabels: Object.fromEntries(initialWorkflow.relationships.map((relationship) => [relationship.id, relationship.label])),
    overlayRelationships: initialWorkflow.relationships.filter((relationship) => relationship.kind === "decision" || relationship.kind === "control"),
    portTreatment: "hybrid" as const,
    onArtifactInspect: vi.fn(),
  };
}

describe("ReactFlowRecoveryCanvas component contract", () => {
  it("collapses reusable components without losing internal run-lineage addresses", () => {
    const projection = toDraftProjection(initialWorkflow, cloneLayout(initialLayout));
    const run = initialRunProjection(initialWorkflow, "a".repeat(64), "2026-08-31T00:00:00Z");
    run.steps["block.review-design"] = {
      state: "blocked",
      label: "Internal review blocked",
      detail: "The reusable review cell needs attention.",
      componentScope: {
        componentInstanceId: "block.review-design",
        componentId: "component.review-cell",
        componentVersion: "1.0.0",
        internalSemanticId: "component.review-cell.block.evaluate",
      },
    };
    render(
      <RecoveryCanvasRuntimeProvider value={runtime(run)}>
        <ReactFlowRecoveryCanvas projection={projection} selectedSemanticId={null} onIntent={() => undefined} />
      </RecoveryCanvasRuntimeProvider>,
    );

    const node = screen.getByTestId("workflow-recovery-block-block.review-design");
    expect(node).toHaveAttribute("data-component-collapsed", "true");
    expect(node).toHaveTextContent("Reusable design review cell · v1.0.0");
    expect(node).toHaveTextContent("1 internal target");
    expect(node).toHaveTextContent("component.review-cell.block.evaluate");
    fireEvent.click(screen.getByTestId("workflow-recovery-component-toggle-block.review-design"));
    expect(node).toHaveAttribute("data-component-collapsed", "false");
    expect(node).toHaveTextContent("component.review-cell.relationship.accept");
    fireEvent.click(screen.getByTestId("workflow-recovery-component-toggle-block.review-design"));
    expect(node).toHaveAttribute("data-component-collapsed", "true");
  });

  it("renders the default projection with identified controls and emits host-owned selection", () => {
    const onIntent = vi.fn();
    const projection = toDraftProjection(initialWorkflow, cloneLayout(initialLayout));
    const { container } = render(
      <RecoveryCanvasRuntimeProvider value={runtime()}>
        <ReactFlowRecoveryCanvas projection={projection} selectedSemanticId={null} onIntent={onIntent} />
      </RecoveryCanvasRuntimeProvider>,
    );
    expect(screen.getByTestId("workflow-recovery-reactflow-pane")).toBeVisible();
    expect(screen.getByTestId("workflow-recovery-canvas-zoom-in")).toBeVisible();
    expect(screen.getByTestId("workflow-recovery-canvas-zoom-out")).toBeVisible();
    expect(screen.getByTestId("workflow-recovery-canvas-fit")).toBeVisible();
    fireEvent.click(screen.getByTestId("workflow-recovery-block-block.generate-geometry"));
    expect(onIntent).toHaveBeenCalledWith({ type: "select", semanticId: "block.generate-geometry" });
    const missing = [...container.querySelectorAll<HTMLElement>('button, [role="button"], [tabindex]:not([tabindex="-1"])')]
      .filter((element) => !element.dataset.testid)
      .map((element) => element.outerHTML.slice(0, 100));
    expect(missing).toEqual([]);
  });

  it("projects running and failed records without changing canonical or layout authority", () => {
    const projection = toDraftProjection(initialWorkflow, cloneLayout(initialLayout));
    const run = initialRunProjection(initialWorkflow, "a".repeat(64), "2026-08-31T00:00:00Z");
    run.state = "running";
    run.activeBlockId = "block.generate-geometry";
    run.activeRelationshipId = "rel.brief-to-geometry";
    run.steps["block.generate-geometry"] = { state: "running", label: "Running", detail: "Projected test record." };
    const view = render(
      <RecoveryCanvasRuntimeProvider value={runtime(run)}>
        <ReactFlowRecoveryCanvas projection={projection} selectedSemanticId={null} onIntent={() => undefined} />
      </RecoveryCanvasRuntimeProvider>,
    );
    expect(screen.getByTestId("workflow-recovery-block-block.generate-geometry")).toHaveAttribute("data-run-state", "running");

    run.state = "failed";
    run.activeBlockId = "block.export-step";
    run.steps["block.export-step"] = { state: "failed", label: "Failed", detail: "Projected test failure." };
    view.rerender(
      <RecoveryCanvasRuntimeProvider value={runtime(run)}>
        <ReactFlowRecoveryCanvas projection={projection} selectedSemanticId={null} onIntent={() => undefined} />
      </RecoveryCanvasRuntimeProvider>,
    );
    expect(screen.getByTestId("workflow-recovery-block-block.export-step")).toHaveAttribute("data-run-state", "failed");
  });

  it("fails closed before rendering an unknown run-record version", () => {
    const projection = toDraftProjection(initialWorkflow, cloneLayout(initialLayout));
    const run = { ...initialRunProjection(), schemaVersion: "99.0.0" } as unknown as ReturnType<typeof initialRunProjection>;
    expect(() => render(
      <RecoveryCanvasRuntimeProvider value={runtime(run)}>
        <ReactFlowRecoveryCanvas projection={projection} selectedSemanticId={null} onIntent={() => undefined} />
      </RecoveryCanvasRuntimeProvider>,
    )).toThrow("WFR-RUN-VERSION-UNSUPPORTED");
  });

  it("fails closed before rendering a run bound to another semantic digest", () => {
    const projection = toDraftProjection(initialWorkflow, cloneLayout(initialLayout));
    const run = initialRunProjection(initialWorkflow, "b".repeat(64), "2026-08-31T00:00:00Z");
    const value = runtime(run);
    value.runSubject = { ...value.runSubject, semanticSha256: "a".repeat(64) };
    expect(() => render(
      <RecoveryCanvasRuntimeProvider value={value}>
        <ReactFlowRecoveryCanvas projection={projection} selectedSemanticId={null} onIntent={() => undefined} />
      </RecoveryCanvasRuntimeProvider>,
    )).toThrow("WFR-RUN-SUBJECT-MISMATCH");
  });

  it("keeps fit and stable selection usable with a 100-block projection", () => {
    const source = toDraftProjection(initialWorkflow, cloneLayout(initialLayout));
    const template = source.phases[0]!.blocks[0]!;
    const blocks = Array.from({ length: 100 }, (_, index) => {
      const semanticId = `block.large-${String(index + 1).padStart(3, "0")}`;
      return {
        ...template,
        id: semanticId,
        semanticId,
        title: `Large graph block ${index + 1}`,
        input_port_ids: [],
        output_port_ids: [],
        gate_ids: [],
        intended_artifact_ids: [],
        inputs: [],
        outputs: [],
        gates: [],
        artifacts: [],
        position: {
          semantic_id: semanticId,
          x: (index % 10) * 340,
          y: Math.floor(index / 10) * 250,
        },
      };
    });
    const projection: DraftProjection = {
      ...source,
      phases: [{
        ...source.phases[0]!,
        id: "phase.large-graph",
        semanticId: "phase.large-graph",
        name: "Large graph contract",
        block_ids: blocks.map((block) => block.semanticId),
        blocks,
      }],
      connections: [],
      feedbackPaths: [],
    };
    const onIntent = vi.fn();
    const started = performance.now();
    render(
      <RecoveryCanvasRuntimeProvider value={runtime()}>
        <ReactFlowRecoveryCanvas projection={projection} selectedSemanticId={null} onIntent={onIntent} />
      </RecoveryCanvasRuntimeProvider>,
    );
    const elapsed = performance.now() - started;
    expect(screen.getByTestId("workflow-recovery-canvas")).toHaveAttribute("data-detail-level", "compact");
    expect(screen.getAllByTestId(/^workflow-recovery-block-block\.large-/)).toHaveLength(100);
    fireEvent.click(screen.getByTestId("workflow-recovery-canvas-fit"));
    fireEvent.change(screen.getByTestId("workflow-recovery-find-input"), { target: { value: "block.large-100" } });
    fireEvent.click(screen.getByTestId("workflow-recovery-find-submit"));
    expect(onIntent).toHaveBeenCalledWith({ type: "select", semanticId: "block.large-100" });
    expect(screen.getByRole("status")).toHaveTextContent("Focused Large graph block 100");
    expect(elapsed).toBeLessThan(5000);
  });
});
