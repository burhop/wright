import { describe, expect, it } from "vitest";

import { IframeProvider } from "../providers/iframe-provider";
import { PdfProvider } from "../providers/pdf-provider";
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
  it("uses a root-relative same-origin sandboxed HTML source", async () => {
    const provider = new IframeProvider();
    const documentModel = await provider.openDocument(
      file("https://evil.test/file.html?x=/../#fragment", "html", "text/html"),
      { sessionId: "session&redirect=https://evil.test" },
    );
    const host = panel();

    await provider.resolveViewer(documentModel, host, "preview", token);

    const iframe = host.container.querySelector("iframe");
    const src = iframe?.getAttribute("src") ?? "";
    expect(src).toMatch(/^\/api\/workspace\/files\/content\?/);
    expect(new URL(src, "http://wright.local").origin).toBe(
      "http://wright.local",
    );
    expect(new URL(src, "http://wright.local").pathname).toBe(
      "/api/workspace/files/content",
    );
    expect(new URL(src, "http://wright.local").searchParams.get("path")).toBe(
      documentModel.uri,
    );
    expect(iframe?.getAttribute("sandbox")).toContain("allow-scripts");
    expect(iframe?.getAttribute("sandbox")).not.toContain("allow-same-origin");
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
