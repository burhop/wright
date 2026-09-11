import { act, fireEvent, render, screen } from "@testing-library/react";
import { beforeAll, describe, expect, it, vi } from "vitest";

import type { DraftProjection } from "../../components/workflow-composer/draft-projection";
import {
  cloneLayout,
  cloneWorkflow,
  initialLayout,
  initialRunProjection,
  initialWorkflow,
  toDraftProjection,
} from "./model";
import { createAuthoringObject } from "./authoring-objects";
import {
  recoveryBlockIconKinds,
  WorkflowObjectIcon,
} from "./WorkflowObjectIcon";
import {
  ReactFlowRecoveryCanvas,
  RecoveryCanvasRuntimeProvider,
  recoveryRelationshipHandleBinding,
} from "./ReactFlowRecoveryCanvas";

class MockResizeObserver {
  observe = vi.fn();
  unobserve = vi.fn();
  disconnect = vi.fn();
}

beforeAll(() => {
  vi.stubGlobal("ResizeObserver", MockResizeObserver);
});

function runtime(
  run = initialRunProjection(
    initialWorkflow,
    "a".repeat(64),
    "2026-08-31T00:00:00Z",
  ),
) {
  return {
    run,
    runSubject: {
      workflowId: run.workflowId,
      workflowRevision: run.workflowRevision,
      semanticSha256: run.semanticSha256,
    },
    proposedBlockIds: new Set<string>(),
    portArtifactIds: Object.fromEntries(
      initialWorkflow.ports
        .filter((port) => port.artifactContractId)
        .map((port) => [port.id, port.artifactContractId!]),
    ),
    relationshipLabels: Object.fromEntries(
      initialWorkflow.relationships.map((relationship) => [
        relationship.id,
        relationship.label,
      ]),
    ),
    overlayRelationships: initialWorkflow.relationships.filter(
      (relationship) =>
        relationship.kind === "decision" || relationship.kind === "control",
    ),
    portTreatment: "hybrid" as const,
    onArtifactInspect: vi.fn(),
  };
}

describe("ReactFlowRecoveryCanvas component contract", () => {
  it("rejects an image-to-text keyboard connection but accepts an image input", () => {
    const workflow = cloneWorkflow(initialWorkflow);
    workflow.ports.find(
      (port) => port.id === "port.reference-images-out",
    )!.cardinality = "one";
    const onIntent = vi.fn();
    render(
      <RecoveryCanvasRuntimeProvider value={runtime()}>
        <ReactFlowRecoveryCanvas
          projection={toDraftProjection(workflow, initialLayout)}
          selectedSemanticId={"block.create-design-specification"}
          onIntent={onIntent}
        />
      </RecoveryCanvasRuntimeProvider>,
    );
    fireEvent.keyDown(
      screen.getByTestId("workflow-recovery-handle-port.reference-images-out"),
      { key: "Enter" },
    );
    fireEvent.keyDown(
      screen.getByTestId("workflow-recovery-handle-port.design-intent-in"),
      { key: "Enter" },
    );
    expect(onIntent).not.toHaveBeenCalled();
    expect(screen.getByRole("status")).toHaveTextContent(
      "Connect the image to an input that accepts images.",
    );
    fireEvent.keyDown(
      screen.getByTestId("workflow-recovery-handle-port.reference-images-in"),
      { key: "Enter" },
    );
    expect(onIntent).toHaveBeenCalledWith({
      type: "create-connection",
      sourcePortId: "port.reference-images-out",
      targetPortId: "port.reference-images-in",
    });
  });
  it("distinguishes authored tools from document writers without using their names or identities", () => {
    const workflow = cloneWorkflow(initialWorkflow);
    const layout = cloneLayout(initialLayout);
    const examples = [
      ["mcp-tool", "block.independent-a", "mcp-tools"],
      ["document", "block.independent-b", "llm-document"],
      ["file-input", "block.independent-c", "file"],
      ["fdm-check", "block.independent-d", "fdm"],
      ["manual-review", "block.independent-e", "review"],
      ["engineering-step", "block.independent-f", "more"],
    ] as const;
    for (const [template, id] of examples) {
      const added = createAuthoringObject(template, workflow, layout);
      added.block.id = id;
      added.block.title = "Same engineer-supplied title";
      for (const port of added.ports) port.ownerBlockId = id;
      workflow.blocks.push(added.block);
      workflow.ports.push(...added.ports);
      layout.positions[id] = added.position;
    }
    const semanticBefore = JSON.stringify(workflow);
    const layoutBefore = JSON.stringify(layout);
    const icons = recoveryBlockIconKinds(workflow);
    for (const [, id, icon] of examples) expect(icons[id]).toBe(icon);
    expect(icons["block.reference-images"]).toBe("image");
    expect(icons["block.company-context"]).toBe("context");
    expect(icons["block.generate-geometry"]).toBe("model");
    expect(icons["block.check-manufacturability"]).toBe("3d-check");
    expect(icons["block.review-design"]).toBe("review");
    const projection = toDraftProjection(workflow, layout);
    render(
      <RecoveryCanvasRuntimeProvider
        value={{ ...runtime(), blockIcons: icons }}
      >
        <ReactFlowRecoveryCanvas
          projection={projection}
          selectedSemanticId={null}
          onIntent={() => undefined}
        />
      </RecoveryCanvasRuntimeProvider>,
    );
    expect(
      screen
        .getByTestId("workflow-recovery-block-block.independent-a")
        .querySelector("svg[data-icon-kind]"),
    ).toHaveAttribute("data-icon-kind", "mcp-tools");
    expect(
      screen
        .getByTestId("workflow-recovery-block-block.independent-b")
        .querySelector("svg[data-icon-kind]"),
    ).toHaveAttribute("data-icon-kind", "llm-document");
    expect(
      screen
        .getByTestId("workflow-recovery-block-block.independent-c")
        .querySelector("svg[data-icon-kind]"),
    ).toHaveAttribute("data-icon-kind", "context");
    expect(JSON.stringify(workflow)).toBe(semanticBefore);
    expect(JSON.stringify(layout)).toBe(layoutBefore);
  });

  it("uses current execution and input mode when no matching template supplies the presentation kind", () => {
    const workflow = cloneWorkflow(initialWorkflow);
    const layout = cloneLayout(initialLayout);
    const added = createAuthoringObject("document", workflow, layout);
    added.block.executionKind = "deterministic";
    workflow.blocks.push(added.block);
    workflow.ports.push(...added.ports);
    workflow.blocks.find(
      (block) => block.id === "block.design-intent",
    )!.configuration.input_mode = "workspace-file";
    const icons = recoveryBlockIconKinds(workflow);
    expect(icons[added.block.id]).toBe("mcp-tools");
    expect(icons["block.design-intent"]).toBe("file");
  });

  it("gives the file kind an explicit decorative document alias", () => {
    const { container } = render(<WorkflowObjectIcon kind="file" />);
    expect(container.querySelector("svg")).toHaveAttribute(
      "data-icon-kind",
      "context",
    );
    expect(container.querySelector("svg")).toHaveAttribute(
      "aria-hidden",
      "true",
    );
    expect(container.querySelector("svg")).toHaveAttribute(
      "focusable",
      "false",
    );
  });

  it.each([false, true])(
    "collapses the minimap in a short viewport and permits explicitly reopening it (initially short: %s)",
    (initiallyShort) => {
      let short = initiallyShort;
      const listeners = new Set<(event: MediaQueryListEvent) => void>();
      const media = {
        get matches() {
          return short;
        },
        media: "(max-height: 550px)",
        addEventListener: vi.fn(
          (_type: string, listener: (event: MediaQueryListEvent) => void) =>
            listeners.add(listener),
        ),
        removeEventListener: vi.fn(
          (_type: string, listener: (event: MediaQueryListEvent) => void) =>
            listeners.delete(listener),
        ),
      } as unknown as MediaQueryList;
      const original = window.matchMedia;
      window.matchMedia = (query) =>
        query === media.media ? media : original(query);
      const projection = toDraftProjection(
        initialWorkflow,
        cloneLayout(initialLayout),
      );
      const view = render(
        <RecoveryCanvasRuntimeProvider value={runtime()}>
          <ReactFlowRecoveryCanvas
            projection={projection}
            selectedSemanticId={null}
            onIntent={() => undefined}
          />
        </RecoveryCanvasRuntimeProvider>,
      );
      try {
        const toggle = screen.getByTestId("workflow-recovery-minimap-toggle");
        expect(toggle).toHaveAttribute(
          "aria-expanded",
          String(!initiallyShort),
        );
        if (!initiallyShort)
          act(() => {
            short = true;
            listeners.forEach((listener) =>
              listener({ matches: true } as MediaQueryListEvent),
            );
          });
        expect(screen.queryByTestId("rf__minimap")).not.toBeInTheDocument();
        expect(toggle).toHaveAttribute("aria-label", "Show minimap");
        fireEvent.click(toggle);
        expect(screen.getByTestId("rf__minimap")).toBeInTheDocument();
        expect(toggle).toHaveAttribute("aria-expanded", "true");
        act(() => {
          short = false;
          listeners.forEach((listener) =>
            listener({ matches: false } as MediaQueryListEvent),
          );
        });
        expect(toggle).toHaveAttribute("aria-expanded", "true");
        act(() => {
          short = true;
          listeners.forEach((listener) =>
            listener({ matches: true } as MediaQueryListEvent),
          );
        });
        expect(toggle).toHaveAttribute("aria-expanded", "false");
      } finally {
        view.unmount();
        window.matchMedia = original;
      }
      expect(listeners.size).toBe(0);
    },
  );

  it("keeps every selected input endpoint named and independently keyboard-connectable", () => {
    const projection = toDraftProjection(
      initialWorkflow,
      cloneLayout(initialLayout),
    );
    const onIntent = vi.fn();
    render(
      <RecoveryCanvasRuntimeProvider value={runtime()}>
        <ReactFlowRecoveryCanvas
          projection={projection}
          selectedSemanticId="block.create-design-specification"
          onIntent={onIntent}
        />
      </RecoveryCanvasRuntimeProvider>,
    );
    const selected = screen.getByTestId(
      "workflow-recovery-block-block.create-design-specification",
    );
    expect(selected).toHaveAttribute("data-endpoints-visible", "true");
    for (const id of [
      "port.design-intent-in",
      "port.reference-images-in",
      "port.company-context-in",
    ]) {
      expect(
        screen.getByTestId(`workflow-recovery-handle-${id}`),
      ).toHaveAttribute("tabindex", "0");
      expect(
        screen.getByTestId(`workflow-recovery-handle-${id}`),
      ).toHaveAttribute("data-port-direction", "input");
    }
    fireEvent.keyDown(
      screen.getByTestId("workflow-recovery-handle-port.design-intent-out"),
      { key: "Enter" },
    );
    fireEvent.keyDown(
      screen.getByTestId("workflow-recovery-handle-port.design-intent-in"),
      { key: "Enter" },
    );
    expect(onIntent).toHaveBeenCalledWith({
      type: "create-connection",
      sourcePortId: "port.design-intent-out",
      targetPortId: "port.design-intent-in",
    });
  });

  it("traces selected dependencies without deleting other graph identities", () => {
    const projection = toDraftProjection(
      initialWorkflow,
      cloneLayout(initialLayout),
    );
    const base = runtime();
    render(
      <RecoveryCanvasRuntimeProvider value={{ ...base, focusPath: true }}>
        <ReactFlowRecoveryCanvas
          projection={projection}
          selectedSemanticId="block.export-step"
          onIntent={() => undefined}
        />
      </RecoveryCanvasRuntimeProvider>,
    );
    expect(screen.getByTestId("workflow-recovery-canvas")).toHaveAttribute(
      "data-focus-path",
      "true",
    );
    expect(
      screen.getAllByTestId(/^workflow-recovery-block-block\./),
    ).toHaveLength(initialWorkflow.blocks.length);
    expect(
      screen.getByTestId("workflow-recovery-block-block.export-step"),
    ).not.toHaveClass("is-muted");
  });

  it("collapses reusable components without losing internal run-lineage addresses", () => {
    const projection = toDraftProjection(
      initialWorkflow,
      cloneLayout(initialLayout),
    );
    const run = initialRunProjection(
      initialWorkflow,
      "a".repeat(64),
      "2026-08-31T00:00:00Z",
    );
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
        <ReactFlowRecoveryCanvas
          projection={projection}
          selectedSemanticId={null}
          onIntent={() => undefined}
        />
      </RecoveryCanvasRuntimeProvider>,
    );

    const node = screen.getByTestId(
      "workflow-recovery-block-block.review-design",
    );
    expect(node).toHaveAttribute("data-component-collapsed", "true");
    expect(node).toHaveTextContent("Review group");
    expect(node).toHaveTextContent("1 issue");
    expect(node).not.toHaveTextContent("technical review items");
    expect(node).not.toHaveTextContent("Evaluate the design review");
    expect(
      screen.queryByTestId("workflow-recovery-find-input"),
    ).not.toBeInTheDocument();
    expect(
      screen.queryByTestId(
        "workflow-recovery-component-keyboard-block.review-design",
      ),
    ).not.toBeInTheDocument();
    fireEvent.click(
      screen.getByTestId(
        "workflow-recovery-component-toggle-block.review-design",
      ),
    );
    expect(node).toHaveAttribute("data-component-collapsed", "false");
    expect(node).toHaveTextContent("4 technical review items");
    expect(node).toHaveTextContent("Evaluate the design review");
    expect(node).toHaveTextContent("Accept the reviewed design");
    expect(node).not.toHaveTextContent(
      "component.review-cell.relationship.accept",
    );
    fireEvent.click(
      screen.getByTestId(
        "workflow-recovery-component-toggle-block.review-design",
      ),
    );
    expect(node).toHaveAttribute("data-component-collapsed", "true");
  });

  it("renders the default projection with identified controls and emits host-owned selection", () => {
    const onIntent = vi.fn();
    const projection = toDraftProjection(
      initialWorkflow,
      cloneLayout(initialLayout),
    );
    const { container } = render(
      <RecoveryCanvasRuntimeProvider value={runtime()}>
        <ReactFlowRecoveryCanvas
          projection={projection}
          selectedSemanticId={null}
          onIntent={onIntent}
        />
      </RecoveryCanvasRuntimeProvider>,
    );
    expect(
      screen.getByTestId("workflow-recovery-reactflow-pane"),
    ).toBeVisible();
    expect(
      screen.getByTestId("workflow-recovery-canvas-zoom-in"),
    ).toBeVisible();
    expect(
      screen.getByTestId("workflow-recovery-canvas-zoom-out"),
    ).toBeVisible();
    expect(screen.getByTestId("workflow-recovery-canvas-fit")).toBeVisible();
    expect(
      screen.getByTestId("workflow-recovery-block-block.reference-images"),
    ).toHaveTextContent("Reference images");
    expect(
      screen.getByTestId("workflow-recovery-block-block.reference-images"),
    ).toHaveTextContent("0 in → 1 out");
    expect(
      screen.getByTestId("workflow-recovery-block-block.reference-images"),
    ).not.toHaveTextContent("JPG or PNG images");
    expect(
      screen.getByTestId("workflow-recovery-block-block.design-intent"),
    ).not.toHaveTextContent("text or document");
    expect(
      screen.getByTestId("workflow-recovery-block-block.company-context"),
    ).not.toHaveTextContent("approved company knowledge");
    const minimap = screen.getByTestId("rf__minimap");
    expect(
      screen.getByRole("img", {
        name: "Workflow overview; blue frame shows the visible area",
      }),
    ).toBeVisible();
    expect(minimap).toHaveStyle({
      "--xy-minimap-background-color-props": "#0b1628",
      "--xy-minimap-node-background-color-props": "#1e3a5f",
      "--xy-minimap-node-stroke-color-props": "#38bdf8",
      "--xy-minimap-mask-background-color-props": "rgba(7, 17, 31, 0.48)",
      "--xy-minimap-mask-stroke-color-props": "#38bdf8",
    });
    expect(
      container.querySelector(".react-flow__minimap-mask"),
    ).toBeInTheDocument();
    expect(
      container.querySelector(".recovery-phase-stripe"),
    ).not.toBeInTheDocument();
    fireEvent.click(
      screen.getByTestId("workflow-recovery-block-block.generate-geometry"),
    );
    expect(onIntent).toHaveBeenCalledWith({
      type: "select",
      semanticId: "block.generate-geometry",
    });
    const missing = [
      ...container.querySelectorAll<HTMLElement>(
        'button, [role="button"], [tabindex]:not([tabindex="-1"])',
      ),
    ]
      .filter((element) => !element.dataset.testid)
      .map((element) => element.outerHTML.slice(0, 100));
    expect(missing).toEqual([]);
  });

  it("provides explicit typed handles for decision and revision relationships", () => {
    const projection = toDraftProjection(
      initialWorkflow,
      cloneLayout(initialLayout),
    );
    render(
      <RecoveryCanvasRuntimeProvider value={runtime()}>
        <ReactFlowRecoveryCanvas
          projection={projection}
          selectedSemanticId={null}
          onIntent={() => undefined}
        />
      </RecoveryCanvasRuntimeProvider>,
    );

    const relationships = [
      {
        kind: "feedback" as const,
        source: "block.create-design-specification",
        target: "block.design-intent",
      },
      {
        kind: "flow" as const,
        source: "block.create-design-specification",
        target: "block.generate-geometry",
      },
    ];
    for (const relationship of relationships) {
      const binding = recoveryRelationshipHandleBinding(
        relationship.kind,
        relationship.source,
        relationship.target,
      );
      expect(binding.sourceHandle).not.toBe("");
      expect(binding.targetHandle).not.toBe("");
      const sourceHandle = screen.getByTestId(
        `workflow-recovery-routing-handle-${relationship.kind}-source-${relationship.source}`,
      );
      const targetHandle = screen.getByTestId(
        `workflow-recovery-routing-handle-${relationship.kind}-target-${relationship.target}`,
      );
      expect(sourceHandle).toHaveAttribute(
        "data-handleid",
        binding.sourceHandle,
      );
      expect(sourceHandle).toHaveAttribute("data-nodeid", relationship.source);
      expect(sourceHandle).toHaveClass("source");
      expect(targetHandle).toHaveAttribute(
        "data-handleid",
        binding.targetHandle,
      );
      expect(targetHandle).toHaveAttribute("data-nodeid", relationship.target);
      expect(targetHandle).toHaveClass("target");
    }
  });

  it("projects running and failed records without changing canonical or layout authority", () => {
    const projection = toDraftProjection(
      initialWorkflow,
      cloneLayout(initialLayout),
    );
    const run = initialRunProjection(
      initialWorkflow,
      "a".repeat(64),
      "2026-08-31T00:00:00Z",
    );
    run.state = "running";
    run.activeBlockId = "block.generate-geometry";
    run.activeRelationshipId = "rel.specification-to-geometry";
    run.steps["block.generate-geometry"] = {
      state: "running",
      label: "Running",
      detail: "Projected test record.",
    };
    const view = render(
      <RecoveryCanvasRuntimeProvider value={runtime(run)}>
        <ReactFlowRecoveryCanvas
          projection={projection}
          selectedSemanticId={null}
          onIntent={() => undefined}
        />
      </RecoveryCanvasRuntimeProvider>,
    );
    expect(
      screen.getByTestId("workflow-recovery-block-block.generate-geometry"),
    ).toHaveAttribute("data-run-state", "running");

    run.state = "failed";
    run.activeBlockId = "block.export-step";
    run.steps["block.export-step"] = {
      state: "failed",
      label: "Failed",
      detail: "Projected test failure.",
    };
    view.rerender(
      <RecoveryCanvasRuntimeProvider value={runtime(run)}>
        <ReactFlowRecoveryCanvas
          projection={projection}
          selectedSemanticId={null}
          onIntent={() => undefined}
        />
      </RecoveryCanvasRuntimeProvider>,
    );
    expect(
      screen.getByTestId("workflow-recovery-block-block.export-step"),
    ).toHaveAttribute("data-run-state", "failed");
  });

  it("fails closed before rendering an unknown run-record version", () => {
    const projection = toDraftProjection(
      initialWorkflow,
      cloneLayout(initialLayout),
    );
    const run = {
      ...initialRunProjection(),
      schemaVersion: "99.0.0",
    } as unknown as ReturnType<typeof initialRunProjection>;
    expect(() =>
      render(
        <RecoveryCanvasRuntimeProvider value={runtime(run)}>
          <ReactFlowRecoveryCanvas
            projection={projection}
            selectedSemanticId={null}
            onIntent={() => undefined}
          />
        </RecoveryCanvasRuntimeProvider>,
      ),
    ).toThrow("WFR-RUN-VERSION-UNSUPPORTED");
  });

  it("fails closed before rendering a run bound to another semantic digest", () => {
    const projection = toDraftProjection(
      initialWorkflow,
      cloneLayout(initialLayout),
    );
    const run = initialRunProjection(
      initialWorkflow,
      "b".repeat(64),
      "2026-08-31T00:00:00Z",
    );
    const value = runtime(run);
    value.runSubject = { ...value.runSubject, semanticSha256: "a".repeat(64) };
    expect(() =>
      render(
        <RecoveryCanvasRuntimeProvider value={value}>
          <ReactFlowRecoveryCanvas
            projection={projection}
            selectedSemanticId={null}
            onIntent={() => undefined}
          />
        </RecoveryCanvasRuntimeProvider>,
      ),
    ).toThrow("WFR-RUN-SUBJECT-MISMATCH");
  });

  it("keeps fit and stable selection usable with a 100-block projection", () => {
    const source = toDraftProjection(
      initialWorkflow,
      cloneLayout(initialLayout),
    );
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
      phases: [
        {
          ...source.phases[0]!,
          id: "phase.large-graph",
          semanticId: "phase.large-graph",
          name: "Large graph contract",
          block_ids: blocks.map((block) => block.semanticId),
          blocks,
        },
      ],
      connections: [],
      feedbackPaths: [],
    };
    const onIntent = vi.fn();
    const largeGraphRuntime = runtime();
    largeGraphRuntime.overlayRelationships = [];
    const started = performance.now();
    render(
      <RecoveryCanvasRuntimeProvider value={largeGraphRuntime}>
        <ReactFlowRecoveryCanvas
          projection={projection}
          selectedSemanticId={null}
          onIntent={onIntent}
        />
      </RecoveryCanvasRuntimeProvider>,
    );
    const elapsed = performance.now() - started;
    expect(screen.getByTestId("workflow-recovery-canvas")).toHaveAttribute(
      "data-detail-level",
      "compact",
    );
    expect(
      screen.getAllByTestId(/^workflow-recovery-block-block\.large-/),
    ).toHaveLength(100);
    fireEvent.click(screen.getByTestId("workflow-recovery-canvas-fit"));
    fireEvent.change(screen.getByTestId("workflow-recovery-find-input"), {
      target: { value: "block.large-100" },
    });
    fireEvent.click(screen.getByTestId("workflow-recovery-find-submit"));
    expect(onIntent).toHaveBeenCalledWith({
      type: "select",
      semanticId: "block.large-100",
    });
    expect(screen.getByRole("status")).toHaveTextContent(
      "Focused Large graph block 100",
    );
    expect(elapsed).toBeLessThan(5000);
  });
});
