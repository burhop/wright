import type {
  FileDescriptor,
  ViewerProvider,
  ViewerDocument,
  PanelHost,
  OpenContext,
  CancellationToken,
  BackupContext,
  BackupHandle,
  ViewerDocumentChangeEvent,
  Event,
} from "../types";
import { API_BASE } from "../../workspace-service";

export interface PdfDocument extends ViewerDocument {
  sessionId: string;
}

class PdfDocumentImpl implements PdfDocument {
  readonly uri: string;
  readonly type = "pdf";
  public sessionId: string;

  constructor(uri: string, sessionId: string) {
    this.uri = uri;
    this.sessionId = sessionId;
  }

  isDirty() {
    return false;
  }

  markClean() {}

  dispose() {}
}

export class PdfProvider implements ViewerProvider<PdfDocument> {
  readonly id = "pdf-viewer";
  private changeCallbacks = new Set<(e: ViewerDocumentChangeEvent) => void>();

  readonly onDidChangeDocument: Event<ViewerDocumentChangeEvent> = (
    listener,
  ) => {
    this.changeCallbacks.add(listener);
    return {
      dispose: () => {
        this.changeCallbacks.delete(listener);
      },
    };
  };

  async openDocument(
    file: FileDescriptor,
    context: OpenContext,
  ): Promise<PdfDocument> {
    const sessionId = context.sessionId;
    if (!sessionId) {
      throw new Error("No active session ID provided");
    }
    return new PdfDocumentImpl(file.uri, sessionId);
  }

  disposeDocument(doc: PdfDocument) {
    doc.dispose();
  }

  async resolveViewer(
    document: PdfDocument,
    panel: PanelHost,
    _mode: string,
    _token: CancellationToken,
  ): Promise<void> {
    const container = panel.container;
    container.innerHTML = "";

    const iframe = window.document.createElement("iframe");
    const encodedPath = encodeURIComponent(document.uri);
    const encodedSessionId = encodeURIComponent(document.sessionId);

    // Set source pointing to file endpoint which returns PDF content
    iframe.src = `${API_BASE}/api/workspace/files/content?path=${encodedPath}&session_id=${encodedSessionId}`;
    iframe.style.width = "100%";
    iframe.style.height = "100%";
    iframe.style.border = "none";
    iframe.setAttribute("data-testid", "pdf-iframe");

    container.appendChild(iframe);
  }

  async save(
    _document: PdfDocument,
    _token: CancellationToken,
  ): Promise<void> {}

  async saveAs(
    _document: PdfDocument,
    _destination: FileDescriptor,
    _token: CancellationToken,
  ): Promise<void> {}

  async revert(
    _document: PdfDocument,
    _token: CancellationToken,
  ): Promise<void> {}

  async backup(
    document: PdfDocument,
    _context: BackupContext,
    _token: CancellationToken,
  ): Promise<BackupHandle> {
    return {
      id: "backup-" + document.uri,
      delete: async () => {},
    };
  }

  getCapabilities(_file: FileDescriptor, _mode: string) {
    return {
      canEdit: false,
      canAnnotate: false,
      supports3DControls: false,
      prefersIsolation: true,
      supportsMultiView: false,
    };
  }
}

export default PdfProvider;
