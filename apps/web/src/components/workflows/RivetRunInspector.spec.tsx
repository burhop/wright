import { fireEvent, render, screen, within } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { describe, expect, it, vi } from "vitest";

import {
  cancelledInspection,
  emptyInspection,
  failedInspection,
  historicalRun,
  runningInspection,
  succeededInspection,
} from "./rivet-run-inspector.fixtures";
import { RivetRunInspector } from "./RivetRunInspector";

const renderInspector = (
  inspection = succeededInspection,
  overrides: Partial<React.ComponentProps<typeof RivetRunInspector>> = {},
) =>
  render(
    <RivetRunInspector
      inspection={inspection}
      recentRuns={[inspection.run, historicalRun]}
      currentRevision={2}
      elapsedMs={inspection.run.duration_ms || 2500}
      onSelectRun={vi.fn()}
      onFocusStep={vi.fn()}
      onRerun={vi.fn()}
      onExportEvidence={vi.fn()}
      {...overrides}
    />,
  );

describe("RivetRunInspector", () => {
  it("opens for running state and can collapse to its compact summary", async () => {
    const user = userEvent.setup();
    renderInspector(runningInspection);
    expect(await screen.findByTestId("rivet-run-state-running")).toBeVisible();
    expect(screen.getByTestId("rivet-run-inspector")).toHaveClass("is-open");
    await user.click(screen.getByRole("button", { name: /run inspector/i }));
    expect(screen.getByTestId("rivet-run-inspector")).toHaveClass(
      "is-collapsed",
    );
  });

  it("renders every retained output type and bounded/redacted disclosures", async () => {
    const user = userEvent.setup();
    renderInspector();
    expect(
      await screen.findByTestId("rivet-run-result-empty"),
    ).toHaveTextContent("null");
    expect(screen.getByTestId("rivet-run-result-dimensions")).toHaveTextContent(
      "width: 4",
    );
    expect(screen.getByTestId("rivet-run-result-items")).toHaveTextContent(
      "- a",
    );
    expect(screen.getByRole("link", { name: "Open link" })).toHaveAttribute(
      "href",
      "https://example.test/report",
    );
    expect(screen.getByTestId("rivet-run-result-large")).toHaveTextContent(
      "Incomplete",
    );
    expect(screen.getByTestId("rivet-run-result-secret")).toHaveTextContent(
      "Redacted",
    );
    expect(screen.getByText("Created artifacts")).toBeVisible();
    expect(screen.getByText("Result values")).toBeVisible();
    await user.click(screen.getByRole("button", { name: "Expand" }));
    expect(screen.getByRole("button", { name: "Collapse" })).toBeVisible();
  });

  it("states explicitly when a successful run has no outputs", async () => {
    renderInspector(emptyInspection);
    expect(
      await screen.findByText("This run succeeded with no final outputs."),
    ).toBeVisible();
  });

  it("opens an authoritative artifact through the run-scoped host callback", async () => {
    const user = userEvent.setup();
    const onOpenArtifact = vi.fn();
    renderInspector(succeededInspection, { onOpenArtifact });

    await user.click(
      await screen.findByRole("button", { name: "Open artifact" }),
    );

    expect(onOpenArtifact).toHaveBeenCalledTimes(1);
    expect(onOpenArtifact).toHaveBeenCalledWith({
      artifact_id: "artifact-1",
      label: "CAD model",
    });
  });

  it("preserves an API-retained empty text output as available", async () => {
    renderInspector({
      ...succeededInspection,
      final_outputs: [
        {
          result_id: "final_output:output",
          name: "output",
          origin: "final_output",
          kind: "text",
          data_type: "text",
          evidence_state: "available",
          value: "",
          preview: "",
          complete: true,
          truncation_reason: null,
          original_bytes: 2,
          retained_bytes: 2,
          digest:
            "12ae32cb1ec02d01eda3581b127c1fee3b0dc53572ed6baf239721a03d82e126",
          redaction_count: 0,
          artifact: null,
        },
      ],
      completeness: {
        ...succeededInspection.completeness,
        outputs_complete: true,
        reasons: [],
      },
    });

    expect(
      await screen.findByTestId("rivet-run-result-value-output"),
    ).toHaveTextContent("Empty text (0 characters)");
    expect(screen.getByTestId("rivet-run-result-output")).toHaveTextContent(
      "available",
    );
  });

  it("orders the engineering tabs and discloses retained run inputs", async () => {
    const user = userEvent.setup();
    const input = {
      ...succeededInspection.final_outputs[1],
      result_id: "run-input-prompt",
      name: "prompt",
      origin: "run_input",
      value: "Create a bracket",
      preview: "Create a bracket",
    };
    renderInspector({
      ...succeededInspection,
      run_inputs: [input],
      inputs_state: "available",
    });
    const navigation = screen.getByRole("navigation", {
      name: "Run Inspector sections",
    });
    expect(
      within(navigation)
        .getAllByRole("button")
        .map((button) => button.textContent),
    ).toEqual(["Inputs", "Outputs", "Steps", "Diagnosis", "History"]);
    await user.click(screen.getByRole("button", { name: "Inputs" }));
    expect(screen.getByTestId("rivet-run-result-prompt")).toHaveTextContent(
      "Create a bracket",
    );
  });

  it("shows compact safe input and output states on the owning box", async () => {
    const user = userEvent.setup();
    const value = {
      ...succeededInspection.final_outputs[2],
      result_id: "node-input-length",
      name: "length",
      origin: "node_input",
      value: 25,
      preview: "25",
      data_type: "number",
    };
    renderInspector({
      ...succeededInspection,
      steps: [
        {
          ...succeededInspection.steps[0],
          inputs: [value],
          outputs: [],
          input_state: "available",
          output_state: "not-retained",
        },
      ],
    });
    await user.click(screen.getByRole("button", { name: "Steps" }));
    await user.click(screen.getByText("Inspect box values"));
    expect(screen.getByText("length")).toBeVisible();
    expect(screen.getByText("not retained")).toBeVisible();
  });

  it("auto-opens failed diagnosis, preserves upstream steps, and offers only safe full rerun", async () => {
    const user = userEvent.setup();
    const rerun = vi.fn();
    renderInspector(failedInspection, { onRerun: rerun });
    expect(await screen.findByText(/connection ended/i)).toBeVisible();
    expect(screen.getByText("Failed box: Create feature")).toBeVisible();
    expect(screen.getByText(/partial change/i)).toBeVisible();
    expect(
      screen.queryByRole("button", { name: /retry step/i }),
    ).not.toBeInTheDocument();
    await user.click(
      screen.getByRole("button", { name: /run saved revision again/i }),
    );
    expect(rerun).toHaveBeenCalledTimes(1);
    await user.click(screen.getByRole("button", { name: "Steps" }));
    expect(screen.getByText(/Inspect CAD/)).toBeVisible();
    expect(screen.getByText(/Create feature/)).toBeVisible();
  });

  it("explains failed zero-output runs and links directly to Diagnosis", async () => {
    const user = userEvent.setup();
    renderInspector({
      ...failedInspection,
      run: { ...failedInspection.run, has_outputs: false },
      final_outputs: [],
    });

    await user.click(screen.getByRole("button", { name: "Outputs" }));
    expect(
      screen.getByText(/no final outputs because it failed/i),
    ).toBeVisible();
    await user.click(screen.getByRole("button", { name: "View Diagnosis" }));
    expect(screen.getByText("Failed box: Create feature")).toBeVisible();
  });

  it("shows cancellation and technical details without residue warning when cleanup is known", async () => {
    const user = userEvent.setup();
    renderInspector(cancelledInspection);
    expect(
      await screen.findByText(/workflow run was cancelled/i),
    ).toBeVisible();
    expect(screen.queryByText(/partial change/i)).not.toBeInTheDocument();
    fireEvent.click(screen.getByText("Technical details"));
    expect(screen.getByText("RIVET_RUN_CANCELLED")).toBeVisible();
    expect(screen.getByText("trace-child")).toBeVisible();
    await user.click(screen.getByRole("button", { name: "History" }));
    expect(screen.getByText(/Revision 1 · historical/)).toBeVisible();
  });
});
