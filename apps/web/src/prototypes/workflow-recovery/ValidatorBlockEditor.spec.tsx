import { fireEvent, render, screen } from "@testing-library/react";
import { expect, it, vi } from "vitest";
import { ValidatorBlockEditor } from "./ValidatorBlockEditor";
import { createAuthoringObject } from "./authoring-objects";
import { initialWorkflow, initialLayout } from "./model";

it("selects the actual packaged profile through normal editing commands", () => {
  const add = createAuthoringObject(
    "process-validator",
    initialWorkflow,
    initialLayout,
  );
  const apply = vi.fn(() => true);
  render(
    <ValidatorBlockEditor
      block={add.block}
      workflow={initialWorkflow}
      readOnly={false}
      onApply={apply}
    />,
  );
  fireEvent.change(
    screen.getByRole("combobox", { name: "Validation profile" }),
    { target: { value: "structured-demo" } },
  );
  expect(apply).toHaveBeenCalledOnce();
  const commands = apply.mock.calls[0] as unknown as [
    { kind: string; key?: string; value?: string }[],
  ];
  const configuration = commands[0].find((item) => item.key === "validation")!;
  const value = JSON.parse(configuration.value!);
  expect(value.profile.name).toBe("structured-demo");
  expect(value.profile.reference.sha256).toMatch(/^[a-f0-9]{64}$/);
  expect(value.baseline.id).toBe("structured-demo");
  expect(screen.queryByLabelText("MCP server")).toBeNull();
});

it("preserves the running/read-only authoring boundary", () => {
  const add = createAuthoringObject(
    "process-validator",
    initialWorkflow,
    initialLayout,
  );
  render(
    <ValidatorBlockEditor
      block={add.block}
      workflow={initialWorkflow}
      readOnly
      onApply={() => false}
    />,
  );
  expect(
    screen.getByRole("combobox", { name: "Validation profile" }),
  ).toBeDisabled();
});
