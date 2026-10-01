import { useState } from "react";
import { cleanup, fireEvent, render, screen } from "@testing-library/react";
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
import { createAuthoringObject } from "./authoring-objects";
import { hydrateAuthoringLayout } from "./authoring-positioning";
import {
  declarationEditorKey,
  interactionObject,
} from "./interaction-settings";
import {
  InputDeclarationEditor,
  HumanInputDeclarationEditor,
} from "./InteractionDeclarationEditor";

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
  it.each(["block.brief", "block.choice"])(
    "disables every mutation control for a read-only %s",
    (id) => {
      const accepted = vi.fn();
      render(<Harness id={id} readOnly accepted={accepted} />);
      for (const textarea of screen.getAllByRole("textbox"))
        expect(textarea).toBeDisabled();
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
});
