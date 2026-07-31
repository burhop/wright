import { useMemo, useState, type ReactElement } from "react";

import { PaneSeparator } from "../workspace/PaneSeparator";
import { ResponsivePaneSwitcher } from "../workspace/ResponsivePaneSwitcher";
import { WorkspaceLayout } from "../workspace/WorkspaceLayout";
import {
  createWorkspaceLayout,
  resolveWorkspaceLayout,
  type WorkspaceLayoutMode,
  type WorkspaceLayoutState,
} from "../workspace/workspace-layout";
import { SurfaceTabs } from "./SurfaceTabs";

type SurfaceStoryState = "ready" | "loading" | "error" | "permission";

interface StoryArgs {
  readonly mode: WorkspaceLayoutMode;
  readonly state: SurfaceStoryState;
}

function storyLayout(
  mode: WorkspaceLayoutMode,
  width: number,
): WorkspaceLayoutState {
  const base = createWorkspaceLayout(width);
  if (mode === "normal") return base;
  if (mode === "narrow")
    return { ...base, mode: "narrow", narrowPane: "surface" };
  return { ...base, mode: "focus", wideMode: "focus" };
}

function SurfaceStory({ mode, state }: StoryArgs): ReactElement {
  const width = mode === "narrow" ? 700 : 1200;
  const [layout, setLayout] = useState(() => storyLayout(mode, width));
  const [selected, setSelected] = useState("graph");
  const resolved = useMemo(
    () => resolveWorkspaceLayout(layout, width),
    [layout, width],
  );
  const status =
    state === "loading"
      ? "Starting graph renderer…"
      : state === "error"
        ? "Renderer failed. Retry or open diagnostics."
        : state === "permission"
          ? "Graph app requests read access to the selected data file."
          : "Interactive graph ready";

  return (
    <div style={{ width, height: 640 }}>
      <WorkspaceLayout
        layout={layout}
        paneContainerWidth={width}
        leftSidebarWidth={260}
        leftSidebarCollapsed
      >
        {layout.mode === "narrow" && (
          <ResponsivePaneSwitcher
            controlsOnly
            activePane={layout.narrowPane}
            onChange={(narrowPane) =>
              setLayout((current) => ({ ...current, narrowPane }))
            }
          />
        )}
        <main
          data-testid="story-surface-pane"
          style={{
            gridColumn: layout.mode === "narrow" ? 1 : 4,
            minWidth: 0,
            display:
              layout.mode === "narrow" && layout.narrowPane !== "surface"
                ? "none"
                : "block",
          }}
        >
          <SurfaceTabs
            tabs={[
              { id: "graph", label: "Graph", closable: true, status: state },
              { id: "brep", label: "BREP", closable: true, status: "ready" },
            ]}
            selectedId={selected}
            onSelect={setSelected}
          />
          <section
            role="tabpanel"
            aria-label={selected === "graph" ? "Graph" : "BREP"}
            style={{ padding: 24 }}
          >
            <h2>{selected === "graph" ? "Quarterly output" : "BREP design"}</h2>
            <p role={state === "error" ? "alert" : "status"}>{status}</p>
            {state === "permission" && (
              <div role="dialog" aria-label="Permission request">
                <button type="button">Allow once</button>
                <button type="button">Deny</button>
              </div>
            )}
          </section>
        </main>
        {layout.mode !== "narrow" && (
          <PaneSeparator
            valueBasisPoints={resolved.chatBasisPoints}
            minimumBasisPoints={resolved.minimumChatBasisPoints}
            maximumBasisPoints={resolved.maximumChatBasisPoints}
            onChange={() => undefined}
          />
        )}
        <aside
          style={{
            gridColumn: layout.mode === "narrow" ? 1 : 6,
            padding: 16,
            display:
              layout.mode === "narrow" && layout.narrowPane !== "chat"
                ? "none"
                : "block",
          }}
        >
          <label>
            Chat instruction
            <textarea defaultValue="Make the graph blue" />
          </label>
        </aside>
      </WorkspaceLayout>
    </div>
  );
}

function requireElement(canvasElement: HTMLElement, selector: string): void {
  if (!canvasElement.querySelector(selector)) {
    throw new Error(`Story is missing required element: ${selector}`);
  }
}

const meta = {
  title: "Workspace Surfaces/Adaptive workspace",
  component: SurfaceStory,
};

export default meta;

export const Normal = {
  args: { mode: "normal", state: "ready" } satisfies StoryArgs,
  play: ({ canvasElement }: { canvasElement: HTMLElement }) => {
    requireElement(canvasElement, '[role="separator"]');
  },
};

export const Focus = {
  args: { mode: "focus", state: "ready" } satisfies StoryArgs,
  play: ({ canvasElement }: { canvasElement: HTMLElement }) => {
    requireElement(canvasElement, '[data-wide-layout-mode="focus"]');
  },
};

export const Narrow = {
  args: { mode: "narrow", state: "ready" } satisfies StoryArgs,
  play: ({ canvasElement }: { canvasElement: HTMLElement }) => {
    requireElement(canvasElement, '[aria-label="Workspace pane"]');
  },
};

export const Loading = {
  args: { mode: "normal", state: "loading" } satisfies StoryArgs,
  play: ({ canvasElement }: { canvasElement: HTMLElement }) => {
    requireElement(canvasElement, '[role="status"]');
  },
};

export const ErrorState = {
  args: { mode: "normal", state: "error" } satisfies StoryArgs,
  play: ({ canvasElement }: { canvasElement: HTMLElement }) => {
    requireElement(canvasElement, '[role="alert"]');
  },
};

export const Permission = {
  args: { mode: "normal", state: "permission" } satisfies StoryArgs,
  play: ({ canvasElement }: { canvasElement: HTMLElement }) => {
    requireElement(
      canvasElement,
      '[role="dialog"][aria-label="Permission request"]',
    );
  },
};
