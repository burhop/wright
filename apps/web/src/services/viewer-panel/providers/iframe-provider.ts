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
import { workspaceService } from "../../workspace-service";
import { bindWorkspaceHtmlLinks } from "./workspace-html-links";

export interface IframeDocument extends ViewerDocument {
  sessionId: string;
}

class IframeDocumentImpl implements IframeDocument {
  readonly uri: string;
  readonly type = "iframe";
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

export class IframeProvider implements ViewerProvider<IframeDocument> {
  readonly id = "iframe-viewer";
  private bindings = new Map<PanelHost, {document: IframeDocument; dispose: () => void}>();
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
  ): Promise<IframeDocument> {
    const sessionId = context.sessionId;
    if (!sessionId) {
      throw new Error("No active session ID provided");
    }
    return new IframeDocumentImpl(file.uri, sessionId);
  }

  disposeDocument(doc: IframeDocument) {
    for (const binding of this.bindings.values()) if (binding.document === doc) binding.dispose();
    doc.dispose();
  }

  async resolveViewer(
    document: IframeDocument,
    panel: PanelHost,
    _mode: string,
    _token: CancellationToken,
  ): Promise<void> {
    this.bindings.get(panel)?.dispose();
    const container = panel.container;
    // Once the old binding is gone, do not leave its inert links visible while
    // waiting for replacement content. Keep the pending state explicit.
    const loading = window.document.createElement("p");
    loading.setAttribute("role", "status");
    loading.textContent = "Loading HTML preview…";
    container.replaceChildren(loading);
    let active = true;
    let removeLinks = () => {};
    const dispose = () => {
      if (!active) return;
      active = false;
      removeLinks();
      disposed.dispose();
      cancelled.dispose();
      if (this.bindings.get(panel)?.dispose === dispose) this.bindings.delete(panel);
    };
    let disposed = {dispose: () => {}};
    let cancelled = {dispose: () => {}};
    disposed = panel.onDidDispose(dispose);
    cancelled = _token.onCancellationRequested(dispose);
    this.bindings.set(panel, {document, dispose});
    let html: string;
    try { html = await workspaceService.getFileContentText(document.sessionId, document.uri); }
    catch (error) {
      if (active && !_token.isCancellationRequested) {
        loading.setAttribute("role", "alert");
        loading.textContent = "Could not load HTML preview. Reopen the file to try again.";
      }
      dispose();
      throw error;
    }
    if (!active || _token.isCancellationRequested) { dispose(); return; }
    container.innerHTML = "";

    const iframe = window.document.createElement("iframe");
    // Sandbox attribute to prevent access to parent document and cookies
    iframe.setAttribute("sandbox", "allow-scripts");

    // Text files arrive in a JSON envelope. Render their content while retaining
    // the existing isolated iframe, rather than navigating to that envelope.
    const preview = new DOMParser().parseFromString(html, "text/html");
    // srcdoc otherwise inherits the workspace page's base URL. A local #anchor
    // would navigate the frame to Wright instead of scrolling within the report.
    // Preserve an explicit base supplied by the document author.
    if (!preview.querySelector("base[href]")) {
      const base = preview.createElement("base");
      base.href = "about:srcdoc";
      preview.head.prepend(base);
    }
    removeLinks = bindWorkspaceHtmlLinks(preview, document.uri, document.sessionId, panel);
    const doctype = preview.doctype
      ? new XMLSerializer().serializeToString(preview.doctype)
      : "";
    iframe.srcdoc = doctype + preview.documentElement.outerHTML;
    iframe.title = document.uri.split("/").at(-1) ?? "HTML preview";
    iframe.style.width = "100%";
    iframe.style.height = "100%";
    iframe.style.border = "none";
    iframe.style.backgroundColor = "white";
    iframe.setAttribute("data-testid", "iframe-sandbox");

    container.appendChild(iframe);
  }

  async save(
    _document: IframeDocument,
    _token: CancellationToken,
  ): Promise<void> {}

  async saveAs(
    _document: IframeDocument,
    _destination: FileDescriptor,
    _token: CancellationToken,
  ): Promise<void> {}

  async revert(
    _document: IframeDocument,
    _token: CancellationToken,
  ): Promise<void> {}

  async backup(
    document: IframeDocument,
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
      // Workspace HTML is a document and need not implement a host protocol.
      supportsHeartbeat: false,
    };
  }
}

export default IframeProvider;
