import { describe, it, expect, beforeEach } from "vitest";
import { ViewerRegistry } from "../registry";
import type { ViewerContribution, ViewerProvider } from "../types";

describe("ViewerRegistry", () => {
  let registry: ViewerRegistry;

  const dummyProviderFactory = (id: string): () => ViewerProvider => {
    return () => ({
      id,
      openDocument: async (file) => ({
        uri: file.uri,
        type: id,
        isDirty: () => false,
        markClean: () => {},
        dispose: () => {},
      }),
      disposeDocument: () => {},
      resolveViewer: async () => {},
      save: async () => {},
      saveAs: async () => {},
      revert: async () => {},
      backup: async () => ({ id: "mock-backup", delete: async () => {} }),
      onDidChangeDocument: () => ({ dispose: () => {} }),
      getCapabilities: () => ({
        canEdit: false,
        canAnnotate: false,
        supports3DControls: false,
        prefersIsolation: false,
        supportsMultiView: false,
      }),
    });
  };

  beforeEach(() => {
    // Get a fresh instance by clearing singleton or creating a new registry instance for tests
    registry = new ViewerRegistry();
  });

  it("should register and match by extension", () => {
    const contribution: ViewerContribution = {
      id: "threed",
      label: "3D Viewer",
      selector: [{ extension: "step" }],
      priority: "default",
      providerFactory: dummyProviderFactory("threed"),
    };

    registry.register(contribution);

    const file = {
      id: "1",
      uri: "/workspace/model.step",
      name: "model.step",
      extension: "step",
      mimeType: "application/step",
    };

    const viewers = registry.getViewersFor(file, "preview");
    expect(viewers.length).toBe(1);
    expect(viewers[0].id).toBe("threed");

    const defaultViewer = registry.getDefaultViewer(file, "preview");
    expect(defaultViewer?.id).toBe("threed");
  });

  it("should match by mimeType", () => {
    const contribution: ViewerContribution = {
      id: "pdf-viewer",
      label: "PDF Viewer",
      selector: [{ mimeType: "application/pdf" }],
      priority: "default",
      providerFactory: dummyProviderFactory("pdf-viewer"),
    };

    registry.register(contribution);

    const file = {
      id: "2",
      uri: "/workspace/doc.pdf",
      name: "doc.pdf",
      extension: "pdf",
      mimeType: "application/pdf",
    };

    const viewers = registry.getViewersFor(file, "preview");
    expect(viewers.length).toBe(1);
    expect(viewers[0].id).toBe("pdf-viewer");
  });

  it("should match by glob pattern", () => {
    const contribution: ViewerContribution = {
      id: "markdown",
      label: "Markdown Viewer",
      selector: [{ pattern: "**/doc/*.md" }],
      priority: "default",
      providerFactory: dummyProviderFactory("markdown"),
    };

    registry.register(contribution);

    const file = {
      id: "3",
      uri: "/workspace/doc/intro.md",
      name: "intro.md",
      extension: "md",
      mimeType: "text/markdown",
    };

    const viewers = registry.getViewersFor(file, "preview");
    expect(viewers.length).toBe(1);
    expect(viewers[0].id).toBe("markdown");

    // Non-matching file
    const file2 = {
      id: "4",
      uri: "/workspace/other/intro.md",
      name: "intro.md",
      extension: "md",
      mimeType: "text/markdown",
    };
    const viewers2 = registry.getViewersFor(file2, "preview");
    expect(viewers2.length).toBe(0);
  });

  it("should sort by priority", () => {
    const optionViewer: ViewerContribution = {
      id: "editor-option",
      label: "Alternative Editor",
      selector: [{ extension: "py" }],
      priority: "option",
      providerFactory: dummyProviderFactory("editor-option"),
    };

    const defaultViewer: ViewerContribution = {
      id: "editor-default",
      label: "Default Editor",
      selector: [{ extension: "py" }],
      priority: "default",
      providerFactory: dummyProviderFactory("editor-default"),
    };

    registry.register(optionViewer);
    registry.register(defaultViewer);

    const file = {
      id: "5",
      uri: "/workspace/script.py",
      name: "script.py",
      extension: "py",
      mimeType: "text/x-python",
    };

    const viewers = registry.getViewersFor(file, "edit");
    expect(viewers.length).toBe(2);
    expect(viewers[0].id).toBe("editor-default");
    expect(viewers[1].id).toBe("editor-option");
  });

  it("should support deregistration on dispose", () => {
    const contribution: ViewerContribution = {
      id: "temp",
      label: "Temp Viewer",
      selector: [{ extension: "tmp" }],
      priority: "default",
      providerFactory: dummyProviderFactory("temp"),
    };

    const handle = registry.register(contribution);

    const file = {
      id: "6",
      uri: "/workspace/file.tmp",
      name: "file.tmp",
      extension: "tmp",
      mimeType: "text/plain",
    };

    expect(registry.getViewersFor(file, "preview").length).toBe(1);

    handle.dispose();

    expect(registry.getViewersFor(file, "preview").length).toBe(0);
  });
});
