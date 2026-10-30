import type {
  FileDescriptor,
  ViewerDocument,
  ViewerProvider,
  PanelHost,
  OpenContext,
} from "../types";
import { workspaceContentUrl } from "./workspace-content-url";

const FORMATS: Record<string, { label: string; application: string }> = {
  fcstd: { label: "FreeCAD document", application: "FreeCAD" },
  fcstd1: { label: "FreeCAD backup", application: "FreeCAD" },
  blend: { label: "Blender document", application: "Blender" },
  blend1: { label: "Blender backup", application: "Blender" },
  "3mf": { label: "3MF model or preparation package", application: "a compatible CAD application or slicer" },
  glb: { label: "Binary glTF model", application: "a compatible 3D application" },
  zip: { label: "ZIP archive", application: "an archive application" },
};

interface NativeFileDocument extends ViewerDocument {
  readonly file: FileDescriptor;
  readonly sessionId: string;
}

export class NativeFileProvider implements ViewerProvider<NativeFileDocument> {
  readonly id = "native-file-viewer";
  readonly onDidChangeDocument = () => ({ dispose() {} });

  async openDocument(
    file: FileDescriptor,
    context: OpenContext,
  ): Promise<NativeFileDocument> {
    if (!context.sessionId) {
      throw new Error("No workspace session was provided for this file.");
    }
    return {
      uri: file.uri,
      type: "native-file",
      file,
      sessionId: context.sessionId,
      isDirty: () => false,
      markClean() {},
      dispose() {},
    };
  }

  async resolveViewer(document: NativeFileDocument, panel: PanelHost) {
    const format = FORMATS[document.file.extension.toLowerCase()] ?? {
      label: "Native file",
      application: "its compatible engineering application",
    };
    const section = window.document.createElement("section");
    section.style.padding = "var(--space-lg, 24px)";
    section.style.color = "var(--color-primary)";
    section.setAttribute("aria-label", format.label);

    const title = window.document.createElement("h2");
    title.textContent = format.label;
    const filename = window.document.createElement("p");
    filename.textContent = document.file.name;
    const guidance = window.document.createElement("p");
    guidance.textContent = `Download this file and open it in ${format.application} to inspect its saved model or results.`;
    const download = window.document.createElement("a");
    download.href = workspaceContentUrl(document.uri, document.sessionId);
    download.download = document.file.name;
    download.textContent = "Download native file";
    download.className = "recovery-button recovery-button--primary";
    download.setAttribute("data-testid", "native-file-download");
    const reports = window.document.createElement("p");
    reports.textContent = "Open the workflow’s report or exported images for a readable view inside Wright.";
    section.append(title, filename, guidance, download, reports);
    panel.container.replaceChildren(section);
  }

  disposeDocument(document: NativeFileDocument) { document.dispose(); }
  async save() {}
  async saveAs() {}
  async revert() {}
  async backup(document: NativeFileDocument) {
    return { id: "native-file-" + document.uri, delete: async () => {} };
  }
  getCapabilities() {
    return {
      canEdit: false,
      canAnnotate: false,
      supports3DControls: false,
      prefersIsolation: false,
      supportsMultiView: false,
    };
  }
}
