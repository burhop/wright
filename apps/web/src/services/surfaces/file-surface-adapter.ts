import type {
  CancellationToken,
  FileDescriptor,
  ViewerDocument,
  ViewerMode,
  ViewerProvider,
} from "../viewer-panel/types";
import {
  parseSurfaceDescriptor,
  type SurfaceDescriptor,
} from "./surface-contract";

interface ViewerSelector {
  getDefaultViewer(
    file: FileDescriptor,
    mode: ViewerMode,
  ):
    | {
        readonly id: string;
        providerFactory(): ViewerProvider;
      }
    | undefined;
}

export interface FileSurfaceOpenContext {
  readonly mode: ViewerMode;
  readonly sessionId: string;
  readonly workspaceId: string;
}

export class FileSurfaceUnsupportedError extends Error {}

const cancellationToken: CancellationToken = {
  isCancellationRequested: false,
  onCancellationRequested: () => ({ dispose: () => undefined }),
};

function normalizedFile(file: FileDescriptor): FileDescriptor {
  const value = file.uri.trim().replace(/\\/g, "/").replace(/\/+/g, "/");
  const uri = value.startsWith("/") ? value : `/${value}`;
  return { ...file, id: uri, uri };
}

export interface FileSurfaceHost {
  readonly descriptor: SurfaceDescriptor;
  readonly provider: ViewerProvider;
  readonly document: ViewerDocument;
  save(): Promise<void>;
  revert(): Promise<void>;
  dispose(): void;
}

export class FileSurfaceAdapter {
  private readonly registry: ViewerSelector;
  private readonly clock: () => Date;

  constructor(registry: ViewerSelector, clock: () => Date = () => new Date()) {
    this.registry = registry;
    this.clock = clock;
  }

  async open(
    input: FileDescriptor,
    context: FileSurfaceOpenContext,
  ): Promise<FileSurfaceHost> {
    const file = normalizedFile(input);
    const contribution = this.registry.getDefaultViewer(file, context.mode);
    if (!contribution) {
      throw new FileSurfaceUnsupportedError(
        `No viewer supports ${file.name || file.uri}`,
      );
    }
    const provider = contribution.providerFactory();
    const document = await provider.openDocument(file, {
      sessionId: context.sessionId,
    });
    const subscription = provider.onDidChangeDocument(() => undefined);
    const revision =
      typeof file.metadata?.last_modified === "number" &&
      file.metadata.last_modified >= 1
        ? Math.floor(file.metadata.last_modified)
        : 1;
    const timestamp = this.clock().toISOString();
    const path = file.uri.replace(/^\/+/, "");
    const descriptor = parseSurfaceDescriptor({
      schemaVersion: 1,
      surfaceId: `file:${encodeURIComponent(path)}`,
      workspaceId: context.workspaceId,
      source: {
        kind: "file",
        sourceId: path,
        sourceVersion: String(revision),
        path,
        mediaType: file.mimeType,
      },
      title: file.name || path,
      lifecycle: "ready",
      presentations: [],
      capabilities: [],
      revision,
      createdAt: timestamp,
      updatedAt: timestamp,
    });
    let disposed = false;
    return {
      descriptor,
      provider,
      document,
      save: () => provider.save(document, cancellationToken),
      revert: () => provider.revert(document, cancellationToken),
      dispose: () => {
        if (disposed) return;
        disposed = true;
        subscription.dispose();
        provider.disposeDocument(document);
      },
    };
  }
}
