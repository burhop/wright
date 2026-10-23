import { useState } from "react";
import { afterEach, describe, expect, it, vi } from "vitest";
import {
  cleanup,
  act,
  fireEvent,
  render,
  screen,
  waitFor,
  within,
} from "@testing-library/react";
import {
  ProcessUI,
  ReasonNotice,
  ActionButton,
  ReadinessPanel,
  ProgressPanel,
  InputEditor,
  ResultCard,
  EvidenceReference,
  CheckpointCard,
  SchemaField,
  parseToolpaths,
  parseRecordedToolpaths,
  parseCsv,
  DataTable,
  NumericPlot,
  ImageThumbnail,
  RepresentationViewer,
  RepresentationDownload,
  FindingsPanel,
  ScalarFieldPlot,
  CsvNumericInspector,
  RecordedToolpathPreview,
  type ToolpathDocument,
} from "@wright/ui-kit";
import type {
  InputBinding,
  InputDefinition,
  Observation,
  OutputRef,
} from "@wright/process-client";

import { ProcessClientError } from "@wright/process-client";

const hash = "a".repeat(64);
const input: InputDefinition = {
  input_id: "prompt",
  block_id: "intent",
  port_id: "out",
  title: "What should Wright make?",
  required: true,
  value_schema: { type: "string" },
};
const reason = {
  code: "INPUT_REQUIRED",
  message: "Choose a material before starting.",
  correction: "Return to material choices.",
};
const observation: Observation = {
  observation_id: "operation",
  provider_binding: "configured-tool",
  state: "running",
  observed_at: "2026-09-30T12:00:00Z",
  stale_after: "2026-09-30T12:01:00Z",
  progress_percent: 25,
  estimated_remaining_seconds: 120,
  activity: "Measuring geometry",
};
const output: OutputRef = {
  result_id: "run:mesh:output",
  step_id: "mesh",
  port_id: "output",
  role: "geometry",
  title: "Repaired geometry",
  representations: [
    { artifact_ref: "outputs/mesh.stl", sha256: hash, media_type: "model/stl" },
  ],
  assessments: [
    {
      assessment_id: "check-one",
      subject_digest: hash,
      currentness: "current",
      outcome: "fail",
    },
  ],
};
afterEach(() => {
  cleanup();
  vi.restoreAllMocks();
});

describe("public kit presentation and authority", () => {
  it.each([
    ["results/run-one/mesh.stl", "results/run-one/mesh.stl", "mesh.stl"],
    ["results\\run-one\\mesh.stl", "results\\run-one\\mesh.stl", "mesh.stl"],
    [
      "Stress / strain comparison",
      "results/metrics.csv",
      "Stress / strain comparison",
    ],
    ["Attempt 1: mesh.stl", "results/run-one/mesh.stl", "Attempt 1: mesh.stl"],
    ["results/unrelated.stl", "results/mesh.stl", "results/unrelated.stl"],
  ])(
    "presents %s without changing its evidence target",
    (title, path, heading) => {
      const reference = {
        artifact_ref: path,
        sha256: hash,
        result_id: output.result_id,
      };
      const onOpen = vi.fn();
      const onNavigate = vi.fn();
      render(
        <ResultCard
          output={{ ...output, title, representations: [reference] }}
          onOpen={onOpen}
          onNavigate={onNavigate}
        />,
      );
      expect(screen.getByRole("heading", { name: heading })).toHaveAttribute(
        "title",
        title,
      );
      fireEvent.click(screen.getByText("File details"));
      expect(screen.getByText(path, { selector: "code" })).toBeVisible();
      fireEvent.click(screen.getByRole("button", { name: "Open file" }));
      expect(onOpen).toHaveBeenCalledWith(reference);
      fireEvent.click(
        screen.getByRole("button", { name: "Open producing step" }),
      );
      expect(onNavigate).toHaveBeenCalledWith({
        kind: "block",
        block_id: output.step_id,
        result_id: output.result_id,
      });
    },
  );
  it("keeps equal filenames bound to their own result, path and hash", () => {
    const onOpen = vi.fn();
    const references = [
      {
        artifact_ref: "results/run-one/metrics.csv",
        sha256: hash,
        result_id: "one",
      },
      {
        artifact_ref: "results/run-two/metrics.csv",
        sha256: "b".repeat(64),
        result_id: "two",
      },
    ];
    const { container } = render(
      <>
        {references.map((reference) => (
          <ResultCard
            key={reference.result_id}
            output={{
              ...output,
              result_id: reference.result_id,
              title: reference.artifact_ref,
              representations: [reference],
            }}
            onOpen={onOpen}
          />
        ))}
      </>,
    );
    expect(
      screen.getAllByRole("heading", { name: "metrics.csv" }),
    ).toHaveLength(2);
    const cards = container.querySelectorAll(".wp-result");
    references.forEach((reference, index) => {
      expect(cards[index]).toHaveAttribute(
        "data-result-id",
        reference.result_id,
      );
      fireEvent.click(
        within(cards[index] as HTMLElement).getByRole("button", {
          name: "Open file",
        }),
      );
      expect(onOpen).toHaveBeenLastCalledWith(reference);
    });
  });
  it.each([
    ["failed", "completed", "Completed"],
    ["running", "cancelled", "Cancelled"],
    ["reconciliation_required", "completed", "Completed"],
  ] as const)(
    "does not promote an observed %s / %s outcome to process completion",
    (state, observedState, label) => {
      render(
        <ProgressPanel
          state={state}
          observations={[
            {
              ...observation,
              activity: undefined,
              state: observedState,
              observed_at: "2026-09-30T12:00:00Z",
            },
          ]}
          now={Date.parse("2026-09-30T12:00:30Z")}
        />,
      );
      expect(screen.getByText(`Observed state: ${label}`)).toBeInTheDocument();
      expect(screen.queryByText("Process completed")).not.toBeInTheDocument();
      expect(screen.queryByText("Process cancelled")).not.toBeInTheDocument();
    },
  );
  it("labels the process completion once and preserves the observation's activity and identity", () => {
    const { container } = render(
      <ProgressPanel
        state="completed"
        observations={[
          {
            ...observation,
            state: "completed",
            operation_id: "job-123",
          },
        ]}
        now={Date.parse("2026-09-30T12:00:30Z")}
      />,
    );
    expect(screen.getAllByText("Process completed")).toHaveLength(1);
    expect(screen.getByText("Observed state: Completed")).toBeInTheDocument();
    expect(screen.getByText("Reported by configured-tool")).toBeVisible();
    expect(screen.getByText("Measuring geometry")).toBeInTheDocument();
    expect(container.querySelector("details")).toHaveTextContent(
      "Provider: configured-tool",
    );
    expect(container.querySelector("details")).toHaveTextContent(
      "Operation: job-123",
    );
  });
  it("uses an explicit theme without private shell state", () => {
    const { container } = render(
      <ProcessUI theme="light">
        <p>Design task</p>
      </ProcessUI>,
    );
    expect(container.firstChild).toHaveAttribute("data-theme", "light");
    expect(container.firstChild).toHaveClass("wright-process-ui");
  });
  it("shows readable correction and keeps raw identifiers in details", () => {
    render(<ReasonNotice reason={reason} />);
    expect(screen.getByRole("alert")).toHaveTextContent(reason.message);
    expect(screen.getByRole("alert")).toHaveTextContent(reason.correction);
    expect(screen.getByText("Technical details")).toBeInTheDocument();
  });
  it("requires both backend permission and an explicit handler for actions", () => {
    const onAction = vi.fn();
    const { rerender } = render(
      <ActionButton
        action={{
          action_id: "start",
          operation: "start",
          title: "Start process",
          enabled: false,
          reasons: [reason],
        }}
        onAction={onAction}
      />,
    );
    fireEvent.click(screen.getByRole("button", { name: "Start process" }));
    expect(onAction).not.toHaveBeenCalled();
    rerender(
      <ActionButton
        action={{
          action_id: "start",
          operation: "start",
          title: "Start process",
          enabled: true,
        }}
      />,
    );
    expect(
      screen.getByRole("button", { name: "Start process" }),
    ).toBeDisabled();
    rerender(
      <ActionButton
        action={{
          action_id: "start",
          operation: "start",
          title: "Start process",
          enabled: true,
        }}
        onAction={onAction}
      />,
    );
    expect(onAction).not.toHaveBeenCalled();
    fireEvent.click(screen.getByRole("button", { name: "Start process" }));
    expect(onAction).toHaveBeenCalledTimes(1);
  });
  it("shows missing readiness and declared later dependency distinctions", () => {
    render(
      <ReadinessPanel
        readiness={{
          process: {
            workspace_id: "ws",
            source_path: "part.wflow",
            source_digest: hash,
          },
          assessment_id: "ready",
          assessed_at: observation.observed_at,
          state: "blocked",
          reasons: [reason],
          dependencies: [
            {
              binding_id: "mesh",
              classification: "upstream_produced",
              producer_step: "create",
            },
            {
              binding_id: "decision",
              classification: "declared_human_response",
              interaction_step: "review",
            },
          ],
        }}
      />,
    );
    expect(screen.getByText("Not ready to start")).toBeInTheDocument();
    expect(screen.getByText(/Produced by an earlier step/)).toBeInTheDocument();
    expect(
      screen.getByText(/Provided at a declared interaction/),
    ).toBeInTheDocument();
  });
  it("displays only observed progress and does not refresh stale measurements", () => {
    const { rerender } = render(
      <ProgressPanel
        state="waiting_external"
        observations={[observation]}
        now={Date.parse("2026-09-30T12:00:30Z")}
      />,
    );
    expect(screen.getByRole("progressbar")).toHaveAttribute("value", "25");
    expect(screen.getByText(/2 min/)).toBeInTheDocument();
    rerender(
      <ProgressPanel
        state="waiting_external"
        observations={[observation]}
        now={Date.parse("2026-09-30T12:02:00Z")}
      />,
    );
    expect(screen.queryByRole("progressbar")).not.toBeInTheDocument();
    expect(screen.getByText(/needs a fresh observation/i)).toBeInTheDocument();
    expect(screen.queryByText(/2 min remaining/)).not.toBeInTheDocument();
  });
  it("does not fabricate percentage or a confirmed stop for cancellation requests", () => {
    render(<ProgressPanel state="cancellation_requested" observations={[]} />);
    expect(screen.getByText("Cancellation requested")).toBeInTheDocument();
    expect(screen.queryByRole("progressbar")).not.toBeInTheDocument();
    expect(
      screen.getByText(/Waiting for the actual outcome/),
    ).toBeInTheDocument();
  });
  it("retains terminal historical progress without advertising a remaining time", () => {
    render(
      <ProgressPanel
        state="failed"
        observations={[{ ...observation, state: "failed" }]}
        now={Date.parse("2026-09-30T12:10:00Z")}
      />,
    );
    expect(screen.getByText("25% last reported")).toBeInTheDocument();
    expect(screen.queryByText(/2 min remaining/)).not.toBeInTheDocument();
  });
  it.each<Observation["state"]>([
    "completed",
    "failed",
    "cancelled",
    "waiting_human",
    "preparing",
    "ready",
    "reconciliation_required",
  ])(
    "does not ask for a progress estimate when the observation is %s",
    (state) => {
      render(
        <ProgressPanel
          state={state}
          observations={[
            {
              ...observation,
              state,
              progress_percent: undefined,
              estimated_remaining_seconds: undefined,
              limitations: ["Physical fit has not been tested."],
            },
          ]}
          now={Date.parse("2026-09-30T12:00:30Z")}
        />,
      );
      expect(
        screen.queryByText(/has not supplied a percentage/),
      ).not.toBeInTheDocument();
      expect(screen.queryByRole("progressbar")).not.toBeInTheDocument();
      expect(
        screen.getByText("Physical fit has not been tested."),
      ).toBeInTheDocument();
      expect(screen.getByText(observation.observed_at)).toBeInTheDocument();
    },
  );
  it.each<Observation["state"]>([
    "running",
    "waiting_external",
    "cancellation_requested",
  ])("explains an absent progress estimate while %s", (state) => {
    render(
      <ProgressPanel
        state={state}
        observations={[
          {
            ...observation,
            state,
            progress_percent: undefined,
            estimated_remaining_seconds: undefined,
          },
        ]}
        now={Date.parse("2026-09-30T12:00:30Z")}
      />,
    );
    expect(
      screen.getByText(/has not supplied a percentage/),
    ).toBeInTheDocument();
    expect(screen.queryByRole("progressbar")).not.toBeInTheDocument();
  });
  it("expires observations while the view is quiet, without changing the observed timestamp", () => {
    vi.useFakeTimers();
    try {
      vi.setSystemTime(new Date("2026-09-30T12:00:30Z"));
      render(
        <ProgressPanel state="waiting_external" observations={[observation]} />,
      );
      expect(screen.getByRole("progressbar")).toHaveAttribute("value", "25");
      act(() => vi.advanceTimersByTime(31_000));
      expect(screen.queryByRole("progressbar")).not.toBeInTheDocument();
      expect(screen.getByText(/needs a fresh observation/)).toBeInTheDocument();
      expect(screen.getByText(observation.observed_at)).toBeInTheDocument();
    } finally {
      cleanup();
      vi.useRealTimers();
    }
  });
  it("keeps failing exact assessments visible with navigation to their owner", () => {
    const onNavigate = vi.fn();
    render(<ResultCard output={output} onNavigate={onNavigate} />);
    expect(screen.getByText("Failed")).toBeInTheDocument();
    fireEvent.click(screen.getByRole("button", { name: "Open assessment" }));
    expect(onNavigate).toHaveBeenCalledWith({
      kind: "assessment",
      assessment_id: "check-one",
      result_id: output.result_id,
    });
    expect(screen.getByRole("button", { name: "Open file" })).toBeDisabled();
  });
  it("shows a readable filename while retaining exact evidence identity and open scope", () => {
    const onOpen = vi.fn();
    const reference = {
      artifact_ref: "process-proofs/case/outputs/run-id/geometry-basis.json",
      sha256: hash,
    };
    render(<EvidenceReference reference={reference} onOpen={onOpen} />);
    expect(screen.getByText("geometry-basis.json")).toBeVisible();
    expect(
      screen.getByText(reference.artifact_ref).closest("details"),
    ).not.toHaveAttribute("open");
    expect(screen.getByText(hash).closest("details")).not.toHaveAttribute(
      "open",
    );
    fireEvent.click(screen.getByRole("button", { name: "Open file" }));
    expect(onOpen).toHaveBeenCalledExactlyOnceWith(reference);
  });
  it("shows declared review evidence without enabling an invented approval", () => {
    const onAction = vi.fn();
    render(
      <CheckpointCard
        interaction={{
          checkpoint_id: "cp",
          step_id: "review",
          subject_digest: hash,
          kind: "review",
          instructions: "Check the thermal limit.",
          decisions: ["approve", "reject"],
          evidence: output.representations,
        }}
        actions={[
          {
            action_id: "other",
            checkpoint_id: "elsewhere",
            subject_digest: hash,
            operation: "review",
            title: "Approve",
            enabled: true,
          },
        ]}
        onAction={onAction}
      />,
    );
    expect(screen.getByText("Check the thermal limit.")).toBeInTheDocument();
    expect(
      screen.queryByRole("button", { name: "Approve" }),
    ).not.toBeInTheDocument();
    expect(onAction).not.toHaveBeenCalled();
  });
  it("keeps unavailable checkpoint actions disabled with their exact reason on demand", () => {
    const onAction = vi.fn();
    render(
      <ActionButton
        compactReasons
        action={{
          action_id: "continue",
          operation: "action",
          title: "Continue process",
          enabled: false,
          subject_digest: hash,
          reasons: [
            {
              code: "ACTION_NOT_PERMITTED",
              message: "Review is still pending.",
              correction: "Complete the declared review.",
            },
          ],
        }}
        onAction={onAction}
      />,
    );
    const button = screen.getByRole("button", { name: "Continue process" });
    expect(button).toBeDisabled();
    expect(
      screen
        .getByText("Review is still pending.")
        .closest("details.wp-action-reasons"),
    ).not.toHaveAttribute("open");
    fireEvent.click(button);
    expect(onAction).not.toHaveBeenCalled();
  });
  it("shows a retained test review without inventing dispatch authority", () => {
    const onAction = vi.fn();
    render(
      <CheckpointCard
        interaction={{
          checkpoint_id: "cp",
          step_id: "review",
          subject_digest: hash,
          kind: "action",
          instructions: "Inspect the exact package",
          decisions: ["approved", "changes_requested"],
          state: "waiting",
          decision: {
            decision: "approved",
            actor: "integration_test:private",
            request_id: "review-one",
            reason: "Synthetic test review",
            integration_test: true,
          },
        }}
        actions={[]}
        onAction={onAction}
      />,
    );
    expect(
      screen.getByText("Test review recorded: Approved"),
    ).toBeInTheDocument();
    expect(screen.getByText("Synthetic test review")).toBeInTheDocument();
    expect(
      screen.getByText("Decision actor: integration_test:private"),
    ).toBeInTheDocument();
    expect(screen.getByText("Review request: review-one")).toBeInTheDocument();
    expect(
      screen.queryByRole("button", { name: /approve|continue|submit/i }),
    ).not.toBeInTheDocument();
    expect(onAction).not.toHaveBeenCalled();
  });
});

describe("schema and provider-backed input controls", () => {
  it("shows the declared quantity error beside its field and enables only a corrected response", () => {
    const submit = vi.fn();
    function Form() {
      const [value, setValue] =
        useState<import("@wright/process-client").JsonValue>();
      return (
        <CheckpointCard
          interaction={{
            checkpoint_id: "cp",
            step_id: "choice",
            subject_digest: hash,
            kind: "input",
            instructions: "Choose a material and quantity.",
            state: "waiting",
            response_schema: {
              type: "object",
              properties: {
                material: { type: "string", enum: ["steel", "aluminum"] },
                quantity: {
                  type: "integer",
                  title: "Number of plates",
                  minimum: 1,
                  maximum: 5,
                },
              },
              required: ["material", "quantity"],
              additionalProperties: false,
            },
          }}
          actions={[
            {
              action_id: "answer",
              checkpoint_id: "cp",
              subject_digest: hash,
              operation: "respond",
              title: "Submit response",
              enabled: true,
            },
          ]}
          response={{ value, onChange: setValue, onSubmit: submit }}
        />
      );
    }
    render(<Form />);
    const button = screen.getByRole("button", { name: "Submit response" });
    expect(button).toBeDisabled();
    fireEvent.change(screen.getByLabelText("material (required)"), {
      target: { value: "0" },
    });
    expect(button).toBeDisabled();
    const quantity = screen.getByLabelText("Number of plates (required)");
    fireEvent.change(quantity, { target: { value: "0" } });
    expect(quantity).toHaveAttribute("aria-invalid", "true");
    expect(quantity).toHaveAccessibleDescription(
      "Enter a value of at least 1.",
    );
    expect(button).toBeDisabled();
    fireEvent.click(button);
    expect(submit).not.toHaveBeenCalled();
    fireEvent.change(quantity, { target: { value: "2.5" } });
    expect(quantity).toHaveAccessibleDescription("Enter a whole number.");
    expect(button).toBeDisabled();
    fireEvent.change(quantity, { target: { value: "6" } });
    expect(quantity).toHaveAccessibleDescription("Enter a value of at most 5.");
    fireEvent.change(quantity, { target: { value: "2" } });
    expect(quantity).toHaveAttribute("aria-invalid", "false");
    expect(button).toBeEnabled();
    fireEvent.click(button);
    expect(submit).toHaveBeenCalledExactlyOnceWith(
      expect.objectContaining({ subject_digest: hash }),
      { material: "steel", quantity: 2 },
    );
  });
  it("keeps the backend's disabled action authoritative for a valid local answer", () => {
    render(
      <CheckpointCard
        interaction={{
          checkpoint_id: "cp",
          step_id: "choice",
          subject_digest: hash,
          kind: "input",
          instructions: "Choose quantity",
          response_schema: { type: "integer", minimum: 1 },
        }}
        actions={[
          {
            action_id: "answer",
            checkpoint_id: "cp",
            subject_digest: hash,
            operation: "respond",
            title: "Submit response",
            enabled: false,
            reasons: [reason],
          },
        ]}
        response={{ value: 2, onChange: vi.fn(), onSubmit: vi.fn() }}
      />,
    );
    expect(
      screen.getByRole("button", { name: "Submit response" }),
    ).toBeDisabled();
    expect(screen.getByText(reason.message)).toBeVisible();
  });
  it("checks nested local references and text bounds without counting UTF-16 units as characters", () => {
    const schema = {
      $defs: { name: { type: "string", minLength: 2 } },
      type: "object",
      properties: { name: { $ref: "#/$defs/name" } },
      required: ["name"],
    };
    const { rerender } = render(
      <SchemaField
        title="Answer"
        schema={schema}
        value={{ name: "😀" }}
        onChange={vi.fn()}
      />,
    );
    expect(
      screen.getByLabelText("name (required)"),
    ).toHaveAccessibleDescription("Enter at least 2 characters.");
    rerender(
      <SchemaField
        title="Answer"
        schema={schema}
        value={{ name: "😀a" }}
        onChange={vi.fn()}
      />,
    );
    expect(screen.getByLabelText("name (required)")).toHaveAttribute(
      "aria-invalid",
      "false",
    );
  });
  it("edits a prompt as a typed binding without executing the process", () => {
    const onChange = vi.fn();
    render(<InputEditor definition={input} onChange={onChange} />);
    fireEvent.change(screen.getByLabelText(/What should Wright make/), {
      target: { value: "A focus wheel" },
    });
    expect(onChange).toHaveBeenCalledWith({
      kind: "value",
      input_id: "prompt",
      value: "A focus wheel",
      provenance: "supplied",
    });
  });
  it("preserves explicit false and clears numeric values without inventing defaults", () => {
    const onChange = vi.fn();
    const { rerender } = render(
      <SchemaField
        title="Calibrate"
        schema={{ type: "boolean" }}
        value={false}
        onChange={onChange}
      />,
    );
    expect(screen.getByLabelText("Calibrate")).not.toBeChecked();
    fireEvent.click(screen.getByLabelText("Calibrate"));
    expect(onChange).toHaveBeenLastCalledWith(true);
    rerender(
      <SchemaField
        title="Width"
        schema={{ type: "number", minimum: 1 }}
        value={10}
        onChange={onChange}
      />,
    );
    fireEvent.change(screen.getByLabelText("Width"), { target: { value: "" } });
    expect(onChange).toHaveBeenLastCalledWith(undefined);
  });
  it("renders configured option identities and their actual capability provenance", () => {
    const onChange = vi.fn();
    render(
      <InputEditor
        definition={{
          ...input,
          title: "Material",
          binding_kind: "option",
          option_source: { binding_id: "materials", schema_digest: hash },
          options_observed_at: observation.observed_at,
          available_options: [
            {
              option_id: "slot-b",
              title: "Loaded PLA · red",
              value: { material: "PLA", location: "B" },
            },
          ],
        }}
        onChange={onChange}
      />,
    );
    fireEvent.change(screen.getByLabelText(/Material/), {
      target: { value: "slot-b" },
    });
    expect(onChange).toHaveBeenCalledWith(
      expect.objectContaining({
        kind: "option",
        option_id: "slot-b",
        capability: { binding_id: "materials", schema_digest: hash },
        observed_at: observation.observed_at,
        value: { material: "PLA", location: "B" },
      }),
    );
  });
  it("does not guess missing provider option lists or unsupported schemas", () => {
    render(
      <>
        <InputEditor
          definition={{ ...input, title: "Material", binding_kind: "option" }}
          onChange={vi.fn()}
        />
        <SchemaField
          title="Unusual data"
          schema={{ type: "object", patternProperties: {} }}
          onChange={vi.fn()}
        />
      </>,
    );
    expect(
      screen.getByText(/configured choices are unavailable/i),
    ).toBeInTheDocument();
    expect(screen.getByText(/unsupported schema/i)).toBeInTheDocument();
  });
  it("renders a bounded structured field with declared units", () => {
    function Form() {
      const [binding, setBinding] = useState<InputBinding>();
      return (
        <InputEditor
          definition={{
            ...input,
            title: "Dimensions",
            unit: "mm",
            value_schema: {
              type: "object",
              properties: {
                width: { type: "number" },
                quantity: { type: "integer" },
              },
              required: ["width"],
            },
          }}
          binding={binding}
          onChange={(value) => setBinding(value ?? undefined)}
        />
      );
    }
    render(<Form />);
    expect(screen.getByText(/mm/)).toBeInTheDocument();
    fireEvent.change(screen.getByLabelText(/width/), {
      target: { value: "12.5" },
    });
    expect(screen.getByLabelText(/width/)).toHaveValue(12.5);
  });
  it("shows a selected image while the host stores an exact file reference", async () => {
    vi.spyOn(URL, "createObjectURL").mockReturnValue("blob:local-image");
    vi.spyOn(URL, "revokeObjectURL").mockImplementation(() => undefined);
    const onChange = vi.fn();
    const onUpload = vi.fn(async () => ({
      artifact_ref: "inputs/pumpkin.png",
      sha256: hash,
      media_type: "image/png",
    }));
    render(
      <InputEditor
        definition={{
          ...input,
          title: "Reference image",
          binding_kind: "file",
        }}
        onChange={onChange}
        onUpload={onUpload}
      />,
    );
    const file = new File(["png-data"], "pumpkin.png", { type: "image/png" });
    fireEvent.change(screen.getByLabelText(/Reference image/), {
      target: { files: [file] },
    });
    expect(
      await screen.findByAltText("Selected reference: pumpkin.png"),
    ).toBeInTheDocument();
    await waitFor(() =>
      expect(onChange).toHaveBeenCalledWith({
        kind: "file",
        input_id: "prompt",
        reference: {
          artifact_ref: "inputs/pumpkin.png",
          sha256: hash,
          media_type: "image/png",
        },
        provenance: "supplied",
      }),
    );
  });
  it("keeps an uncertain upload unbound without retrying or exposing a bitmap warning", async () => {
    const onChange = vi.fn();
    const onUpload = vi.fn().mockRejectedValue(
      new ProcessClientError({
        code: "OUTCOME_UNKNOWN",
        message: "The upload acknowledgement was lost.",
        correction: "Inspect the saved input before another upload.",
      }),
    );
    render(
      <InputEditor
        definition={{ ...input, binding_kind: "file" }}
        onChange={onChange}
        onUpload={onUpload}
      />,
    );
    fireEvent.change(screen.getByLabelText(/What should Wright make/), {
      target: {
        files: [
          new File(["requirements"], "requirements.txt", {
            type: "text/plain",
          }),
        ],
      },
    });
    expect(await screen.findByRole("alert")).toHaveTextContent(
      "The upload acknowledgement was lost. Inspect the saved input before another upload.",
    );
    expect(onUpload).toHaveBeenCalledTimes(1);
    expect(onChange.mock.calls.every(([value]) => value === null)).toBe(true);
    expect(screen.queryByText(/bitmap preview/i)).not.toBeInTheDocument();
    expect(screen.queryByText(/File attached/)).not.toBeInTheDocument();
  });
  it("shows a prepared file reference with an omitted default discriminator", () => {
    const onUpload = vi.fn();
    render(
      <InputEditor
        definition={{
          ...input,
          binding_kind: "file",
          current_value: {
            input_id: input.input_id,
            reference: { artifact_ref: "inputs/prepared.png", sha256: hash },
            provenance: "explicit_default",
          },
        }}
        onChange={vi.fn()}
        onUpload={onUpload}
      />,
    );
    expect(screen.getByText("File attached")).toBeVisible();
    expect(screen.getByText("inputs/prepared.png")).not.toBeVisible();
    fireEvent.click(screen.getByText("File details"));
    expect(screen.getByText("inputs/prepared.png")).toBeVisible();
    expect(onUpload).not.toHaveBeenCalled();
  });
  it("preserves an explicit prepared zero with an omitted default discriminator", () => {
    render(
      <InputEditor
        definition={{
          ...input,
          value_schema: { type: "number" },
          current_value: {
            input_id: input.input_id,
            value: 0,
            provenance: "explicit_default",
          },
        }}
        onChange={vi.fn()}
      />,
    );
    expect(screen.getByRole("spinbutton")).toHaveValue(0);
  });
  it("shows an explicit default file before preparation without uploading it", () => {
    const onUpload = vi.fn();
    const definition = {
      ...input,
      binding_kind: "file" as const,
      current_value: null,
      default: {
        input_id: input.input_id,
        reference: { artifact_ref: "inputs/default.png", sha256: hash },
        provenance: "explicit_default" as const,
      },
    };
    const view = render(
      <InputEditor
        definition={definition}
        onChange={vi.fn()}
        onUpload={onUpload}
      />,
    );
    expect(screen.getByText("File attached")).toBeVisible();
    expect(screen.getByText("inputs/default.png")).not.toBeVisible();
    fireEvent.click(screen.getByText("File details"));
    expect(screen.getByText("inputs/default.png")).toBeVisible();
    expect(onUpload).not.toHaveBeenCalled();
    view.rerender(
      <InputEditor
        definition={definition}
        binding={null}
        onChange={vi.fn()}
        onUpload={onUpload}
      />,
    );
    expect(screen.queryByText("inputs/default.png")).not.toBeInTheDocument();
  });
});

describe("bounded neutral toolpath data", () => {
  const document = {
    format: "wright.gcode.toolpaths.v1",
    package_sha256: hash,
    layers: [{ index: 1, z: 0.2, model: [[0, 0, 10, 0]], support: [] }],
  };
  it("accepts actual finite layer paths only for their matching package", () => {
    expect(parseToolpaths(document, hash).layers).toHaveLength(1);
    expect(() => parseToolpaths(document, "b".repeat(64))).toThrow(/package/i);
  });
  it("keeps legacy absent classification evidence unknown", () => {
    const value: ToolpathDocument = parseToolpaths(document, hash);
    expect(value.classificationKnown).toBe(false);
  });
  it("retains finite passive reader provenance without promoting acceptance", () => {
    const provenance = {
      reader: "wright.passive-representations/1",
      source_sha256: hash,
      archive_entry: null,
      method: "Actual planar commands",
      units: "mm",
      segments: 1,
      extruding_arcs: 0,
      arc_maximum_chord_error_mm: 0.02,
      unlayered_extrusion_commands_excluded: 2,
      unclassified_features: ["custom"],
      engineering_acceptance: false,
    };
    const parsed = parseToolpaths({ ...document, provenance }, hash);
    expect(parsed.provenance?.sourceSha256).toBe(hash);
    expect(parsed.provenance?.excludedUnlayeredCommands).toBe(2);
    for (const change of [
      { engineering_acceptance: true },
      { segments: 2 },
      { source_sha256: "b".repeat(64) },
      { archive_entry: "../other.gcode" },
      { arc_maximum_chord_error_mm: Infinity },
    ]) {
      expect(() =>
        parseToolpaths(
          { ...document, provenance: { ...provenance, ...change } },
          hash,
        ),
      ).toThrow();
    }
  });
  it.each([NaN, Infinity, "10", undefined])(
    "rejects invalid path coordinate %s",
    (coordinate) => {
      expect(() =>
        parseToolpaths(
          {
            ...document,
            layers: [{ ...document.layers[0], model: [[0, 0, coordinate, 0]] }],
          },
          hash,
        ),
      ).toThrow();
    },
  );
  it("rejects malformed, empty, duplicate and excessive layer documents", () => {
    for (const layers of [
      [],
      [{ ...document.layers[0], z: null }],
      [document.layers[0], document.layers[0]],
      Array.from({ length: 10001 }, (_, i) => ({
        ...document.layers[0],
        index: i,
      })),
    ]) {
      expect(() => parseToolpaths({ ...document, layers }, hash)).toThrow();
    }
  });
});

describe("bounded representation views", () => {
  const recordedPaths = {
    format: "wright.gcode.toolpaths.v1",
    package_sha256: hash,
    classification_source: "gcode_feature_comments",
    layers: [{ index: 0, z: 0.2, model: [[0, 0, 10, 0]], support: [] }],
    provenance: {
      reader: "wright.passive-representations/1",
      source_sha256: "b".repeat(64),
      archive_entry: "Metadata/plate_1.gcode",
      method: "Recorded planar commands",
      units: "mm",
      segments: 1,
      extruding_arcs: 0,
      arc_maximum_chord_error_mm: 0.02,
      unlayered_extrusion_commands_excluded: 0,
      unclassified_features: [],
      engineering_acceptance: false,
      selected_section: {
        start_marker: "; BODY START",
        end_marker: "; BODY END",
        first_line: 11,
        last_line: 20,
        excluded_prefix_lines: 10,
        excluded_suffix_lines: 5,
        selected_text_sha256: "c".repeat(64),
      },
    },
  };
  function jsonBlob(value: unknown): Blob {
    const text = JSON.stringify(value);
    const blob = new Blob([text], { type: "application/json" });
    Object.defineProperty(blob, "text", { value: async () => text });
    return blob;
  }
  it("keeps the recorded evidence identity distinct from its reported package", () => {
    const parsed = parseRecordedToolpaths(recordedPaths, "d".repeat(64));
    expect(parsed.recordedEvidenceSha256).toBe("d".repeat(64));
    expect(parsed.packageSha256).toBe(hash);
    expect(parsed.provenance?.selectedSection?.excludedPrefixLines).toBe(10);
    expect(() => parseRecordedToolpaths(recordedPaths, "unknown")).toThrow();
    expect(() =>
      parseRecordedToolpaths({ ...recordedPaths, provenance: null }, hash),
    ).toThrow();
    expect(() =>
      parseRecordedToolpaths(
        { ...recordedPaths, package_sha256: "unknown" },
        hash,
      ),
    ).toThrow();
  });
  it.each([
    { first_line: 0 },
    { first_line: 10 },
    { last_line: 9 },
    { excluded_prefix_lines: -1 },
    { excluded_suffix_lines: 2_000_000 },
    { start_marker: "BODY START" },
    { end_marker: "; BODY START" },
    { start_marker: "; BODY\nSTART" },
    { selected_text_sha256: "unknown" },
  ])("rejects inconsistent nominal scope evidence (%#)", (change) => {
    expect(() =>
      parseRecordedToolpaths(
        {
          ...recordedPaths,
          provenance: {
            ...recordedPaths.provenance,
            selected_section: {
              ...recordedPaths.provenance.selected_section,
              ...change,
            },
          },
        },
        hash,
      ),
    ).toThrow();
  });
  it("shows recorded neutral paths and their excluded machine scope without requesting another read", async () => {
    const readToolpaths = vi.fn();
    render(
      <RepresentationViewer
        blob={jsonBlob(recordedPaths)}
        title="recorded-paths.json"
        sourceSha256={"d".repeat(64)}
        readToolpaths={readToolpaths}
      />,
    );
    await screen.findByRole("slider");
    expect(
      screen.getByText(/Package correspondence and engineering/),
    ).toBeVisible();
    expect(
      screen.getByText(
        /Machine setup and shutdown are excluded and unverified/,
      ),
    ).toBeVisible();
    expect(
      screen.getByText(/Recorded evidence SHA-256: d{64}/),
    ).toBeInTheDocument();
    expect(
      screen.getByText(/Reported package SHA-256: a{64}/),
    ).toBeInTheDocument();
    expect(readToolpaths).not.toHaveBeenCalled();
  });
  it("supports bounded recorded layer data beyond the ordinary text preview limit", async () => {
    const count = 120_000;
    const value = {
      ...recordedPaths,
      layers: [
        {
          ...recordedPaths.layers[0],
          model: Array.from({ length: count }, () => [0, 0, 10, 0]),
        },
      ],
      provenance: { ...recordedPaths.provenance, segments: count },
    };
    const blob = jsonBlob(value);
    expect(blob.size).toBeGreaterThan(1024 * 1024);
    render(
      <RepresentationViewer
        blob={blob}
        title="large-recorded-paths.json"
        sourceSha256={hash}
      />,
    );
    await screen.findByRole("slider");
  });
  it("retains the ordinary JSON text bound and refuses incomplete recorded provenance", async () => {
    const view = render(
      <RepresentationViewer
        blob={jsonBlob({ value: "x".repeat(2 * 1024 * 1024) })}
        title="large-report.json"
        sourceSha256={hash}
      />,
    );
    await screen.findByText(/exceeds the supported text preview size/);
    expect(screen.queryByRole("slider")).not.toBeInTheDocument();
    view.rerender(
      <RepresentationViewer
        blob={jsonBlob({ ...recordedPaths, provenance: null })}
        title="invalid-paths.json"
        sourceSha256={hash}
      />,
    );
    await screen.findByText(/could not be read/);
    expect(screen.queryByRole("slider")).not.toBeInTheDocument();
  });
  it("requires the exact recorded file identity and reconciles a changed representation", async () => {
    const blob = jsonBlob(recordedPaths);
    const view = render(
      <RepresentationViewer blob={blob} title="recorded-paths.json" />,
    );
    await screen.findByText(/could not be read/);
    view.rerender(
      <RepresentationViewer
        blob={blob}
        title="recorded-paths.json"
        sourceSha256={hash}
      />,
    );
    await screen.findByRole("slider");
    view.rerender(
      <RepresentationViewer
        blob={jsonBlob({ ...recordedPaths, layers: [] })}
        title="changed-paths.json"
        sourceSha256={hash}
      />,
    );
    await screen.findByText(/could not be read/);
    expect(screen.queryByRole("slider")).not.toBeInTheDocument();
  });
  it("reveals all true layers and the exact source evidence from a passive read", async () => {
    const raw = new Blob(["exact package"], { type: "model/3mf" });
    const data = {
      format: "wright.gcode.toolpaths.v1",
      package_sha256: hash,
      classification_source: "gcode_feature_comments",
      layers: Array.from({ length: 30 }, (_, i) => ({
        index: i,
        z: (i + 1) * 0.2,
        model: [[0, 0, 10, 0]],
        support: [],
        unclassified: [],
      })),
      provenance: {
        reader: "wright.passive-representations/1",
        source_sha256: "b".repeat(64),
        archive_entry: "Metadata/plate_1.gcode",
        method: "Recorded planar commands",
        units: "mm",
        segments: 30,
        extruding_arcs: 0,
        arc_maximum_chord_error_mm: 0.02,
        unlayered_extrusion_commands_excluded: 3,
        unclassified_features: ["custom"],
        engineering_acceptance: false,
      },
    };
    const passive = new Blob([JSON.stringify(data)], {
      type: "application/vnd.wright.toolpaths+json",
    });
    Object.defineProperty(passive, "text", {
      value: async () => JSON.stringify(data),
    });
    const read = vi.fn(async () => passive);
    // Finish the asynchronous reader mount and its effects before moving the slider.
    await act(async () => {
      render(
        <RecordedToolpathPreview
          blob={raw}
          sourceSha256={hash}
          readToolpaths={read}
        />,
      );
    });
    const slider = await screen.findByRole("slider");
    expect(slider).toHaveAttribute("max", "30");
    fireEvent.change(slider, { target: { value: "2" } });
    expect(
      screen.getByText(/Layers 1–2 of 30 · Z 0.40 mm/),
    ).toBeInTheDocument();
    expect(
      screen.getByText(/Package entry: Metadata\/plate_1.gcode/),
    ).toBeInTheDocument();
    expect(
      screen.getByText(/3 extrusion commands outside recorded layers/),
    ).toBeInTheDocument();
    expect(read).toHaveBeenCalledTimes(1);
  });
  it("keeps numeric view axes as explicit choices over the exact table", () => {
    render(
      <CsvNumericInspector
        columns={["x_m", "y_m", "z_m", "temperature_c"]}
        rows={[
          ["0", "0", "0", "20"],
          ["0.05", "0.03", "0.002", "25.5"],
        ]}
      />,
    );
    expect(screen.getByRole("table")).toBeInTheDocument();
    expect(screen.queryByRole("img")).not.toBeInTheDocument();
    fireEvent.change(screen.getByLabelText("Horizontal column"), {
      target: { value: "x_m" },
    });
    fireEvent.change(screen.getByLabelText("Vertical column"), {
      target: { value: "y_m" },
    });
    fireEvent.change(screen.getByLabelText("Value column"), {
      target: { value: "temperature_c" },
    });
    expect(screen.getByRole("img")).toHaveAccessibleName(
      /samples from 20 to 25.5/,
    );
    expect(
      screen.getByText(/Other coordinates remain in the exact table/),
    ).toBeInTheDocument();
  });
  it("keeps numeric plotting controls above a short exact-data page and plots all samples", () => {
    const rows = Array.from({ length: 23 }, (_, index) => [
      String(index),
      "0",
      "0",
      String(25 + index),
    ]);
    render(
      <CsvNumericInspector
        columns={["x_m", "y_m", "z_m", "temperature_c"]}
        rows={rows}
      />,
    );
    const table = screen.getByRole("table");
    const controls = screen.getByText("View numerical samples");
    expect(
      controls.compareDocumentPosition(table) &
        Node.DOCUMENT_POSITION_FOLLOWING,
    ).toBeTruthy();
    expect(table.querySelectorAll("tbody tr")).toHaveLength(10);
    expect(table.querySelector("tbody tr td")?.textContent).toBe("0");
    fireEvent.click(screen.getByRole("button", { name: "Next rows" }));
    expect(table.querySelector("tbody tr td")?.textContent).toBe("10");
    fireEvent.change(screen.getByLabelText("Horizontal column"), {
      target: { value: "x_m" },
    });
    fireEvent.change(screen.getByLabelText("Vertical column"), {
      target: { value: "y_m" },
    });
    fireEvent.change(screen.getByLabelText("Value column"), {
      target: { value: "temperature_c" },
    });
    expect(screen.getByRole("img").querySelectorAll("circle")).toHaveLength(23);
    expect(rows[22]).toEqual(["22", "0", "0", "47"]);
  });
  it("refuses missing exact package identity and preserves download fallback", async () => {
    const read = vi.fn();
    render(
      <RecordedToolpathPreview
        blob={new Blob(["package"], { type: "model/3mf" })}
        readToolpaths={read}
      />,
    );
    expect(
      await screen.findByText(/complete toolpath preview is unavailable/),
    ).toBeInTheDocument();
    expect(read).not.toHaveBeenCalled();
  });
  it("aborts a passive read on close and ignores late results", async () => {
    let signal: AbortSignal | undefined;
    let complete!: (value: Blob) => void;
    const read = vi.fn((input: AbortSignal) => {
      signal = input;
      return new Promise<Blob>((resolve) => {
        complete = resolve;
      });
    });
    const { unmount } = render(
      <RecordedToolpathPreview
        blob={new Blob(["package"], { type: "model/3mf" })}
        sourceSha256={hash}
        readToolpaths={read}
      />,
    );
    await waitFor(() => expect(read).toHaveBeenCalledTimes(1));
    unmount();
    expect(signal?.aborted).toBe(true);
    await act(async () =>
      complete(
        new Blob(["invalid"], {
          type: "application/vnd.wright.toolpaths+json",
        }),
      ),
    );
    expect(screen.queryByRole("slider")).not.toBeInTheDocument();
  });
  it("does not restart a pending passive read because a host callback identity changes", async () => {
    const blob = new Blob(["package"], { type: "model/3mf" });
    const first = vi.fn(() => new Promise<Blob>(() => {}));
    const next = vi.fn(() => new Promise<Blob>(() => {}));
    const { rerender } = render(
      <RecordedToolpathPreview
        blob={blob}
        sourceSha256={hash}
        readToolpaths={first}
      />,
    );
    await waitFor(() => expect(first).toHaveBeenCalledTimes(1));
    rerender(
      <RecordedToolpathPreview
        blob={blob}
        sourceSha256={hash}
        readToolpaths={next}
      />,
    );
    expect(next).not.toHaveBeenCalled();
  });
  it("presents actionable findings without treating absent findings as approval", () => {
    const { rerender } = render(<FindingsPanel findings={[reason]} />);
    expect(screen.getByText(reason.correction)).toBeInTheDocument();
    rerender(<FindingsPanel findings={[]} />);
    expect(screen.getByText(/this is not an approval/)).toBeInTheDocument();
  });
  it("shows supplied scalar samples with actual ranges and explicit units", () => {
    render(
      <ScalarFieldPlot
        title="Thermal field"
        xLabel="x · mm"
        yLabel="y · mm"
        valueLabel="Temperature · K"
        points={[
          { x: 0, y: 0, value: 300 },
          { x: 1, y: 1, value: 320 },
        ]}
      />,
    );
    expect(screen.getByRole("img")).toHaveAccessibleName(
      /samples from 300 to 320/,
    );
    expect(
      screen.getByText(/without interpolated geometry/),
    ).toBeInTheDocument();
    expect(screen.getByLabelText("x · mm axis").textContent).toContain("0.25");
    expect(screen.getByLabelText("y · mm axis").textContent).toContain("0.75");
    const scale = screen.getByLabelText("Temperature · K color scale");
    expect(scale.textContent).toContain("300");
    expect(scale.textContent).toContain("310");
    expect(scale.textContent).toContain("320");
    expect(
      screen.getByText(/Colors show the recorded value range/),
    ).toBeVisible();
    expect(screen.getByRole("img").querySelectorAll("circle")).toHaveLength(2);
  });
  it("shows one value for constant axes and a constant field without inventing a range", () => {
    render(
      <ScalarFieldPlot
        title="Uniform field"
        xLabel="x"
        yLabel="y"
        valueLabel="value"
        points={[{ x: 2, y: -3, value: 17 }]}
      />,
    );
    expect(
      screen.getByLabelText("x axis").querySelectorAll("text"),
    ).toHaveLength(1);
    expect(
      screen.getByLabelText("y axis").querySelectorAll("text"),
    ).toHaveLength(1);
    expect(screen.getByLabelText("value color scale").textContent).toBe("17");
    expect(screen.getByRole("img").querySelector("linearGradient")).toBeNull();
    expect(screen.getByRole("img").innerHTML).not.toMatch(/NaN|Infinity/);
  });
  it("keeps separate field legends independent and exact values available", () => {
    const points = [
      { x: 0, y: 0, value: 25 },
      { x: 0.1, y: 0.06, value: 41.6666666665829 },
    ];
    render(
      <>
        <ScalarFieldPlot
          title="First"
          xLabel="x"
          yLabel="y"
          valueLabel="T"
          points={points}
        />
        <ScalarFieldPlot
          title="Second"
          xLabel="x"
          yLabel="y"
          valueLabel="T"
          points={points}
        />
      </>,
    );
    const plots = screen.getAllByRole("img");
    const ids = plots.map((plot) => plot.querySelector("linearGradient")?.id);
    expect(ids.every(Boolean)).toBe(true);
    expect(new Set(ids).size).toBe(2);
    expect(plots[0].querySelectorAll("circle title")[1].textContent).toContain(
      "41.6666666665829",
    );
    expect(plots[0].textContent).toContain("41.6667");
  });
  it("keeps closely spaced large coordinate ticks distinguishable", () => {
    render(
      <NumericPlot
        title="Close positions"
        xLabel="position"
        yLabel="value"
        points={[
          [1e12, 0],
          [1e12 + 1, 1],
        ]}
      />,
    );
    const labels = [
      ...screen.getByLabelText("position axis").querySelectorAll("text"),
    ].map((node) => node.textContent);
    expect(labels).toHaveLength(5);
    expect(new Set(labels).size).toBe(5);
    expect(labels).toContain("1000000000001");
  });
  it("parses quoted CSV fields and Windows line endings as actual table data", () => {
    expect(
      parseCsv('\ufeffPosition,Temperature\r\n"1,2","310"\r\n"3""4",320\r\n'),
    ).toEqual({
      columns: ["Position", "Temperature"],
      rows: [
        ["1,2", "310"],
        ['3"4', "320"],
      ],
    });
    expect(() => parseCsv("x,y\n1\n")).toThrow();
    expect(() => parseCsv('x\n"unfinished')).toThrow();
  });
  it("paginates data instead of silently claiming that the first rows are the whole result", () => {
    render(
      <DataTable
        columns={["Temperature · K"]}
        rows={[[300], [310], [320]]}
        pageSize={2}
      />,
    );
    expect(screen.getByText("Page 1 of 2")).toBeInTheDocument();
    fireEvent.click(screen.getByRole("button", { name: "Next rows" }));
    expect(screen.getByText("320")).toBeInTheDocument();
    expect(screen.queryByText("300")).not.toBeInTheDocument();
  });
  it("plots finite supplied data and labels the range and units", () => {
    const { rerender } = render(
      <NumericPlot
        title="Temperature profile"
        xLabel="Position · mm"
        yLabel="Temperature · K"
        points={[
          [0, 300],
          [10, 320],
        ]}
      />,
    );
    expect(screen.getByRole("img")).toHaveAccessibleName(
      /Position · mm from 0 to 10/,
    );
    rerender(
      <NumericPlot
        title="Bad plot"
        xLabel="x"
        yLabel="y"
        points={[[NaN, 300]]}
      />,
    );
    expect(screen.queryByRole("img")).not.toBeInTheDocument();
  });
  it("does not render HTML or SVG representations as executable content", async () => {
    const blob = new Blob(["<script>window.bad=true</script>"], {
      type: "text/html",
    });
    render(<RepresentationViewer blob={blob} title="Unsupported document" />);
    expect(await screen.findByText(/no supported preview/)).toBeInTheDocument();
    expect(document.querySelector("script, iframe, object, embed")).toBeNull();
  });
  it("announces preview readiness only after asynchronous content commits, once per blob", async () => {
    const blob = new Blob(["loaded preview"], { type: "text/plain" });
    let finish: ((value: string) => void) | undefined;
    vi.spyOn(blob, "text").mockImplementation(
      () =>
        new Promise<string>((resolve) => {
          finish = resolve;
        }),
    );
    const ready = vi.fn(() =>
      expect(screen.getByText("loaded preview")).toBeInTheDocument(),
    );
    const view = render(
      <RepresentationViewer
        blob={blob}
        title="Exact preview"
        onReady={ready}
      />,
    );
    await screen.findByText("Opening representation…");
    expect(ready).not.toHaveBeenCalled();
    await act(async () => {
      finish?.("loaded preview");
    });
    expect(ready).toHaveBeenCalledTimes(1);
    view.rerender(
      <RepresentationViewer
        blob={blob}
        title="Exact preview"
        onReady={ready}
      />,
    );
    expect(ready).toHaveBeenCalledTimes(1);
  });
  it("renders Markdown engineering headings and tables with the exact source and download", async () => {
    const text =
      "# Inspection plan\r\n\r\n| Characteristic | Result |\r\n| --- | --- |\r\n| Diameter | 38 mm |\r\n\r\n- [ ] Engineer review\r\n";
    const blob = new Blob([text], { type: "text/markdown; charset=utf-8" });
    const create = vi
      .spyOn(URL, "createObjectURL")
      .mockReturnValue("blob:exact-markdown");
    const revoke = vi
      .spyOn(URL, "revokeObjectURL")
      .mockImplementation(() => undefined);
    const ready = vi.fn(() =>
      expect(screen.getByRole("table")).toBeInTheDocument(),
    );
    const view = render(
      <>
        <RepresentationDownload blob={blob} name="inspection-plan.md" />
        <RepresentationViewer
          blob={blob}
          title="Inspection plan"
          onReady={ready}
        />
      </>,
    );
    expect(
      await screen.findByRole("heading", { name: "Inspection plan", level: 1 }),
    ).toBeInTheDocument();
    expect(
      screen.getByRole("columnheader", { name: "Characteristic" }),
    ).toBeInTheDocument();
    expect(screen.getByRole("cell", { name: "38 mm" })).toBeInTheDocument();
    expect(screen.getByRole("checkbox")).toBeDisabled();
    const source = screen.getByText("View source").closest("details")!;
    expect(source).not.toHaveAttribute("open");
    fireEvent.click(screen.getByText("View source"));
    expect(source.querySelector("pre")?.textContent).toBe(text);
    expect(
      screen.getByRole("link", { name: "Download exact file" }),
    ).toHaveAttribute("download", "inspection-plan.md");
    expect(create).toHaveBeenCalledWith(blob);
    await waitFor(() => expect(ready).toHaveBeenCalledTimes(1));
    view.unmount();
    expect(revoke).toHaveBeenCalledWith("blob:exact-markdown");
  });
  it("keeps Markdown references passive and HTML inert without requesting more evidence", async () => {
    const text =
      '# Passive document\n\n[Remote](https://example.invalid/read) [Local](./secret.md) [Action](javascript:alert(1))\n\n![Remote diagram](https://example.invalid/image.png)\n\n<img src="/api/private" onerror="window.bad=true">\n<script>window.bad=true</script>\n<iframe src="https://example.invalid"></iframe>\n';
    const fetch = vi.spyOn(globalThis, "fetch");
    const view = render(
      <RepresentationViewer
        blob={new Blob([text], { type: "text/markdown" })}
        title="Passive document"
      />,
    );
    await screen.findByRole("heading", { name: "Passive document" });
    expect(screen.getByText("Remote")).toBeInTheDocument();
    expect(screen.getByText("[Image: Remote diagram]")).toBeInTheDocument();
    expect(
      view.container.querySelector(
        "a, img, script, iframe, object, embed, [src], [href], [onerror]",
      ),
    ).toBeNull();
    expect(view.container.querySelector("pre")?.textContent).toBe(text);
    expect(fetch).not.toHaveBeenCalled();
  });
  it("does not interpret ordinary plain text as Markdown", async () => {
    const view = render(
      <RepresentationViewer
        blob={new Blob(["# Plain document"], { type: "text/plain" })}
        title="Plain file"
      />,
    );
    await screen.findByText("# Plain document");
    expect(screen.queryByRole("heading")).not.toBeInTheDocument();
    expect(view.container.querySelector("pre")?.textContent).toBe(
      "# Plain document",
    );
  });
  it("discards a late Markdown read after the engineer opens a different file", async () => {
    const old = new Blob(["# Old requirements"], { type: "text/markdown" });
    let finish: ((text: string) => void) | undefined;
    vi.spyOn(old, "text").mockImplementation(
      () =>
        new Promise((resolve) => {
          finish = resolve;
        }),
    );
    const ready = vi.fn();
    const view = render(
      <RepresentationViewer blob={old} title="Old" onReady={ready} />,
    );
    view.rerender(
      <RepresentationViewer
        blob={new Blob(["# Current requirements"], { type: "text/x-markdown" })}
        title="Current"
        onReady={ready}
      />,
    );
    await screen.findByRole("heading", { name: "Current requirements" });
    await act(async () => {
      finish?.("# Old requirements");
    });
    expect(
      screen.queryByRole("heading", { name: "Old requirements" }),
    ).not.toBeInTheDocument();
    expect(ready).toHaveBeenCalledTimes(1);
  });
  it("waits for a bitmap to load before announcing its preview readiness", async () => {
    vi.spyOn(URL, "createObjectURL").mockReturnValue("blob:ready-preview");
    vi.spyOn(URL, "revokeObjectURL").mockImplementation(() => undefined);
    const ready = vi.fn();
    render(
      <RepresentationViewer
        blob={new Blob(["png"], { type: "image/png" })}
        title="Exact image"
        onReady={ready}
      />,
    );
    const image = await screen.findByRole("img", { name: "Exact image" });
    expect(image.closest(".wp-image-preview")).not.toBeNull();
    expect(ready).not.toHaveBeenCalled();
    fireEvent.load(image);
    expect(ready).toHaveBeenCalledTimes(1);
  });
  it("shows exact assessment-sized JSON as inert text without the smaller prose limit", async () => {
    const text = JSON.stringify({
      schema_version: "wright.process-validation/1",
      summary: { counts: { pass: 25, blocked: 1 } },
      evidence: "x".repeat(80_000),
      note: "<script>window.bad=true</script>",
    });
    const view = render(
      <RepresentationViewer
        blob={new Blob([text], { type: "application/json" })}
        title="Exact assessment"
      />,
    );
    await waitFor(() =>
      expect(view.container.querySelector("pre")?.textContent).toBe(text),
    );
    expect(
      view.container.querySelector("script, iframe, object, embed"),
    ).toBeNull();
    expect(
      screen.queryByText(/exceeds the supported preview size/),
    ).not.toBeInTheDocument();
  });
  it.each([
    ["application/json", 16 * 1024 * 1024 + 1],
    ["text/plain", 65_537],
    ["text/markdown", 65_537],
  ])("rejects oversized %s before reading bytes", async (type, size) => {
    const blob = new Blob(["x".repeat(size)], { type });
    const read = vi.spyOn(blob, "text");
    render(<RepresentationViewer blob={blob} title="Bounded evidence" />);
    expect(
      await screen.findByText(/exceeds the supported preview size/),
    ).toBeInTheDocument();
    expect(read).not.toHaveBeenCalled();
  });
  it("releases thumbnails and never reuses a bitmap for a different blob", () => {
    vi.spyOn(URL, "createObjectURL").mockReturnValue("blob:old-image");
    const revoke = vi
      .spyOn(URL, "revokeObjectURL")
      .mockImplementation(() => undefined);
    const { rerender, unmount } = render(
      <ImageThumbnail
        blob={new Blob(["bitmap"], { type: "image/png" })}
        title="First image"
      />,
    );
    expect(screen.getByAltText("First image")).toBeInTheDocument();
    rerender(
      <ImageThumbnail
        blob={new Blob(["data"], { type: "application/octet-stream" })}
        title="Different file"
      />,
    );
    expect(screen.queryByRole("img")).not.toBeInTheDocument();
    expect(revoke).toHaveBeenCalledWith("blob:old-image");
    unmount();
  });
});
