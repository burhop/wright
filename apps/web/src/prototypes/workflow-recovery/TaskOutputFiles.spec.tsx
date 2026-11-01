import { useState } from "react";
import userEvent from "@testing-library/user-event";
import { cleanup, fireEvent, render, screen } from "@testing-library/react";
import { afterEach, expect, it, vi } from "vitest";
import { TaskOutputFiles } from "./TaskOutputFiles";
import { parseRecoverySourceDocument } from "./recovery-authoring";
import source from "../../../../../prototypes/desktop-harness/engineering-experience/handle/replacement-handle-draft.workflow.wflow?raw";

afterEach(cleanup);
function fixture() {
  const workflow = parseRecoverySourceDocument(source, 1).workflow!;
  const block = workflow.blocks.find((b) => b.id === "block.cad")!;
  const paths = {
    cad_geometry:
      "results/{{wright.run_id}}/{{wright.producer_attempt}}/handle.step",
    cad_mesh:
      "results/{{wright.run_id}}/{{wright.producer_attempt}}/handle.stl",
    cad_preview:
      "results/{{wright.run_id}}/{{wright.producer_attempt}}/preview.png",
  };
  block.configuration.expected_file_ports = JSON.stringify(paths);
  block.configuration.expected_files = [
    ...Object.values(paths),
    "inspection/measurements.csv",
  ].join("\n");
  return { workflow, block, paths };
}

it("changes one filename atomically while preserving other outputs, run templates and additional required evidence", () => {
  const { workflow, block, paths } = fixture();
  const apply = vi.fn(() => true);
  render(
    <TaskOutputFiles
      block={block}
      workflow={workflow}
      readOnly={false}
      onApply={apply}
    />,
  );
  fireEvent.change(screen.getByLabelText("Handle STEP"), {
    target: {
      value:
        "results/{{wright.run_id}}/{{wright.producer_attempt}}/revised.step",
    },
  });
  const commands = apply.mock.calls[0] as unknown as [
    Array<{ key: string; value: string }>,
  ];
  const settings = Object.fromEntries(commands[0].map((c) => [c.key, c.value]));
  const mapping = JSON.parse(settings.expected_file_ports!);
  expect(mapping).toEqual({
    ...paths,
    cad_geometry:
      "results/{{wright.run_id}}/{{wright.producer_attempt}}/revised.step",
  });
  expect(settings.expected_files!.split("\n")).toEqual([
    paths.cad_mesh,
    paths.cad_preview,
    "inspection/measurements.csv",
    mapping.cad_geometry,
  ]);
  expect(apply).toHaveBeenCalledTimes(1);
});

it("does not silently replace malformed saved mappings", () => {
  const { workflow, block } = fixture();
  block.configuration.expected_file_ports = "not a mapping";
  const apply = vi.fn(() => true);
  render(
    <TaskOutputFiles
      block={block}
      workflow={workflow}
      readOnly={false}
      onApply={apply}
    />,
  );
  expect(screen.getByRole("alert")).toHaveTextContent(
    "Correct expected_file_ports in Source",
  );
  expect(apply).not.toHaveBeenCalled();
  expect(screen.queryByRole("textbox")).toBeNull();
});

it("shows accepted mappings read-only without changing the workflow", () => {
  const { workflow, block, paths } = fixture();
  const apply = vi.fn(() => true);
  render(
    <TaskOutputFiles
      block={block}
      workflow={workflow}
      readOnly
      onApply={apply}
    />,
  );
  expect(screen.getByLabelText("Handle STEP")).toHaveValue(paths.cad_geometry);
  expect(screen.getByLabelText("Handle STEP")).toHaveAttribute("readonly");
  fireEvent.blur(screen.getByLabelText("Other files to check"));
  expect(apply).not.toHaveBeenCalled();
});

it("allows typing another evidence filename on a new line without losing the newline", async () => {
  const original = fixture();
  function Harness() {
    const [block, setBlock] = useState(original.block);
    return (
      <TaskOutputFiles
        block={block}
        workflow={original.workflow}
        readOnly={false}
        onApply={(commands) => {
          setBlock((previous) => ({
            ...previous,
            configuration: {
              ...previous.configuration,
              ...Object.fromEntries(
                commands
                  .filter((c) => c.kind === "set_block_configuration")
                  .map((c) => [c.key, c.value]),
              ),
            },
          }));
          return true;
        }}
      />
    );
  }
  render(<Harness />);
  const user = userEvent.setup();
  await user.click(screen.getByText("Additional required files"));
  const extra = screen.getByLabelText("Other files to check");
  await user.click(extra);
  await user.keyboard("{End}{Enter}");
  expect(extra).toHaveValue("inspection/measurements.csv\n");
  await user.keyboard("inspection/review notes.txt");
  expect(extra).toHaveValue(
    "inspection/measurements.csv\ninspection/review notes.txt",
  );
  await user.tab();
  expect(extra).toHaveValue(
    "inspection/measurements.csv\ninspection/review notes.txt",
  );
  expect(screen.getByLabelText("Handle STEP")).toHaveValue(
    original.paths.cad_geometry,
  );
});
