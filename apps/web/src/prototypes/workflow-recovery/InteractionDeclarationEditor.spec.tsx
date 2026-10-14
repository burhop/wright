import { useState } from "react";
import {
  cleanup,
  fireEvent,
  render,
  screen,
  within,
} from "@testing-library/react";
import { afterEach, describe, expect, it, vi } from "vitest";
import declaredSource from "../../../../../specs/083-process-working-interfaces/fixtures/declared-human-input.workflow.wflow?raw";
import {
  initialWorkflow,
  initialLayout,
  cloneWorkflow,
  type RecoveryWorkflow,
} from "./model";
import {
  acceptRecoveryResult,
  applyRecoveryBatch,
  recoveryCommandBatch,
  type RecoveryCommand,
} from "./command-system";
import {
  formatRecoveryAuthoringSource,
  parseRecoveryAuthoringSource,
} from "./recovery-authoring";
import {
  AUTHORING_TEMPLATES,
  createAuthoringObject,
} from "./authoring-objects";
import { hydrateAuthoringLayout } from "./authoring-positioning";
import {
  declarationEditorKey,
  interactionObject,
} from "./interaction-settings";
import {
  InputDeclarationEditor,
  HumanInputDeclarationEditor,
} from "./InteractionDeclarationEditor";
import { AuthoringCreateRail } from "./AuthoringControls";

afterEach(cleanup);
function workflow() {
  const parsed = parseRecoveryAuthoringSource(declaredSource, {
    ...cloneWorkflow(initialWorkflow),
    workflowId: "workflow.test",
  });
  expect(parsed.ok).toBe(true);
  return parsed.workflow!;
}
function Harness({
  initial = workflow(),
  id = "block.brief",
  readOnly = false,
  accepted = vi.fn(),
}: {
  initial?: RecoveryWorkflow;
  id?: string;
  readOnly?: boolean;
  accepted?: (commands: RecoveryCommand[]) => void;
}) {
  const [current, setCurrent] = useState(initial);
  const block = current.blocks.find((item) => item.id === id)!;
  const onApply = (commands: RecoveryCommand[]) => {
    const layout = hydrateAuthoringLayout(current);
    const result = applyRecoveryBatch(
      current,
      layout,
      recoveryCommandBatch(current.revision, "form", commands),
    );
    if (!result.ok) return false;
    setCurrent(acceptRecoveryResult(current, layout, result)!.workflow);
    accepted(commands);
    return true;
  };
  return (
    <>
      {id === "block.brief" ? (
        <InputDeclarationEditor
          key={declarationEditorKey(block)}
          block={block}
          readOnly={readOnly}
          onApply={onApply}
        />
      ) : (
        <HumanInputDeclarationEditor
          key={declarationEditorKey(block)}
          block={block}
          workflow={current}
          readOnly={readOnly}
          onApply={onApply}
        />
      )}
      <output data-testid="accepted-source">
        {formatRecoveryAuthoringSource(current).text}
      </output>
    </>
  );
}
describe("interaction declaration inspector", () => {
  it("authors a bounded unresolved-fields condition from a connected structured task result", () => {
    const initial = workflow();
    const evidence = initial.relationships.find(
      (edge) =>
        edge.targetId ===
        initial.blocks.find((block) => block.id === "block.choice")!
          .inputPortIds[0],
    )!;
    for (const port of initial.ports.filter((port) =>
      [evidence.sourceId, evidence.targetId].includes(port.id),
    ))
      port.typeId = "type.result.structured";
    const accepted = vi.fn();
    render(<Harness initial={initial} id="block.choice" accepted={accepted} />);
    expect(screen.getByLabelText("Ask for input")).toHaveValue("always");
    expect(accepted).not.toHaveBeenCalled();
    fireEvent.change(screen.getByLabelText("Ask for input"), {
      target: { value: "unresolved_fields" },
    });
    expect(screen.getByLabelText("Requirements resolution result")).toHaveValue(
      "first.first_out",
    );
    fireEvent.click(
      screen.getByRole("button", { name: "Apply response declaration" }),
    );
    expect(accepted).toHaveBeenCalledOnce();
    const reopened = parseRecoveryAuthoringSource(
      screen.getByTestId("accepted-source").textContent!,
      initial,
    );
    expect(reopened.ok).toBe(true);
    expect(
      interactionObject(
        reopened.workflow!.blocks.find((block) => block.id === "block.choice")!,
        "human_interaction",
      ),
    ).toMatchObject({
      version: 3,
      when: {
        kind: "unresolved_fields",
        source: "first.first_out",
        fields: ["selection"],
      },
    });
    expect(reopened.workflow!.relationships).toEqual(initial.relationships);
    fireEvent.change(screen.getByLabelText("Ask for input"), {
      target: { value: "always" },
    });
    fireEvent.click(
      screen.getByRole("button", { name: "Apply response declaration" }),
    );
    const always = parseRecoveryAuthoringSource(
      screen.getByTestId("accepted-source").textContent!,
      initial,
    );
    const declaration = interactionObject(
      always.workflow!.blocks.find((block) => block.id === "block.choice")!,
      "human_interaction",
    )!;
    expect(declaration.version).toBe(2);
    expect(declaration.when).toBeUndefined();
  });
  it("does not invent a resolution source when no structured task result is connected", () => {
    const accepted = vi.fn();
    render(<Harness id="block.choice" accepted={accepted} />);
    fireEvent.change(screen.getByLabelText("Ask for input"), {
      target: { value: "unresolved_fields" },
    });
    expect(screen.getByLabelText("Requirements resolution result")).toHaveValue(
      "",
    );
    expect(screen.getByText(/Connect a structured result from/)).toBeTruthy();
    fireEvent.click(
      screen.getByRole("button", { name: "Apply response declaration" }),
    );
    expect(screen.getByRole("alert")).toHaveTextContent(
      "connected structured task result",
    );
    expect(accepted).not.toHaveBeenCalled();
  });
  it("does not accept any change on mount and applies an explicit default with the normal command owner", () => {
    const accepted = vi.fn();
    render(<Harness accepted={accepted} />);
    expect(accepted).not.toHaveBeenCalled();
    const value = {
      version: 1,
      value_schema: { type: "number", minimum: 0 },
      required: true,
      unit: "mm",
      default: 0,
    };
    fireEvent.change(screen.getByLabelText("Input declaration (JSON)"), {
      target: { value: JSON.stringify(value) },
    });
    expect(accepted).not.toHaveBeenCalled();
    fireEvent.click(
      screen.getByRole("button", { name: "Apply input declaration" }),
    );
    expect(accepted).toHaveBeenCalledTimes(1);
    const saved = parseRecoveryAuthoringSource(
      screen.getByTestId("accepted-source").textContent!,
      workflow(),
    );
    expect(saved.ok).toBe(true);
    expect(
      interactionObject(
        saved.workflow!.blocks.find((item) => item.id === "block.brief")!,
        "interaction_input",
      ),
    ).toEqual(value);
    expect(
      JSON.parse(
        (
          screen.getByLabelText(
            "Input declaration (JSON)",
          ) as HTMLTextAreaElement
        ).value,
      ),
    ).toEqual(value);
  });
  it("removes only preparation metadata through explicit inferred-schema selection", () => {
    const accepted = vi.fn();
    render(<Harness accepted={accepted} />);
    fireEvent.click(
      screen.getByRole("button", { name: "Use inferred input schema" }),
    );
    expect(accepted).toHaveBeenCalledTimes(1);
    expect(screen.getByTestId("accepted-source")).not.toHaveTextContent(
      '"interaction_input":',
    );
    expect(screen.getByTestId("accepted-source")).toHaveTextContent(
      '"human_interaction":',
    );
    expect(
      screen.queryByRole("button", { name: "Use inferred input schema" }),
    ).not.toBeInTheDocument();
  });
  it("shows invalid JSON without applying it or losing the existing declaration", () => {
    const accepted = vi.fn();
    render(<Harness accepted={accepted} />);
    const original = screen.getByTestId("accepted-source").textContent;
    fireEvent.change(screen.getByLabelText("Input declaration (JSON)"), {
      target: { value: "broken" },
    });
    fireEvent.click(
      screen.getByRole("button", { name: "Apply input declaration" }),
    );
    expect(screen.getByRole("alert")).toHaveTextContent("complete JSON object");
    expect(accepted).not.toHaveBeenCalled();
    expect(screen.getByTestId("accepted-source").textContent).toBe(original);
  });
  it("reports rejection by the command owner for applying and removing metadata", () => {
    const block = workflow().blocks.find((item) => item.id === "block.brief")!;
    const onApply = vi.fn(() => false);
    render(
      <InputDeclarationEditor
        block={block}
        readOnly={false}
        onApply={onApply}
      />,
    );
    fireEvent.click(
      screen.getByRole("button", { name: "Apply input declaration" }),
    );
    expect(screen.getByRole("alert")).toHaveTextContent("not applied");
    fireEvent.click(
      screen.getByRole("button", { name: "Use inferred input schema" }),
    );
    expect(screen.getByRole("alert")).toHaveTextContent("not removed");
    expect(onApply).toHaveBeenCalledTimes(2);
  });
  it("keeps planned instructions and the response schema together through accepted source", () => {
    const accepted = vi.fn();
    render(<Harness id="block.choice" accepted={accepted} />);
    const original = JSON.parse(
      (
        screen.getByLabelText(
          "Response declaration (JSON)",
        ) as HTMLTextAreaElement
      ).value,
    );
    fireEvent.change(screen.getByLabelText("Instructions for the user"), {
      target: { value: "Review both measured candidates and select one." },
    });
    const draft = JSON.parse(
      (
        screen.getByLabelText(
          "Response declaration (JSON)",
        ) as HTMLTextAreaElement
      ).value,
    );
    expect(draft.response_schema).toEqual(original.response_schema);
    expect(accepted).not.toHaveBeenCalled();
    fireEvent.click(
      screen.getByRole("button", { name: "Apply response declaration" }),
    );
    expect(accepted).toHaveBeenCalledTimes(1);
    const saved = parseRecoveryAuthoringSource(
      screen.getByTestId("accepted-source").textContent!,
      workflow(),
    );
    expect(saved.ok).toBe(true);
    const block = saved.workflow!.blocks.find(
      (item) => item.id === "block.choice",
    )!;
    expect(block.instructions).toBe(draft.instructions);
    expect(interactionObject(block, "human_interaction")).toEqual(draft);
    expect(saved.workflow!.relationships).toEqual(workflow().relationships);
  });
  it("contains incomplete response JSON and a changed output-port identity", () => {
    const accepted = vi.fn();
    render(<Harness id="block.choice" accepted={accepted} />);
    const original = JSON.parse(
      (
        screen.getByLabelText(
          "Response declaration (JSON)",
        ) as HTMLTextAreaElement
      ).value,
    );
    fireEvent.change(screen.getByLabelText("Response declaration (JSON)"), {
      target: { value: "{" },
    });
    expect(screen.getByLabelText("Instructions for the user")).toBeDisabled();
    fireEvent.click(
      screen.getByRole("button", { name: "Apply response declaration" }),
    );
    expect(screen.getByRole("alert")).toHaveTextContent("complete JSON object");
    fireEvent.change(screen.getByLabelText("Response declaration (JSON)"), {
      target: {
        value: JSON.stringify({ ...original, output_port: "another" }),
      },
    });
    fireEvent.click(
      screen.getByRole("button", { name: "Apply response declaration" }),
    );
    expect(screen.getByRole("alert")).toHaveTextContent(
      "single structured response output",
    );
    expect(accepted).not.toHaveBeenCalled();
  });
  it("authors a bounded number and units hint without JSON and preserves evidence and answer connections", () => {
    const accepted = vi.fn();
    render(<Harness id="block.choice" accepted={accepted} />);
    fireEvent.change(screen.getByLabelText("Field name"), {
      target: { value: "width" },
    });
    fireEvent.change(screen.getByLabelText("Field label"), {
      target: { value: "Width (mm)" },
    });
    fireEvent.change(screen.getByLabelText("Answer type"), {
      target: { value: "number" },
    });
    fireEvent.change(screen.getByLabelText("Help text / units"), {
      target: { value: "Enter the measured width in mm." },
    });
    fireEvent.change(screen.getByLabelText("Minimum value"), {
      target: { value: "0" },
    });
    fireEvent.change(screen.getByLabelText("Maximum value"), {
      target: { value: "100" },
    });
    expect(accepted).not.toHaveBeenCalled();
    fireEvent.click(
      screen.getByRole("button", { name: "Apply response declaration" }),
    );
    const saved = parseRecoveryAuthoringSource(
      screen.getByTestId("accepted-source").textContent!,
      workflow(),
    );
    expect(saved.ok).toBe(true);
    const response = interactionObject(
      saved.workflow!.blocks.find((block) => block.id === "block.choice")!,
      "human_interaction",
    )!;
    expect(response.response_schema).toEqual({
      type: "object",
      properties: {
        width: {
          type: "number",
          title: "Width (mm)",
          description: "Enter the measured width in mm.",
          minimum: 0,
          maximum: 100,
        },
      },
      required: ["width"],
      additionalProperties: false,
    });
    expect(response.output_port).toBe("choice_response");
    expect(saved.workflow!.relationships).toEqual(workflow().relationships);
    expect(saved.workflow!.ports).toEqual(workflow().ports);
  });
  it("adds choices and optional boolean answers, removes a field and saves the declared shape", () => {
    render(<Harness id="block.choice" />);
    fireEvent.click(screen.getByRole("button", { name: "Add answer field" }));
    const second = within(screen.getByRole("group", { name: "Field 2" }));
    fireEvent.change(second.getByLabelText("Field name"), {
      target: { value: "confirmed" },
    });
    fireEvent.change(second.getByLabelText("Answer type"), {
      target: { value: "boolean" },
    });
    fireEvent.click(second.getByLabelText("Required answer"));
    const first = within(screen.getByRole("group", { name: "Field 1" }));
    fireEvent.change(first.getByLabelText("Choices (one per line)"), {
      target: { value: "Measured candidate A\nMeasured candidate B" },
    });
    fireEvent.click(
      screen.getByRole("button", { name: "Apply response declaration" }),
    );
    const current = JSON.parse(
      (
        screen.getByLabelText(
          "Response declaration (JSON)",
        ) as HTMLTextAreaElement
      ).value,
    );
    expect(current.response_schema.properties.confirmed).toEqual({
      type: "boolean",
      title: "",
    });
    expect(current.response_schema.properties.selection.enum).toEqual([
      "Measured candidate A",
      "Measured candidate B",
    ]);
    expect(current.response_schema.required).toEqual(["selection"]);
    fireEvent.click(
      screen.getByRole("button", { name: "Remove field selection" }),
    );
    fireEvent.click(
      screen.getByRole("button", { name: "Apply response declaration" }),
    );
    expect(
      JSON.parse(
        (
          screen.getByLabelText(
            "Response declaration (JSON)",
          ) as HTMLTextAreaElement
        ).value,
      ).response_schema,
    ).toEqual({
      type: "object",
      properties: { confirmed: { type: "boolean", title: "" } },
      required: [],
      additionalProperties: false,
    });
  });
  it("retains advanced nested fields and constraints while editing a simple label", () => {
    render(<Harness id="block.choice" />);
    const declaration = JSON.parse(
      (
        screen.getByLabelText(
          "Response declaration (JSON)",
        ) as HTMLTextAreaElement
      ).value,
    );
    declaration.response_schema = {
      type: "object",
      $defs: { metric: { type: "number", multipleOf: 0.5 } },
      properties: {
        label: { type: "string", maxLength: 40, default: "comparison" },
        metrics: {
          type: "array",
          items: { $ref: "#/$defs/metric" },
          minItems: 2,
        },
      },
      required: ["metrics"],
      additionalProperties: false,
    };
    fireEvent.change(screen.getByLabelText("Response declaration (JSON)"), {
      target: { value: JSON.stringify(declaration) },
    });
    fireEvent.change(screen.getByLabelText("Field label"), {
      target: { value: "Comparison name" },
    });
    fireEvent.click(
      screen.getByRole("button", { name: "Apply response declaration" }),
    );
    const saved = JSON.parse(
      (
        screen.getByLabelText(
          "Response declaration (JSON)",
        ) as HTMLTextAreaElement
      ).value,
    );
    expect(saved.response_schema).toEqual({
      ...declaration.response_schema,
      properties: {
        ...declaration.response_schema.properties,
        label: {
          ...declaration.response_schema.properties.label,
          title: "Comparison name",
        },
      },
    });
    expect(
      screen.getByText(/This field uses an advanced schema/),
    ).toBeInTheDocument();
  });
  it("offers Request input alongside inputs while creating a human task with optional evidence", () => {
    expect(
      AUTHORING_TEMPLATES.find((template) => template.id === "human-input"),
    ).toMatchObject({
      group: "input",
      label: "Request input",
    });
    const created = createAuthoringObject(
      "human-input",
      workflow(),
      initialLayout,
    );
    expect(created.block.configuration).toEqual({
      authoring_template: "human-input",
    });
    expect(
      created.ports.find((port) => port.direction === "input"),
    ).toMatchObject({ required: false, cardinality: "optional" });
    const initial = {
      ...workflow(),
      blocks: [...workflow().blocks, created.block],
      ports: [...workflow().ports, ...created.ports],
    };
    render(<Harness initial={initial} id={created.block.id} />);
    fireEvent.change(screen.getByLabelText("Instructions for the user"), {
      target: { value: "Choose the analysis interval in seconds." },
    });
    fireEvent.click(screen.getByRole("button", { name: "Add answer field" }));
    fireEvent.click(
      screen.getByRole("button", { name: "Apply response declaration" }),
    );
    const saved = parseRecoveryAuthoringSource(
      screen.getByTestId("accepted-source").textContent!,
      initial,
    );
    expect(saved.ok).toBe(true);
    const block = saved.workflow!.blocks.find(
      (item) => item.id === created.block.id,
    )!;
    expect(block.executionKind).toBe("human");
    expect(block.configuration.input_mode).toBeUndefined();
    expect(interactionObject(block, "human_interaction")!.version).toBe(2);
    expect(
      interactionObject(block, "human_interaction")!.response_schema,
    ).toEqual({
      type: "object",
      properties: { answer: { type: "string", title: "" } },
      required: ["answer"],
      additionalProperties: false,
    });
  });
  it.each(["block.brief", "block.choice"])(
    "disables every mutation control for a read-only %s",
    (id) => {
      const accepted = vi.fn();
      render(<Harness id={id} readOnly accepted={accepted} />);
      for (const textarea of screen.getAllByRole("textbox"))
        expect(textarea).toBeDisabled();
      for (const select of screen.queryAllByRole("combobox"))
        expect(select).toBeDisabled();
      for (const checkbox of screen.queryAllByRole("checkbox"))
        expect(checkbox).toBeDisabled();
      for (const button of screen.getAllByRole("button")) {
        expect(button).toBeDisabled();
        fireEvent.click(button);
      }
      expect(accepted).not.toHaveBeenCalled();
    },
  );
  it("keeps a newly created human step a draft until explicit declaration", () => {
    const current = workflow();
    const created = createAuthoringObject(
      "human-input",
      current,
      initialLayout,
    );
    const onApply = vi.fn(() => true);
    render(
      <HumanInputDeclarationEditor
        block={created.block}
        workflow={{
          ...current,
          blocks: [...current.blocks, created.block],
          ports: [...current.ports, ...created.ports],
        }}
        readOnly={false}
        onApply={onApply}
      />,
    );
    expect(screen.getByRole("status")).toHaveTextContent("draft");
    expect(screen.getByLabelText("Instructions for the user")).toHaveValue("");
    fireEvent.click(
      screen.getByRole("button", { name: "Apply response declaration" }),
    );
    expect(screen.getByRole("alert")).toHaveTextContent(
      "meaningful instructions",
    );
    expect(onApply).not.toHaveBeenCalled();
  });
  it("lets an author choose Request input directly from the Input palette", () => {
    const onCreate = vi.fn();
    render(<AuthoringCreateRail disabled={false} onCreate={onCreate} />);
    fireEvent.click(screen.getByRole("button", { name: "Add step" }));
    fireEvent.click(screen.getByRole("button", { name: "Input" }));
    const inputChoices = within(
      screen.getByRole("region", { name: "Input templates" }),
    );
    fireEvent.click(
      inputChoices.getByRole("button", { name: /Request input/ }),
    );
    expect(onCreate).toHaveBeenCalledExactlyOnceWith("human-input");
  });
});
