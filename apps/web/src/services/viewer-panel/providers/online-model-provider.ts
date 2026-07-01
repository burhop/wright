import type { EmbeddedViewer } from "online-3d-viewer";
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
import {
  workspaceService,
  type WorkspaceNode,
} from "../../workspace-service";

const MODEL_EXTENSIONS = new Set([
  "3dm",
  "3ds",
  "3mf",
  "amf",
  "bim",
  "brep",
  "dae",
  "fbx",
  "fcstd",
  "glb",
  "gltf",
  "ifc",
  "iges",
  "igs",
  "obj",
  "off",
  "ply",
  "step",
  "stp",
  "wrl",
]);

const COMPANION_EXTENSIONS = new Set([
  ...MODEL_EXTENSIONS,
  "bin",
  "mtl",
  "jpg",
  "jpeg",
  "png",
  "webp",
  "bmp",
  "gif",
  "tga",
  "ktx",
  "ktx2",
]);

const VIEWER_BACKGROUND = [9, 13, 22, 255] as const;
const DEFAULT_MODEL_COLOR = [217, 243, 255] as const;
const DEFAULT_LINE_COLOR = [125, 211, 252] as const;
const EDGE_COLOR = [56, 189, 248] as const;

export interface OnlineModelDocument extends ViewerDocument {
  readonly files: File[];
}

class OnlineModelDocumentImpl implements OnlineModelDocument {
  readonly uri: string;
  readonly type = "online-model";
  readonly files: File[];

  constructor(uri: string, files: File[]) {
    this.uri = uri;
    this.files = files;
  }

  isDirty() {
    return false;
  }

  markClean() {}

  dispose() {}
}

const basename = (path: string) => path.split(/[\\/]/).pop() || path;

const dirname = (path: string) => {
  const normalized = path.replace(/\\/g, "/");
  const index = normalized.lastIndexOf("/");
  return index <= 0 ? "/" : normalized.slice(0, index);
};

const extensionOf = (path: string) =>
  (path.split(".").pop() || "").toLowerCase();

const joinPath = (dir: string, name: string) =>
  dir === "/" ? `/${name}` : `${dir}/${name}`;

const findDirectory = (
  node: WorkspaceNode,
  targetDir: string,
): WorkspaceNode | null => {
  if (node.type !== "directory") {
    return null;
  }
  if (node.path.replace(/\\/g, "/") === targetDir) {
    return node;
  }
  for (const child of node.children || []) {
    const found = findDirectory(child, targetDir);
    if (found) {
      return found;
    }
  }
  return null;
};

const makeWorkspaceFile = (
  name: string,
  buffer: ArrayBuffer,
  mimeType = "application/octet-stream",
) => new File([buffer.slice(0)], name, { type: mimeType });

const modelMimeType = (extension: string) => {
  switch (extension) {
    case "gltf":
      return "model/gltf+json";
    case "glb":
      return "model/gltf-binary";
    case "obj":
      return "model/obj";
    case "stp":
    case "step":
      return "model/step";
    case "igs":
    case "iges":
      return "model/iges";
    case "3mf":
      return "model/3mf";
    case "ply":
      return "model/ply";
    default:
      return "application/octet-stream";
  }
};

export class OnlineModelProvider
  implements ViewerProvider<OnlineModelDocument>
{
  readonly id = "online-model-viewer";
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
  ): Promise<OnlineModelDocument> {
    const sessionId = context.sessionId;
    if (!sessionId) {
      throw new Error("No active session ID provided");
    }

    const files: File[] = [];
    const primaryBuffer = await workspaceService.getFileContentArrayBuffer(
      sessionId,
      file.uri,
      context.backupId,
    );
    files.push(
      makeWorkspaceFile(
        file.name || basename(file.uri),
        primaryBuffer,
        modelMimeType(file.extension),
      ),
    );

    if (!context.backupId) {
      await this.addCompanionFiles(sessionId, file, files);
    }

    return new OnlineModelDocumentImpl(file.uri, files);
  }

  private async addCompanionFiles(
    sessionId: string,
    file: FileDescriptor,
    files: File[],
  ) {
    try {
      const workspace = await workspaceService.getWorkspaceFiles(sessionId);
      const folder = findDirectory(workspace, dirname(file.uri));
      if (!folder) {
        return;
      }

      const primaryName = basename(file.uri);
      const companionNodes = (folder.children || []).filter(
        (node) =>
          node.type === "file" &&
          node.name !== primaryName &&
          COMPANION_EXTENSIONS.has(extensionOf(node.name)),
      );

      for (const node of companionNodes) {
        const path = node.path || joinPath(dirname(file.uri), node.name);
        const buffer = await workspaceService.getFileContentArrayBuffer(
          sessionId,
          path,
        );
        files.push(
          makeWorkspaceFile(node.name, buffer, modelMimeType(extensionOf(node.name))),
        );
      }
    } catch (err) {
      console.warn("Failed to load Online3DViewer companion files", err);
    }
  }

  disposeDocument(doc: OnlineModelDocument) {
    doc.dispose();
  }

  async resolveViewer(
    document: OnlineModelDocument,
    panel: PanelHost,
    _mode: string,
    _token: CancellationToken,
  ): Promise<void> {
    const container = panel.container;
    container.innerHTML = "";

    const wrapper = window.document.createElement("div");
    wrapper.style.width = "100%";
    wrapper.style.height = "100%";
    wrapper.style.position = "relative";
    wrapper.style.backgroundColor = "#090d16";
    wrapper.setAttribute("data-testid", "online-model-viewer");

    const status = window.document.createElement("div");
    status.textContent = "Loading model...";
    status.style.position = "absolute";
    status.style.left = "12px";
    status.style.bottom = "12px";
    status.style.zIndex = "1";
    status.style.padding = "4px 8px";
    status.style.border = "1px solid var(--color-border, #1e293b)";
    status.style.borderRadius = "4px";
    status.style.backgroundColor = "rgba(9, 13, 22, 0.84)";
    status.style.color = "var(--color-secondary, #38bdf8)";
    status.style.font = "12px var(--font-ui, sans-serif)";
    status.style.pointerEvents = "none";
    wrapper.appendChild(status);

    container.appendChild(wrapper);

    const { EdgeSettings, EmbeddedViewer, RGBAColor, RGBColor } =
      await import("online-3d-viewer");

    let viewer: EmbeddedViewer | null = null;
    viewer = new EmbeddedViewer(wrapper, {
      backgroundColor: new RGBAColor(...VIEWER_BACKGROUND),
      defaultColor: new RGBColor(...DEFAULT_MODEL_COLOR),
      defaultLineColor: new RGBColor(...DEFAULT_LINE_COLOR),
      edgeSettings: new EdgeSettings(true, new RGBColor(...EDGE_COLOR), 25),
      onModelLoaded: () => {
        status.remove();
        viewer?.Resize();
      },
      onModelLoadFailed: () => {
        status.textContent = `Could not load ${basename(document.uri)}`;
        status.style.color = "var(--color-error, #ef4444)";
      },
    });
    viewer.LoadModelFromFileList(document.files);

    const resizeObserver = new ResizeObserver(() => viewer?.Resize());
    resizeObserver.observe(container);

    panel.onDidDispose(() => {
      resizeObserver.disconnect();
      viewer?.Destroy();
      viewer = null;
    });
  }

  async save(
    _document: OnlineModelDocument,
    _token: CancellationToken,
  ): Promise<void> {}

  async saveAs(
    _document: OnlineModelDocument,
    _destination: FileDescriptor,
    _token: CancellationToken,
  ): Promise<void> {}

  async revert(
    _document: OnlineModelDocument,
    _token: CancellationToken,
  ): Promise<void> {}

  async backup(
    document: OnlineModelDocument,
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
      supports3DControls: true,
      prefersIsolation: false,
      supportsMultiView: false,
    };
  }
}

export const isOnlineModelExtension = (extension: string) =>
  MODEL_EXTENSIONS.has(extension.toLowerCase());

export default OnlineModelProvider;
