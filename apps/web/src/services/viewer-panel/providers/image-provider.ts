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

export interface ImageDocument extends ViewerDocument {
  sessionId: string;
}

class ImageDocumentImpl implements ImageDocument {
  readonly uri: string;
  readonly type = "image";
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

export class ImageProvider implements ViewerProvider<ImageDocument> {
  readonly id = "image-viewer";
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
  ): Promise<ImageDocument> {
    const sessionId = context.sessionId;
    if (!sessionId) {
      throw new Error("No active session ID provided");
    }
    return new ImageDocumentImpl(file.uri, sessionId);
  }

  disposeDocument(doc: ImageDocument) {
    doc.dispose();
  }

  async resolveViewer(
    document: ImageDocument,
    panel: PanelHost,
    _mode: string,
    _token: CancellationToken,
  ): Promise<void> {
    const container = panel.container;
    container.innerHTML = "";

    const wrapper = window.document.createElement("div");
    wrapper.style.display = "flex";
    wrapper.style.alignItems = "center";
    wrapper.style.justifyContent = "center";
    wrapper.style.height = "100%";
    wrapper.style.backgroundColor = "var(--color-neutral, #121212)";
    wrapper.style.overflow = "auto";
    wrapper.style.padding = "var(--space-md, 12px)";
    wrapper.style.boxSizing = "border-box";
    wrapper.style.flexDirection = "column";
    wrapper.style.gap = "var(--space-sm, 8px)";

    const status = window.document.createElement("p");
    status.setAttribute("role", "status");
    status.textContent = "Loading image…";
    status.style.color = "var(--color-secondary, #aaaaaa)";
    status.style.textAlign = "center";

    const retry = window.document.createElement("button");
    retry.type = "button";
    retry.textContent = "Retry image";
    retry.hidden = true;
    retry.style.padding = "var(--space-sm, 8px) var(--space-md, 12px)";
    retry.style.border = "1px solid var(--color-border, #444444)";
    retry.style.borderRadius = "var(--radius-sm, 4px)";
    retry.style.background = "var(--color-surface, #202020)";
    retry.style.color = "var(--color-primary, #ffffff)";
    retry.style.cursor = "pointer";

    const img = window.document.createElement("img");
    const encodedPath = encodeURIComponent(document.uri);
    const encodedSessionId = encodeURIComponent(document.sessionId);
    const imageUrl = `${API_BASE}/api/workspace/files/content?path=${encodedPath}&session_id=${encodedSessionId}`;
    img.alt = document.uri.split("/").pop() || "";
    img.style.maxWidth = "100%";
    img.style.maxHeight = "100%";
    img.style.objectFit = "contain";
    img.style.borderRadius = "var(--radius-sm, 4px)";
    img.style.boxShadow = "0 4px 12px rgba(0,0,0,0.15)";
    img.setAttribute("data-testid", "image-viewer-img");
    img.hidden = true;
    let disposed = false;
    img.onload = () => {
      if (disposed || _token.isCancellationRequested) return;
      img.hidden = false;
      status.hidden = true;
      retry.hidden = true;
    };
    img.onerror = () => {
      if (disposed || _token.isCancellationRequested) return;
      img.hidden = true;
      status.hidden = false;
      status.textContent = `Could not display ${img.alt}. Check its location in Files or reopen the result.`;
      retry.hidden = false;
    };
    retry.onclick = () => {
      if (disposed || _token.isCancellationRequested) return;
      status.textContent = "Loading image…";
      retry.hidden = true;
      img.src = `${imageUrl}&_refresh=${Date.now()}`;
    };
    panel.onDidDispose(() => {
      disposed = true;
      img.onload = null;
      img.onerror = null;
      retry.onclick = null;
    });
    img.src = imageUrl;

    wrapper.append(status, retry, img);
    container.appendChild(wrapper);
  }

  async save(
    _document: ImageDocument,
    _token: CancellationToken,
  ): Promise<void> {}

  async saveAs(
    _document: ImageDocument,
    _destination: FileDescriptor,
    _token: CancellationToken,
  ): Promise<void> {}

  async revert(
    _document: ImageDocument,
    _token: CancellationToken,
  ): Promise<void> {}

  async backup(
    document: ImageDocument,
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
      prefersIsolation: false,
      supportsMultiView: false,
    };
  }
}

export default ImageProvider;
