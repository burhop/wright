import type {
  FileDescriptor,
  ViewerProvider,
  ViewerDocument,
  PanelHost,
} from "../types";

export interface TextDocument extends ViewerDocument {
  content: string;
}

class TextDocumentImpl implements TextDocument {
  readonly uri: string;
  readonly type = "text";
  public content: string;
  private dirty = false;

  constructor(uri: string, content: string) {
    this.uri = uri;
    this.content = content;
  }

  isDirty() {
    return this.dirty;
  }
  markClean() {
    this.dirty = false;
  }
  dispose() {}
  setDirty(val: boolean) {
    this.dirty = val;
  }
}

export class TextProvider implements ViewerProvider<TextDocument> {
  readonly id = "text-viewer";

  private changeCallbacks = new Set<(e: any) => void>();

  async openDocument(file: FileDescriptor): Promise<TextDocument> {
    let text = "";
    try {
      const response = await fetch(
        `/api/workspace/files/content?path=${encodeURIComponent(file.uri)}`,
      );
      if (response.ok) {
        text = await response.text();
      }
    } catch {
      // fallback
    }
    return new TextDocumentImpl(file.uri, text);
  }

  disposeDocument(doc: TextDocument) {
    doc.dispose();
  }

  async resolveViewer(
    document: TextDocument,
    panel: PanelHost,
  ): Promise<void> {
    const pre = window.document.createElement("pre");
    pre.style.margin = "0";
    pre.style.padding = "var(--space-md)";
    pre.style.overflow = "auto";
    pre.style.height = "100%";
    pre.style.fontFamily = "var(--font-mono)";
    pre.style.fontSize = "0.8rem";
    pre.style.color = "var(--color-primary)";
    pre.textContent = document.content;

    panel.container.appendChild(pre);
  }

  async save(document: TextDocument): Promise<void> {
    document.markClean();
  }

  async saveAs(
    _document: TextDocument,
    _destination: FileDescriptor,
  ): Promise<void> {
    // save
  }

  async revert(document: TextDocument): Promise<void> {
    document.markClean();
  }

  async backup(document: TextDocument) {
    return {
      id: "backup-" + document.uri,
      delete: async () => {},
    };
  }

  readonly onDidChangeDocument = (listener: (e: any) => void) => {
    this.changeCallbacks.add(listener);
    return {
      dispose: () => {
        this.changeCallbacks.delete(listener);
      },
    };
  };

  getCapabilities() {
    return {
      canEdit: true,
      canAnnotate: false,
      supports3DControls: false,
      prefersIsolation: false,
      supportsMultiView: false,
    };
  }
}

export default TextProvider;
