import {
  cleanup,
  fireEvent,
  render,
  screen,
  waitFor,
} from "@testing-library/react";
import {
  afterAll,
  afterEach,
  beforeAll,
  describe,
  expect,
  it,
  vi,
} from "vitest";
import { useState, type ComponentType } from "react";

import type { EngineeringWorkflowCanvasRenderProps } from "../EngineeringWorkflowVisualSlice";
import { ReactFlowWorkflowCanvas } from "../canvas/react-flow/ReactFlowWorkflowCanvas";
import {
  createScaleWorkflow,
  type WorkflowScale,
} from "../fixtures/scale-workflows";

function ScaleHarness({
  Canvas,
  blockCount,
}: {
  Canvas: ComponentType<EngineeringWorkflowCanvasRenderProps>;
  blockCount: WorkflowScale;
}) {
  const workflow = createScaleWorkflow(blockCount);
  const [selectedBlockId, setSelectedBlockId] = useState(
    workflow.blocks[0].blockId,
  );
  return (
    <Canvas
      workflow={workflow}
      selectedBlockId={selectedBlockId}
      onSelectBlock={setSelectedBlockId}
    />
  );
}

describe("React Flow scale interaction", () => {
  const originalGetBoundingClientRect =
    HTMLElement.prototype.getBoundingClientRect;

  beforeAll(() => {
    class ResizeObserverMock {
      private readonly callback: ResizeObserverCallback;

      constructor(callback: ResizeObserverCallback) {
        this.callback = callback;
      }

      observe(target: Element) {
        this.callback(
          [
            {
              target,
              contentRect: target.getBoundingClientRect(),
            } as ResizeObserverEntry,
          ],
          this as unknown as ResizeObserver,
        );
      }

      unobserve() {}
      disconnect() {}
    }

    vi.stubGlobal("ResizeObserver", ResizeObserverMock);
    vi.stubGlobal("requestAnimationFrame", (callback: FrameRequestCallback) => {
      callback(performance.now());
      return 1;
    });
    vi.spyOn(HTMLElement.prototype, "getBoundingClientRect").mockReturnValue({
      x: 0,
      y: 0,
      width: 1200,
      height: 800,
      top: 0,
      right: 1200,
      bottom: 800,
      left: 0,
      toJSON: () => ({}),
    });
  });

  afterEach(() => cleanup());

  afterAll(() => {
    vi.unstubAllGlobals();
    HTMLElement.prototype.getBoundingClientRect = originalGetBoundingClientRect;
    vi.restoreAllMocks();
  });

  it.each([25, 100] as const)(
    "renders, selects, and focuses the %i-block fixture",
    async (blockCount) => {
      const startedAt = performance.now();
      render(
        <ScaleHarness Canvas={ReactFlowWorkflowCanvas} blockCount={blockCount} />,
      );

      const lastBlock = await screen.findByRole(
        "button",
        {
          name: new RegExp(
            `S${String(blockCount).padStart(3, "0")}\\. Scale Step ${blockCount}`,
          ),
        },
        { timeout: 20_000 },
      );
      fireEvent.click(lastBlock);
      await waitFor(
        () =>
          expect(
            screen.getByRole("button", {
              name: new RegExp(
                `S${String(blockCount).padStart(3, "0")}\\. Scale Step ${blockCount}`,
              ),
            }),
          ).toHaveAttribute("aria-pressed", "true"),
        { timeout: 20_000 },
      );
      const selectedLastBlock = screen.getByRole("button", {
        name: new RegExp(
          `S${String(blockCount).padStart(3, "0")}\\. Scale Step ${blockCount}`,
        ),
      });
      selectedLastBlock.focus();
      expect(selectedLastBlock).toHaveFocus();

      const elapsedMilliseconds = performance.now() - startedAt;
      console.info(
        `[canvas-scale] react-flow ${blockCount} blocks: ${elapsedMilliseconds.toFixed(1)} ms`,
      );
      expect(elapsedMilliseconds).toBeLessThan(30_000);
    },
    30_000,
  );
});
