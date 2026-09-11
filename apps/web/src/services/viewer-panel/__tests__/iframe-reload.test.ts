import { afterEach, expect, it, vi } from "vitest";
import { workspaceService } from "../../workspace-service";
import { IframeProvider } from "../providers/iframe-provider";
import { PanelHostImpl } from "../panel-host";

const disposals: (() => void)[] = [];
afterEach(() => {
  disposals.splice(0).forEach((dispose) => dispose());
  vi.restoreAllMocks();
});
const token = {
  isCancellationRequested: false,
  onCancellationRequested: () => ({ dispose() {} }),
};
it("never leaves a visibly actionable old file link after its listener is removed during samehost refresh", async () => {
  vi.spyOn(workspaceService, "getFileContentText").mockResolvedValue(
    '<a href="parts/assembly.csv">Assembly</a>',
  );
  const container = document.createElement("div");
  document.body.append(container);
  const host = new PanelHostImpl("same", "Report", container);
  const provider = new IframeProvider();
  const model = await provider.openDocument(
    {
      id: "report.html",
      uri: "report.html",
      name: "report.html",
      extension: "html",
      mimeType: "text/html",
    },
    { sessionId: "owned" },
  );
  disposals.push(() => {
    host.dispose();
    provider.disposeDocument(model);
    container.remove();
  });
  const received: unknown[] = [];
  container.addEventListener("viewer-message", (event) =>
    received.push((event as CustomEvent).detail),
  );
  await provider.resolveViewer(model, host, "preview", token);
  const old = container.querySelector("iframe")!;
  const id = new DOMParser()
    .parseFromString(old.srcdoc, "text/html")
    .querySelector("a")!
    .getAttribute("data-wright-file-link");
  let finish!: (html: string) => void;
  vi.mocked(workspaceService.getFileContentText).mockReturnValueOnce(
    new Promise((resolve) => {
      finish = resolve;
    }),
  );
  const replacement = provider.resolveViewer(model, host, "preview", token);
  try {
    if (container.querySelector("iframe") === old) {
      window.dispatchEvent(
        new MessageEvent("message", {
          source: old.contentWindow,
          data: { type: "wright-open-workspace-file", id },
        }),
      );
      expect(received).toEqual([
        {
          type: "open-workspace-file",
          path: "/parts/assembly.csv",
          sessionId: "owned",
        },
      ]);
    } else {
      expect(container.querySelector("[role=status]")?.textContent).toMatch(
        /Loading/,
      );
    }
  } finally {
    finish('<a href="parts/new.csv">New file</a>');
    await replacement;
  }
  const current = container.querySelector("iframe")!;
  expect(current).not.toBe(old);
  const newId = new DOMParser()
    .parseFromString(current.srcdoc, "text/html")
    .querySelector("a")!
    .getAttribute("data-wright-file-link");
  window.dispatchEvent(
    new MessageEvent("message", {
      source: current.contentWindow,
      data: { type: "wright-open-workspace-file", id: newId },
    }),
  );
  expect(received.at(-1)).toEqual({
    type: "open-workspace-file",
    path: "/parts/new.csv",
    sessionId: "owned",
  });
});

it("shows a truthful failed reload instead of leaving dead old links or permanent loading", async () => {
  const read = vi
    .spyOn(workspaceService, "getFileContentText")
    .mockResolvedValue('<a href="parts/assembly.csv">Assembly</a>');
  const container = document.createElement("div");
  document.body.append(container);
  const host = new PanelHostImpl("failed", "Report", container);
  const provider = new IframeProvider();
  const model = await provider.openDocument(
    {
      id: "report.html",
      uri: "report.html",
      name: "report.html",
      extension: "html",
      mimeType: "text/html",
    },
    { sessionId: "owned" },
  );
  disposals.push(() => {
    host.dispose();
    provider.disposeDocument(model);
    container.remove();
  });
  await provider.resolveViewer(model, host, "preview", token);
  read.mockRejectedValueOnce(new Error("Controlled missing file"));
  await expect(
    provider.resolveViewer(model, host, "preview", token),
  ).rejects.toThrow("Controlled missing file");
  expect(container.querySelector("iframe")).toBeNull();
  expect(container.querySelector("[role=status]")).toBeNull();
  expect(container.querySelector("[role=alert]")?.textContent).toMatch(
    /Could not load/,
  );
});
