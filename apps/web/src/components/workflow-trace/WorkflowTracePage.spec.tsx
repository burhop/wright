import { fireEvent, render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { describe, expect, it, vi } from "vitest";

import {
  failedInspection,
  succeededInspection,
} from "../workflows/rivet-run-inspector.fixtures";
import { TraceExportMenu } from "./TraceExportMenu";
import { TraceInspector } from "./TraceInspector";
import { WorkflowTracePage } from "./WorkflowTracePage";
import { RivetRunResult } from "../workflows/RivetRunResult";

const renderPage = (inspection = succeededInspection) =>
  render(
    <WorkflowTracePage
      inspection={inspection}
      recentRuns={[inspection.run]}
      currentRevision={inspection.run.revision}
      elapsedMs={inspection.run.duration_ms || 0}
      onSelectRun={vi.fn()}
    />,
  );

describe("WorkflowTracePage", () => {
  it("shows deliverables before process, prompts, inputs, and technical evidence", () => {
    renderPage();
    expect(screen.getByRole("region", { name: "Run results" })).toBeVisible();
    expect(screen.getByText("Created artifacts")).toBeVisible();
    expect(screen.queryByText(/Validation shown here/)).not.toBeInTheDocument();
    expect(
      screen.queryByRole("region", { name: "Executed process" }),
    ).not.toBeInTheDocument();
  });

  it("keeps a failed run truthful and exposes partial results without a new verdict", () => {
    renderPage(failedInspection);
    expect(
      screen.getByRole("region", { name: "Run error or blocker" }),
    ).toBeVisible();
    expect(screen.getByText("Created artifacts")).toBeVisible();
    expect(screen.queryByText(/unresolved concern/i)).not.toBeInTheDocument();
    expect(screen.queryByText(/engineering score/i)).not.toBeInTheDocument();
  });

  it("offers report-only and full-data packages as separate commands", async () => {
    const user = userEvent.setup();
    const exportTrace = vi.fn();
    render(<TraceExportMenu onExportTrace={exportTrace} />);
    fireEvent.click(screen.getByText("Export review"));
    await user.click(screen.getByRole("button", { name: "Report ZIP" }));
    await user.click(
      screen.getByRole("button", { name: "Report and data ZIP" }),
    );
    expect(exportTrace.mock.calls).toEqual([["report_only"], ["full_data"]]);
  });

  it("shows producer-authored validation against its exact subject", async () => {
    const user = userEvent.setup();
    renderPage({
      ...succeededInspection,
      evidence_records: [
        {
          evidence_id: "evidence-1",
          producer: "feature-082-validator",
          producer_version: "1.0",
          kind: "validation",
          statement: "Checked retained artifact revision two.",
          recorded_outcome: "pass",
          subjects: [
            {
              subject_kind: "artifact_version",
              subject_id: "artifact-2",
              revision: "2",
              digest: "a".repeat(64),
            },
          ],
          supporting_refs: [],
          supersedes_id: null,
        },
      ],
    });
    await user.click(screen.getByRole("button", { name: "Evidence" }));
    expect(screen.getByText("validation: pass")).toBeVisible();
    fireEvent.click(screen.getByText("validation: pass"));
    expect(screen.getByText("feature-082-validator 1.0")).toBeVisible();
    expect(screen.getByText("artifact_version:artifact-2@2")).toBeVisible();
  });

  it("navigates between an artifact and its exact producer evidence", async () => {
    const user = userEvent.setup();
    renderPage({
      ...succeededInspection,
      evidence_records: [
        {
          evidence_id: "evidence-artifact-1",
          producer: "feature-082-validator",
          producer_version: "1.0",
          kind: "validation",
          statement: "Checked the retained CAD artifact.",
          recorded_outcome: "pass",
          subjects: [
            {
              subject_kind: "artifact_version",
              subject_id: "artifact-1",
              revision: "1",
              digest: "a".repeat(64),
            },
          ],
          supporting_refs: [],
          supersedes_id: null,
        },
      ],
    });
    await user.click(
      screen.getByRole("button", { name: "View recorded evidence (1)" }),
    );
    expect(
      screen.getByText("Checked the retained CAD artifact."),
    ).toBeVisible();
    await user.click(
      screen.getByRole("button", { name: "View subject model" }),
    );
    expect(screen.getByRole("region", { name: "Run results" })).toBeVisible();
  });

  it("discloses the recorded prompt and configuration only after selection", () => {
    const inspection = {
      ...succeededInspection,
      graph: {
        graph_id: "main",
        name: "Main",
        nodes: [
          {
            node_id: "node-1",
            node_type: "chat",
            label: "Create design",
            order: 1,
            x: 0,
            y: 0,
            width: 220,
            prompt: "Use requirement revision 3.",
            configuration: { model: "reviewed-model" },
          },
        ],
        connections: [],
      },
      steps: [{ ...succeededInspection.steps[0], node_id: "node-1" }],
    };
    render(
      <TraceInspector
        inspection={inspection}
        selection={{ kind: "node", id: "node-1" }}
        selectedStep={null}
        onClose={vi.fn()}
      />,
    );
    expect(screen.getByText("Executed prompt")).toBeVisible();
    expect(screen.queryByText("Use requirement revision 3.")).not.toBeVisible();
    fireEvent.click(screen.getByText("Executed prompt"));
    expect(screen.getByText("Use requirement revision 3.")).toBeVisible();
  });

  it("lists each recorded connection traversal and opens its target attempt", () => {
    const selectStep = vi.fn();
    const inspection = {
      ...succeededInspection,
      graph: {
        graph_id: "main",
        name: "Main",
        nodes: [],
        connections: [
          {
            connection_id: "source:target:result",
            source_node_id: "source",
            target_node_id: "target",
            source_port: "result",
            target_port: "input",
            label: "result",
            traversals: [
              {
                traversal_id: "traversal-1",
                sequence: 2,
                source_step_id: "source-attempt-1",
                target_step_id: "target-attempt-1",
                source_attempt: 1,
                target_attempt: 1,
              },
              {
                traversal_id: "traversal-2",
                sequence: 4,
                source_step_id: "source-attempt-2",
                target_step_id: "target-attempt-2",
                source_attempt: 2,
                target_attempt: 2,
              },
            ],
          },
        ],
      },
      steps: [
        {
          ...succeededInspection.steps[0],
          step_id: "source-attempt-1",
          node_id: "source",
          label: "Source",
          attempt: 1,
        },
        {
          ...succeededInspection.steps[0],
          step_id: "target-attempt-1",
          node_id: "target",
          label: "Target",
          attempt: 1,
        },
        {
          ...succeededInspection.steps[0],
          step_id: "source-attempt-2",
          node_id: "source",
          label: "Source",
          attempt: 2,
        },
        {
          ...succeededInspection.steps[0],
          step_id: "target-attempt-2",
          node_id: "target",
          label: "Target",
          attempt: 2,
        },
      ],
    };
    render(
      <TraceInspector
        inspection={inspection}
        selection={{ kind: "connection", id: "source:target:result" }}
        selectedStep={null}
        onClose={vi.fn()}
        onSelectStep={selectStep}
      />,
    );
    expect(screen.getByText("Attempt 1 to attempt 1")).toBeVisible();
    expect(screen.getByText("Attempt 2 to attempt 2")).toBeVisible();
    fireEvent.click(screen.getAllByRole("button", { name: "Open Target" })[1]);
    expect(selectStep).toHaveBeenCalledWith(
      expect.objectContaining({ step_id: "target-attempt-2" }),
    );
  });

  it("keeps unsupported CAD useful through the original-file fallback", () => {
    const openArtifact = vi.fn();
    render(
      <RivetRunResult
        result={{
          result_id: "artifact:step-1",
          name: "housing.step",
          origin: "artifact",
          kind: "artifact",
          data_type: "model/step",
          value: null,
          preview: "STEP model",
          complete: true,
          evidence_state: "available",
          truncation_reason: null,
          original_bytes: 1024,
          retained_bytes: 1024,
          digest: "a".repeat(64),
          redaction_count: 0,
          artifact: {
            artifact_id: "step-1",
            media_type: "model/step",
            sha256: "a".repeat(64),
            bytes: 1024,
            label: "housing.step",
          },
        }}
        onOpenArtifact={openArtifact}
      />,
    );
    expect(
      screen.getByText(/Interactive geometry preview is unavailable/),
    ).toBeVisible();
    fireEvent.click(screen.getByRole("button", { name: "Open artifact" }));
    expect(openArtifact).toHaveBeenCalledWith(
      expect.objectContaining({ artifact_id: "step-1" }),
    );
  });

  it("renders a verified retained raster preview on the results card", () => {
    render(
      <RivetRunResult
        result={{
          result_id: "artifact:preview-1",
          name: "mesh-preview.png",
          origin: "artifact",
          kind: "artifact",
          data_type: "image/png",
          value: "runs/example/artifacts/mesh-preview.png",
          preview: "mesh-preview.png",
          complete: true,
          evidence_state: "available",
          truncation_reason: null,
          original_bytes: 1024,
          retained_bytes: 1024,
          digest: "a".repeat(64),
          redaction_count: 0,
          artifact: {
            artifact_id: "preview-1",
            media_type: "image/png",
            preview_url:
              "/api/workspace/workflow-sources/run-trace/artifact?id=preview-1",
          },
        }}
      />,
    );
    expect(
      screen.getByRole("img", {
        name: "Recorded preview for mesh-preview.png",
      }),
    ).toHaveAttribute(
      "src",
      "/api/workspace/workflow-sources/run-trace/artifact?id=preview-1",
    );
  });
});
