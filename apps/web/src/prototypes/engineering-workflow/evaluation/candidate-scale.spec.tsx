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

    class DOMMatrixReadOnlyMock {
      readonly m22 = 1;
    }

    vi.stubGlobal("DOMMatrixReadOnly", DOMMatrixReadOnlyMock);
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
        <ScaleHarness
          Canvas={ReactFlowWorkflowCanvas}
          blockCount={blockCount}
        />,
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
  it("focuses one phase of the 100-block fixture without changing the workflow", async () => {
    render(<ScaleHarness Canvas={ReactFlowWorkflowCanvas} blockCount={100} />);

    const verifyPhase = await screen.findByRole(
      "button",
      { name: "Focus Verify phase" },
      { timeout: 20_000 },
    );
    expect(screen.getByText("Showing 100 of 100 blocks")).toBeInTheDocument();

    fireEvent.click(verifyPhase);

    await waitFor(
      () => {
        expect(
          screen.getByText("Showing 33 of 100 blocks"),
        ).toBeInTheDocument();
        expect(verifyPhase).toHaveAttribute("aria-pressed", "true");
      },
      { timeout: 20_000 },
    );
    const firstVerifyBlock = await screen.findByRole("button", {
      name: /S035\. Scale Step 35/,
    });
    expect(firstVerifyBlock).toHaveAttribute("aria-pressed", "true");
    expect(
      screen.queryByRole("button", { name: /S100\. Scale Step 100/ }),
    ).not.toBeInTheDocument();

    fireEvent.click(screen.getByRole("button", { name: "All phases" }));
    expect(
      await screen.findByRole(
        "button",
        { name: /S100\. Scale Step 100/ },
        { timeout: 20_000 },
      ),
    ).toBeInTheDocument();
  }, 30_000);
});
