import React from "react";
import { createRoot, type Root } from "react-dom/client";
import ReactMarkdown from "react-markdown";
import remarkGfm from "remark-gfm";
import type {
  BackupContext,
  BackupHandle,
  CancellationToken,
  Event,
  FileDescriptor,
  OpenContext,
  PanelHost,
  ViewerDocument,
  ViewerDocumentChangeEvent,
  ViewerMode,
  ViewerProvider,
} from "../types";
import { API_BASE, workspaceService } from "../../workspace-service";

export interface MarkdownDocument extends ViewerDocument {
  content: string;
  sessionId: string;
}

class MarkdownDocumentImpl implements MarkdownDocument {
  readonly uri: string;
  readonly type = "markdown";
  public content: string;
  public sessionId: string;

  constructor(uri: string, content: string, sessionId: string) {
    this.uri = uri;
    this.content = content;
    this.sessionId = sessionId;
  }

  isDirty() {
    return false;
  }

  markClean() {}

  dispose() {}
}

const isExternalUrl = (url: string) =>
  url.startsWith("http://") ||
  url.startsWith("https://") ||
  url.startsWith("mailto:") ||
  url.startsWith("tel:");

const isAnchorUrl = (url: string) => url.startsWith("#");

const isRelativeUrl = (url: string) =>
  !url.startsWith("//") && !/^[a-z][a-z0-9+.-]*:/i.test(url);

const isWorkspaceContentUrl = (url: string) =>
  url.startsWith("/api/workspace/files/content?") ||
  Boolean(
    API_BASE && url.startsWith(`${API_BASE}/api/workspace/files/content?`),
  );

const normalizeWorkspacePath = (path: string) =>
  path.startsWith("/") ? path : `/${path}`;

const resolveRelativePath = (documentUri: string, url: string) => {
  if (url.startsWith("/")) {
    return normalizeWorkspacePath(url);
  }

  const baseParts = documentUri.split("/");
  baseParts.pop();
  const parts = [...baseParts, ...url.split("/")];
  const resolved: string[] = [];

  for (const part of parts) {
    if (!part || part === ".") continue;
    if (part === "..") {
      resolved.pop();
      continue;
    }
    resolved.push(part);
  }

  return normalizeWorkspacePath(resolved.join("/"));
};

const workspaceContentUrl = (sessionId: string, path: string) =>
  `${API_BASE}/api/workspace/files/content?session_id=${encodeURIComponent(
    sessionId,
  )}&path=${encodeURIComponent(path)}`;

interface MarkdownPreviewProps {
  document: MarkdownDocument;
}

const MarkdownPreview: React.FC<MarkdownPreviewProps> = ({ document }) => {
  const transformUrl = (url: string, kind: "link" | "image") => {
    const trimmed = url.trim();
    if (!trimmed) return "#";
    if (
      isAnchorUrl(trimmed) ||
      isExternalUrl(trimmed) ||
      isWorkspaceContentUrl(trimmed)
    ) {
      return trimmed;
    }
    if (trimmed.startsWith("data:image/") && kind === "image") return trimmed;
    return workspaceContentUrl(
      document.sessionId,
      resolveRelativePath(document.uri, trimmed),
    );
  };

  return (
    <div className="markdown-viewer-shell" data-testid="markdown-viewer">
      <header className="markdown-viewer-header">
        <span className="markdown-viewer-path">{document.uri}</span>
      </header>
      <main className="markdown-viewer-scroll">
        <article className="markdown-viewer-content">
          <ReactMarkdown
            remarkPlugins={[remarkGfm]}
            urlTransform={(url) => {
              const trimmed = url.trim();
              if (
                isAnchorUrl(trimmed) ||
                isExternalUrl(trimmed) ||
                isRelativeUrl(trimmed) ||
                trimmed.startsWith("data:image/")
              ) {
                return trimmed;
              }
              return "#";
            }}
            components={{
              a: ({ href, children, ...props }) => {
                const safeHref = href ? transformUrl(href, "link") : "#";
                const isWorkspaceHref = safeHref.includes(
                  "/api/workspace/files/content?",
                );
                return (
                  <a
                    href={safeHref}
                    target={
                      isWorkspaceHref || isAnchorUrl(safeHref)
                        ? undefined
                        : "_blank"
                    }
                    rel={
                      isWorkspaceHref || isAnchorUrl(safeHref)
                        ? undefined
                        : "noopener noreferrer"
                    }
                    {...props}
                  >
                    {children}
                  </a>
                );
              },
              img: ({ src, alt, ...props }) => {
                const safeSrc = src ? transformUrl(src, "image") : "";
                return <img src={safeSrc} alt={alt || ""} {...props} />;
              },
            }}
          >
            {document.content}
          </ReactMarkdown>
        </article>
      </main>
    </div>
  );
};

export class MarkdownProvider implements ViewerProvider<MarkdownDocument> {
  readonly id = "markdown-viewer";
  private roots = new Map<string, Root>();

  readonly onDidChangeDocument: Event<ViewerDocumentChangeEvent> = () => ({
    dispose: () => {},
  });

  async openDocument(
    file: FileDescriptor,
    context: OpenContext,
  ): Promise<MarkdownDocument> {
    if (!context.sessionId) {
      throw new Error("No active session ID provided");
    }

    const text = await workspaceService.getFileContentText(
      context.sessionId,
      file.uri,
      context.backupId,
    );
    return new MarkdownDocumentImpl(file.uri, text, context.sessionId);
  }

  disposeDocument(doc: MarkdownDocument) {
    this.roots.get(doc.uri)?.unmount();
    this.roots.delete(doc.uri);
    doc.dispose();
  }

  async resolveViewer(
    document: MarkdownDocument,
    panel: PanelHost,
    _mode: ViewerMode,
    _token: CancellationToken,
  ): Promise<void> {
    this.roots.get(document.uri)?.unmount();
    this.roots.delete(document.uri);
    panel.container.innerHTML = "";

    const mount = window.document.createElement("div");
    mount.style.height = "100%";
    panel.container.appendChild(mount);

    const root = createRoot(mount);
    this.roots.set(document.uri, root);
    root.render(<MarkdownPreview document={document} />);

    panel.onDidDispose(() => {
      root.unmount();
      this.roots.delete(document.uri);
    });
  }

  async save(
    document: MarkdownDocument,
    _token: CancellationToken,
  ): Promise<void> {
    document.markClean();
  }

  async saveAs(
    document: MarkdownDocument,
    destination: FileDescriptor,
    _token: CancellationToken,
  ): Promise<void> {
    await workspaceService.saveFileContent(
      document.sessionId,
      destination.uri,
      document.content,
    );
  }

  async revert(
    document: MarkdownDocument,
    _token: CancellationToken,
  ): Promise<void> {
    document.markClean();
  }

  async backup(
    document: MarkdownDocument,
    _context: BackupContext,
    _token: CancellationToken,
  ): Promise<BackupHandle> {
    return {
      id: `markdown-readonly-${document.uri}`,
      delete: async () => {},
    };
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

export default MarkdownProvider;
