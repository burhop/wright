import axe from "axe-core";
import {
  render,
  screen,
  within,
  type RenderResult,
} from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";
import packagedDefinitionRaw from "../../../../src/wright_engineering/static/process-definitions/product-definition-v1.json?raw";

vi.mock("../services/process-definition", async (importOriginal) => {
  const actual =
    await importOriginal<typeof import("../services/process-definition")>();
  return {
    ...actual,
    fetchProcessDefinition: vi.fn(),
  };
});

import { ProcessDefinitionPage } from "../components/pages/ProcessDefinitionPage";
import {
  decodeProcessDefinitionEnvelope,
  fetchProcessDefinition,
  type ProcessDefinition,
  type ProcessDefinitionEnvelope,
  type ProcessDefinitionFetchResult,
} from "../services/process-definition";

const packagedDefinition = JSON.parse(packagedDefinitionRaw) as unknown;
const sourceSha256 =
  "6a02f71e35f9c3d9a3184509ddeab2df251cff454b6d6ce66d7244d015eefdef";

const envelope: ProcessDefinitionEnvelope = decodeProcessDefinitionEnvelope({
  definition: packagedDefinition,
  source_kind: "packaged_fallback",
  source_id: "process-definitions/product-definition-v1.json",
  source_sha256: sourceSha256,
  source_available: true,
  etag: "e".repeat(64),
  supported_schema_versions: ["1.0.0"],
});

const currentResult: ProcessDefinitionFetchResult = {
  state: "current",
  status: 200,
  etag: `"${envelope.etag}"`,
  envelope,
};

const fetchDefinition = vi.mocked(fetchProcessDefinition);
const originalInnerWidth = window.innerWidth;
const originalMatchMedia = window.matchMedia;

type RegistryEntity =
  | ProcessDefinition["phases"][number]
  | ProcessDefinition["actions"][number]
  | ProcessDefinition["ports"][number]
  | ProcessDefinition["gates"][number]
  | ProcessDefinition["feedback_paths"][number]
  | ProcessDefinition["artifacts"][number];

function canonicalSemanticIds(definition: ProcessDefinition): string[] {
  return [
    definition.process_id,
    ...definition.phases.map(({ id }) => id),
    ...definition.actions.map(({ id }) => id),
    ...definition.ports.map(({ id }) => id),
    ...definition.gates.map(({ id }) => id),
    ...definition.feedback_paths.map(({ id }) => id),
    ...definition.artifacts.map(({ id }) => id),
  ].sort();
}

function projectionSemanticIds(root: HTMLElement): string[] {
  const nodes = [
    ...(root.hasAttribute("data-semantic-id") ? [root] : []),
    ...root.querySelectorAll<HTMLElement>("[data-semantic-id]"),
  ];
  return nodes.map((node) => node.dataset.semanticId ?? "").sort();
}

function semanticNode(root: HTMLElement, id: string): HTMLElement {
  const match =
    root.dataset.semanticId === id
      ? root
      : root.querySelector<HTMLElement>(`[data-semantic-id="${id}"]`);
  expect(match, `semantic node ${id} should be rendered`).not.toBeNull();
  return match as HTMLElement;
}

function expectVisibleIdentityAndLabel(
  root: HTMLElement,
  entity: RegistryEntity,
): void {
  const node = semanticNode(root, entity.id);
  expect(node).toHaveTextContent(entity.id);
  if ("title" in entity) expect(node).toHaveTextContent(entity.title);
  if ("name" in entity) expect(node).toHaveTextContent(entity.name);
}

async function renderReady(): Promise<RenderResult> {
  fetchDefinition.mockResolvedValue(currentResult);
  const view = render(<ProcessDefinitionPage />);
  await within(view.container).findByTestId("process-definition-text");
  return view;
}

function reducedMotionMedia(query: string): MediaQueryList {
  return {
    matches: query === "(prefers-reduced-motion: reduce)",
    media: query,
    onchange: null,
    addListener: vi.fn(),
    removeListener: vi.fn(),
    addEventListener: vi.fn(),
    removeEventListener: vi.fn(),
    dispatchEvent: vi.fn(),
  };
}

describe.sequential("ProcessDefinitionPage", () => {
  beforeEach(() => {
    fetchDefinition.mockReset();
  });

  afterEach(() => {
    document.documentElement.style.removeProperty("zoom");
    Object.defineProperty(window, "innerWidth", {
      configurable: true,
      value: originalInnerWidth,
    });
    Object.defineProperty(window, "matchMedia", {
      configurable: true,
      writable: true,
      value: originalMatchMedia,
    });
  });

  it("shows a bounded loading state and never presents partial definition content", async () => {
    let resolveRequest!: (result: ProcessDefinitionFetchResult) => void;
    fetchDefinition.mockReturnValue(
      new Promise((resolve) => {
        resolveRequest = resolve;
      }),
    );

    render(<ProcessDefinitionPage />);

    const page = screen.getByTestId("page-process-definition");
    const loading = screen.getByTestId("process-definition-loading");
    expect(page).toBeInTheDocument();
    expect(loading).toHaveAttribute("role", "status");
    expect(loading).toHaveAttribute("aria-live", "polite");
    expect(loading).toHaveAttribute("aria-busy", "true");
    expect(screen.queryByTestId("process-definition-text")).toBeNull();
    expect(screen.queryByTestId("process-definition-diagram")).toBeNull();

    resolveRequest(currentResult);

    expect(
      await screen.findByTestId("process-definition-text"),
    ).toBeInTheDocument();
    expect(screen.getByTestId("process-definition-title")).toHaveTextContent(
      envelope.definition.title,
    );
    expect(screen.queryByTestId("process-definition-loading")).toBeNull();
  });

  it("renders complete semantic text from the packaged definition", async () => {
    await renderReady();

    const definition = envelope.definition;
    const title = screen.getByTestId("process-definition-title");
    const text = screen.getByTestId("process-definition-text");
    expect(title.tagName).toBe("H1");
    expect(title).toHaveTextContent(definition.title);
    expect(text).toHaveTextContent(definition.process_id);
    expect(text).toHaveTextContent(definition.purpose);

    for (const phase of definition.phases) {
      const node = semanticNode(text, phase.id);
      expect(node).toHaveTextContent(phase.id);
      expect(node).toHaveTextContent(phase.title);
      expect(node).toHaveTextContent(phase.purpose);
      for (const actionId of phase.action_ids) {
        expect(node).toHaveTextContent(actionId);
      }
    }

    for (const action of definition.actions) {
      const node = semanticNode(text, action.id);
      expect(node).toHaveTextContent(action.id);
      expect(node).toHaveTextContent(action.title);
      expect(node).toHaveTextContent(action.purpose);
      for (const reference of [
        ...action.input_port_ids,
        ...action.output_port_ids,
        ...action.gate_ids,
        ...action.feedback_path_ids,
        ...action.expected_artifact_ids,
      ]) {
        expect(node).toHaveTextContent(reference);
      }
    }

    for (const port of definition.ports) {
      const node = semanticNode(text, port.id);
      expect(node).toHaveTextContent(port.id);
      expect(node).toHaveTextContent(port.name);
      expect(node).toHaveTextContent(
        port.direction === "input" ? /Input ·/ : /Output ·/,
      );
      expect(node).toHaveTextContent(port.value_type);
      expect(node).toHaveTextContent(port.description);
      expect(node).toHaveTextContent(port.owner_action_id);
      if (port.source_port_id !== null) {
        expect(node).toHaveTextContent(port.source_port_id);
      }
    }

    for (const gate of definition.gates) {
      const node = semanticNode(text, gate.id);
      expect(node).toHaveTextContent(gate.id);
      expect(node).toHaveTextContent(gate.title);
      expect(node).toHaveTextContent(gate.condition);
      expect(
        node.closest(`[data-semantic-id="${gate.owner_action_id}"]`),
      ).not.toBeNull();
      expect(node).toHaveTextContent(gate.pass_target_id);
      expect(node).toHaveTextContent(gate.fail_target_id);
    }

    for (const feedback of definition.feedback_paths) {
      const node = semanticNode(text, feedback.id);
      expect(node).toHaveTextContent(feedback.id);
      expect(node).toHaveTextContent(feedback.from_id);
      expect(node).toHaveTextContent(feedback.to_id);
      expect(node).toHaveTextContent(feedback.reason);
    }

    for (const artifact of definition.artifacts) {
      const node = semanticNode(text, artifact.id);
      expect(node).toHaveTextContent(artifact.id);
      expect(node).toHaveTextContent(artifact.name);
      expect(node).toHaveTextContent(artifact.artifact_type);
      expect(node).toHaveTextContent(artifact.purpose);
      expect(node).toHaveTextContent(artifact.produced_by_action_id);
    }
  });

  it("renders exactly the canonical semantic identities in both projections", async () => {
    await renderReady();

    const definition = envelope.definition;
    const expected = canonicalSemanticIds(definition);
    const text = screen.getByTestId("process-definition-text");
    const diagram = screen.getByTestId("process-definition-diagram");
    const textIds = projectionSemanticIds(text);
    const diagramIds = projectionSemanticIds(diagram);

    expect(textIds).toEqual(expected);
    expect(diagramIds).toEqual(expected);
    expect(textIds).toEqual(diagramIds);
    expect(new Set(textIds).size).toBe(textIds.length);
    expect(new Set(diagramIds).size).toBe(diagramIds.length);

    for (const entity of [
      ...definition.phases,
      ...definition.actions,
      ...definition.ports,
      ...definition.gates,
      ...definition.feedback_paths,
      ...definition.artifacts,
    ]) {
      expectVisibleIdentityAndLabel(text, entity);
      expectVisibleIdentityAndLabel(diagram, entity);
    }
  });

  it("traces a review input through its gate, feedback, release, and artifact relationships", async () => {
    await renderReady();

    const text = screen.getByTestId("process-definition-text");
    const reviewInput = semanticNode(text, "model-review-input");
    expect(reviewInput).toHaveTextContent(/Owner:\s*review-product-definition/);
    expect(reviewInput).toHaveTextContent(/Source:\s*product-model/);

    const reviewAction = semanticNode(text, "review-product-definition");
    for (const relationship of [
      "review-decision",
      "definition-approval",
      "revise-definition",
      "definition-review-record",
    ]) {
      expect(semanticNode(reviewAction, relationship)).toHaveTextContent(
        relationship,
      );
    }

    const approvalGate = semanticNode(reviewAction, "definition-approval");
    expect(approvalGate).toHaveTextContent(
      /Pass\s*→\s*release-product-definition/,
    );
    expect(approvalGate).toHaveTextContent(/Fail\s*→\s*define-product/);

    const releaseAction = semanticNode(text, "release-product-definition");
    for (const relationship of [
      "approved-model-input",
      "approval-input",
      "released-package",
      "released-definition-package",
    ]) {
      expect(semanticNode(releaseAction, relationship)).toHaveTextContent(
        relationship,
      );
    }

    const artifact = semanticNode(releaseAction, "released-definition-package");
    expect(artifact).toHaveTextContent(/Expected artifact/);
    expect(artifact).toHaveTextContent(
      /Produced by\s*release-product-definition/,
    );
  });

  it("names every action category and says None declared for each empty one", async () => {
    await renderReady();
    const text = screen.getByTestId("process-definition-text");

    for (const action of envelope.definition.actions) {
      const actionNode = semanticNode(text, action.id);
      const actionView = within(actionNode);
      expect(
        actionView.getByText(/^Inputs?(?: ports?)?$/i),
      ).toBeInTheDocument();
      expect(
        actionView.getByText(/^Outputs?(?: ports?)?$/i),
      ).toBeInTheDocument();
      expect(actionView.getByText(/^Gates?$/i)).toBeInTheDocument();
      expect(
        actionView.getByText(/^Feedback(?: paths?)?$/i),
      ).toBeInTheDocument();
      expect(
        actionView.getByText(/^Expected artifacts?$/i),
      ).toBeInTheDocument();

      const emptyCategoryCount = [
        action.input_port_ids,
        action.output_port_ids,
        action.gate_ids,
        action.feedback_path_ids,
        action.expected_artifact_ids,
      ].filter((ids) => ids.length === 0).length;
      expect(actionView.queryAllByText(/^None declared\.?$/i)).toHaveLength(
        emptyCategoryCount,
      );
    }
  });

  it("uses a native keyboard-operable disclosure for exact source identity", async () => {
    const user = userEvent.setup();
    await renderReady();

    const details = screen.getByTestId("process-definition-source-details");
    const toggle = screen.getByTestId("process-definition-source-toggle");
    expect(details.tagName).toBe("DETAILS");
    expect(toggle.tagName).toBe("SUMMARY");
    expect(details).not.toHaveAttribute("open");

    toggle.focus();
    expect(toggle).toHaveFocus();
    // jsdom does not implement the browser's Enter default action for a
    // <summary>. Prove that the focused control is native, then use the same
    // activation event that a browser dispatches for Enter. T012 covers the
    // real keyboard default action in Chromium.
    await user.click(toggle);

    expect(details).toHaveAttribute("open");
    expect(details).toHaveTextContent(envelope.definition.schema_version);
    expect(details).toHaveTextContent(String(envelope.definition.revision));
    expect(details).toHaveTextContent(envelope.definition.content_sha256);
    expect(details).toHaveTextContent(envelope.source_id);
    expect(details).toHaveTextContent(envelope.source_sha256);
    expect(details).toHaveTextContent(envelope.source_kind);
    expect(details.querySelector("a")).toBeNull();
  });

  it("keeps the logical source and the complete definition view read-only", async () => {
    const user = userEvent.setup();
    const view = await renderReady();

    const boundary = screen.getByRole("note", {
      name: "Read-only definition boundary",
    });
    expect(boundary).toHaveTextContent(
      "Definition only — not evidence that a process ran or an artifact exists",
    );
    expect(fetchDefinition).toHaveBeenCalledTimes(1);
    expect(fetchDefinition).toHaveBeenCalledWith(
      undefined,
      expect.any(AbortSignal),
    );

    const details = screen.getByTestId("process-definition-source-details");
    await user.click(screen.getByTestId("process-definition-source-toggle"));
    expect(details).toHaveTextContent(
      "process-definitions/product-definition-v1.json",
    );
    expect(details).toHaveTextContent(
      "Package-relative identity only; not a filesystem path or external URL.",
    );
    expect(details.querySelector("a[href], [role='link']")).toBeNull();
    expect(
      view.container.querySelector(
        "form, button, input, textarea, select, [contenteditable='true']",
      ),
    ).toBeNull();
    expect(fetchDefinition).toHaveBeenCalledTimes(1);

    await user.click(screen.getByTestId("process-definition-source-toggle"));
    expect(fetchDefinition).toHaveBeenCalledTimes(1);
  });

  it("communicates direction, gate outcomes, feedback, and artifacts without color", async () => {
    await renderReady();
    const diagram = screen.getByTestId("process-definition-diagram");

    expect(diagram).toHaveTextContent(/Input:/i);
    expect(diagram).toHaveTextContent(/Output:/i);
    expect(diagram).toHaveTextContent(/\bPass\b/i);
    expect(diagram).toHaveTextContent(/\bFail\b/i);
    expect(diagram).toHaveTextContent(/\bFeedback\b/i);
    expect(diagram).toHaveTextContent(/Expected artifact/i);

    for (const port of envelope.definition.ports) {
      expect(semanticNode(diagram, port.id)).toHaveTextContent(
        new RegExp(`\\b${port.direction}\\b`, "i"),
      );
    }
  });

  it("has no serious or critical Axe findings in the ready component state", async () => {
    const view = await renderReady();
    const result = await axe.run(view.container, {
      rules: {
        "color-contrast": { enabled: false },
      },
    });

    expect(
      result.violations.filter((violation) =>
        ["serious", "critical"].includes(violation.impact ?? ""),
      ),
    ).toEqual([]);
  });

  it("preserves complete semantic structure under narrow, zoom, and reduced-motion declarations", async () => {
    Object.defineProperty(window, "innerWidth", {
      configurable: true,
      value: 320,
    });
    Object.defineProperty(window, "matchMedia", {
      configurable: true,
      writable: true,
      value: vi.fn(reducedMotionMedia),
    });
    document.documentElement.style.setProperty("zoom", "2");
    window.dispatchEvent(new Event("resize"));

    await renderReady();

    const expected = canonicalSemanticIds(envelope.definition);
    expect(window.innerWidth).toBe(320);
    expect(window.matchMedia("(prefers-reduced-motion: reduce)").matches).toBe(
      true,
    );
    expect(document.documentElement.style.getPropertyValue("zoom")).toBe("2");
    expect(
      projectionSemanticIds(screen.getByTestId("process-definition-text")),
    ).toEqual(expected);
    expect(
      projectionSemanticIds(screen.getByTestId("process-definition-diagram")),
    ).toEqual(expected);
    expect(
      screen.getByTestId("process-definition-source-toggle"),
    ).toBeInTheDocument();
  });

  it("records one warm-up and 20 serial response-to-render observations without a timing gate", async () => {
    fetchDefinition.mockResolvedValue(currentResult);

    const observe = async (): Promise<number> => {
      const startedAt = performance.now();
      const view = render(<ProcessDefinitionPage />);
      await within(view.container).findByTestId("process-definition-text");
      expect(
        projectionSemanticIds(
          within(view.container).getByTestId("process-definition-text"),
        ),
      ).toEqual(canonicalSemanticIds(envelope.definition));
      const durationMs = performance.now() - startedAt;
      view.unmount();
      return durationMs;
    };

    const warmupMs = await observe();
    const observationsMs: number[] = [];
    for (let index = 0; index < 20; index += 1) {
      observationsMs.push(await observe());
    }
    const sorted = [...observationsMs].sort((left, right) => left - right);
    const p95Ms = sorted[Math.ceil(0.95 * sorted.length) - 1];

    expect(observationsMs).toHaveLength(20);
    expect(observationsMs.every(Number.isFinite)).toBe(true);
    expect(observationsMs.every((duration) => duration >= 0)).toBe(true);
    expect(p95Ms).toBe(sorted[18]);
    expect(fetchDefinition).toHaveBeenCalledTimes(21);

    console.info(
      "PROCESS_DEFINITION_RENDER_DIAGNOSTIC",
      JSON.stringify({
        host: {
          runtime: "vitest-jsdom",
          component_order: "describe.sequential",
          evidence_boundary:
            "The checkpoint runner must declare the host and select this file alone before treating timings as isolated evidence.",
        },
        sample: "packaged product-definition-v1",
        warmup_ms: warmupMs,
        observations_ms: observationsMs,
        nearest_rank_p95_ms: p95Ms,
        gating_threshold_ms: null,
      }),
    );
  });
});
