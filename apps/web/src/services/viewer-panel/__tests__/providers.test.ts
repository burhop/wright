import { afterEach, describe, expect, it, vi } from "vitest";
import { workspaceService } from "../../workspace-service";

import { IframeProvider } from "../providers/iframe-provider";
import { PdfProvider } from "../providers/pdf-provider";
import { TextProvider } from "../providers/text-provider";
import type { CancellationToken, FileDescriptor, PanelHost } from "../types";

const token = {
  isCancellationRequested: false,
  onCancellationRequested: () => ({ dispose: () => {} }),
} as CancellationToken;

const panel = (): PanelHost =>
  ({
    id: "test-panel",
    title: "Test",
    container: document.createElement("div"),
    active: true,
    visible: true,
    onDidChangeViewState: () => ({ dispose: () => {} }),
    onDidDispose: () => ({ dispose: () => {} }),
    postMessage: () => {},
    onDidReceiveMessage: () => ({ dispose: () => {} }),
  }) as PanelHost;

const file = (
  uri: string,
  extension: string,
  mimeType: string,
): FileDescriptor => ({
  id: uri,
  uri,
  name: uri,
  extension,
  mimeType,
});

describe("workspace viewer providers", () => {
  afterEach(() => vi.restoreAllMocks());
  it("opens STEP text with its workspace session and surfaces read failures", async () => {
    const read = vi
      .spyOn(workspaceService, "getFileContentText")
      .mockResolvedValue("ISO-10303-21;");
    const provider = new TextProvider();
    const model = await provider.openDocument(
      file("/cad/bracket.step", "step", "application/step"),
      { sessionId: "cad-session" },
    );
    expect(read).toHaveBeenCalledWith("cad-session", "/cad/bracket.step");
    expect(model.content).toBe("ISO-10303-21;");
    read.mockRejectedValueOnce(new Error("File unavailable"));
    await expect(
      provider.openDocument(file("missing.step", "step", "application/step"), {
        sessionId: "cad-session",
      }),
    ).rejects.toThrow("File unavailable");
  });
  it("renders workspace HTML content inside the existing isolated iframe", async () => {
    const html = "<!doctype html><html><body><h1>Report</h1></body></html>";
    const read = vi
      .spyOn(workspaceService, "getFileContentText")
      .mockResolvedValue(html);
    const provider = new IframeProvider();
    const documentModel = await provider.openDocument(
      file("https://evil.test/file.html?x=/../#fragment", "html", "text/html"),
      { sessionId: "session&redirect=https://evil.test" },
    );
    const host = panel();

    await provider.resolveViewer(documentModel, host, "preview", token);

    const iframe = host.container.querySelector("iframe");
    expect(read).toHaveBeenCalledWith(
      documentModel.sessionId,
      documentModel.uri,
    );
    const rendered = new DOMParser().parseFromString(
      iframe?.srcdoc ?? "",
      "text/html",
    );
    expect(rendered.querySelector("h1")?.textContent).toBe("Report");
    expect(rendered.doctype?.name).toBe("html");
    expect(rendered.querySelector("base")?.getAttribute("href")).toBe(
      "about:srcdoc",
    );
    expect(iframe?.hasAttribute("src")).toBe(false);
    expect(iframe?.getAttribute("sandbox")).toContain("allow-scripts");
    expect(iframe?.getAttribute("sandbox")).not.toContain("allow-same-origin");
  });

  it("keeps report fragments local while preserving an authored external base", async () => {
    const read = vi.spyOn(workspaceService, "getFileContentText");
    const provider = new IframeProvider();
    const model = await provider.openDocument(
      file("report.html", "html", "text/html"),
      { sessionId: "session" },
    );
    for (const explicitBase of [
      "",
      '<base href="https://example.org/manual/">',
    ]) {
      read.mockResolvedValueOnce(
        `<!doctype html><html><head>${explicitBase}</head><body><a href="#source">Source</a><h2 id="source">Original quote</h2></body></html>`,
      );
      const host = panel();
      await provider.resolveViewer(model, host, "preview", token);
      const preview = new DOMParser().parseFromString(
        host.container.querySelector("iframe")!.srcdoc,
        "text/html",
      );
      expect(preview.querySelector("a")?.href).toBe(
        explicitBase
          ? "https://example.org/manual/#source"
          : "about:srcdoc#source",
      );
      expect(preview.querySelector("#source")?.textContent).toBe(
        "Original quote",
      );
      expect(preview.querySelectorAll("base")).toHaveLength(1);
    }
  });

  it("uses a root-relative same-origin PDF source", async () => {
    const provider = new PdfProvider();
    const documentModel = await provider.openDocument(
      file(
        "/docs/design.pdf?download=https://evil.test",
        "pdf",
        "application/pdf",
      ),
      { sessionId: "session#evil" },
    );
    const host = panel();

    await provider.resolveViewer(documentModel, host, "preview", token);

    const src =
      host.container.querySelector("iframe")?.getAttribute("src") ?? "";
    const parsed = new URL(src, "http://wright.local");
    expect(src).toMatch(/^\/api\/workspace\/files\/content\?/);
    expect(parsed.origin).toBe("http://wright.local");
    expect(parsed.pathname).toBe("/api/workspace/files/content");
    expect(parsed.searchParams.get("path")).toBe(documentModel.uri);
    expect(parsed.searchParams.get("session_id")).toBe("session#evil");
  });
});
