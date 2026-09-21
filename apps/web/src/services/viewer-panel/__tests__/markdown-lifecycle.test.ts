import { afterEach, expect, it, vi } from "vitest";
import type { CancellationToken } from "../types";
import { PanelHostImpl } from "../panel-host";
import { workspaceService } from "../../workspace-service";
import { MarkdownProvider } from "../providers/markdown-provider";

const roots = vi.hoisted(
  () =>
    [] as Array<{
      render: ReturnType<typeof vi.fn>;
      unmount: ReturnType<typeof vi.fn>;
    }>,
);
vi.mock("react-dom/client", () => ({
  createRoot: () => {
    const root = { render: vi.fn(), unmount: vi.fn() };
    roots.push(root);
    return root;
  },
}));
afterEach(() => {
  vi.restoreAllMocks();
  roots.length = 0;
});

it("defers preview unmount and does not let an old panel dispose the current preview", async () => {
  vi.spyOn(workspaceService, "getFileContentText").mockResolvedValue(
    "# Engineering report",
  );
  const provider = new MarkdownProvider();
  const doc = await provider.openDocument(
    {
      id: "report",
      uri: "report.md",
      name: "report.md",
      extension: "md",
      mimeType: "text/markdown",
    },
    { sessionId: "workspace" },
  );
  const first = new PanelHostImpl(
    "first",
    "Report",
    document.createElement("div"),
  );
  const second = new PanelHostImpl(
    "second",
    "Report",
    document.createElement("div"),
  );
  const token = {
    isCancellationRequested: false,
    onCancellationRequested: () => ({ dispose: () => {} }),
  } as CancellationToken;
  await provider.resolveViewer(doc, first, "preview", token);
  await provider.resolveViewer(doc, second, "preview", token);
  expect(roots[0].unmount).toHaveBeenCalledOnce();
  first.dispose();
  provider.disposeDocument(doc);
  expect(roots[1].unmount).not.toHaveBeenCalled();
  await Promise.resolve();
  expect(roots[1].unmount).toHaveBeenCalledOnce();
  second.dispose();
  await Promise.resolve();
  expect(roots[0].unmount).toHaveBeenCalledOnce();
  expect(roots[1].unmount).toHaveBeenCalledOnce();
});
