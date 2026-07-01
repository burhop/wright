export interface FileDescriptor {
  readonly id: string;
  readonly uri: string;
  readonly name: string;
  readonly extension: string;
  readonly mimeType: string;
  readonly size?: number;
  readonly metadata?: Record<string, unknown>;
}

export type ViewerMode = "preview" | "edit" | "compare";

export interface ViewerCapabilities {
  readonly canEdit: boolean;
  readonly canAnnotate: boolean;
  readonly supports3DControls: boolean;
  readonly prefersIsolation: boolean;
  readonly supportsMultiView: boolean;
}

export interface ViewerDocument {
  readonly uri: string;
  readonly type: string;
  isDirty(): boolean;
  markClean(): void;
  dispose(): void;
}

export interface Disposable {
  dispose(): void;
}

export interface Event<T> {
  (listener: (e: T) => void): Disposable;
}

export interface PanelHost {
  readonly id: string;
  title: string;
  readonly container: HTMLElement;
  readonly active: boolean;
  readonly visible: boolean;

  readonly onDidChangeViewState: Event<{ active: boolean; visible: boolean }>;
  readonly onDidDispose: Event<void>;

  postMessage(message: unknown): void;
  readonly onDidReceiveMessage: Event<unknown>;
  readonly onDidBecomeUnresponsive?: Event<void>;
  readonly onDidBecomeResponsive?: Event<void>;
}

export interface OpenContext {
  readonly backupId?: string;
  readonly sessionId?: string;
}

export interface BackupContext {
  readonly destination: string;
}

export interface BackupHandle {
  readonly id: string;
  delete(): Promise<void>;
}

export interface CancellationToken {
  readonly isCancellationRequested: boolean;
  readonly onCancellationRequested: Event<void>;
}

export interface ViewerEdit {
  readonly label?: string;
  undo(): void | Promise<void>;
  redo(): void | Promise<void>;
}

export interface ViewerDocumentChangeEvent {
  readonly document: ViewerDocument;
  readonly edit?: ViewerEdit;
}

export interface ViewerProvider<
  TDocument extends ViewerDocument = ViewerDocument,
> {
  readonly id: string;

  openDocument(file: FileDescriptor, context: OpenContext): Promise<TDocument>;
  disposeDocument(doc: TDocument): void;

  resolveViewer(
    document: TDocument,
    panel: PanelHost,
    mode: ViewerMode,
    token: CancellationToken,
  ): Promise<void>;

  save(document: TDocument, token: CancellationToken): Promise<void>;
  saveAs(
    document: TDocument,
    destination: FileDescriptor,
    token: CancellationToken,
  ): Promise<void>;
  revert(document: TDocument, token: CancellationToken): Promise<void>;
  backup(
    document: TDocument,
    context: BackupContext,
    token: CancellationToken,
  ): Promise<BackupHandle>;

  readonly onDidChangeDocument: Event<ViewerDocumentChangeEvent>;
  getCapabilities(file: FileDescriptor, mode: ViewerMode): ViewerCapabilities;
}

export interface ViewerSelectorRule {
  readonly extension?: string;
  readonly mimeType?: string;
  readonly pattern?: string;
  readonly predicate?: (file: FileDescriptor, mode: ViewerMode) => boolean;
}

export interface ViewerContribution {
  readonly id: string;
  readonly label: string;
  readonly selector: ViewerSelectorRule[];
  readonly priority: "default" | "option";
  readonly providerFactory: () => ViewerProvider;
}
