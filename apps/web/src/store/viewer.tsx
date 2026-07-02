import React, { createContext, useContext, useState, useCallback } from "react";
import { viewerRegistry } from "../services/viewer-panel";
import type {
  FileDescriptor,
  ViewerMode,
  ViewerDocument,
  ViewerProvider,
  ViewerEdit,
  Disposable,
  ViewerDocumentChangeEvent,
  BackupHandle,
} from "../services/viewer-panel";
import { useChat } from "./sessions";

export interface EditorTab {
  name: string;
  path: string;
  type: string; // "code" | "stl" | "pdf" | etc.
  isDirty?: boolean;
  last_modified?: number;
}

export const normalizeEditorTabPath = (path: string): string => {
  const normalized = path.trim().replace(/\\/g, "/").replace(/\/+/g, "/");
  return normalized.startsWith("/") ? normalized : `/${normalized}`;
};

export const dedupeEditorTabs = (tabs: EditorTab[]): EditorTab[] => {
  const byPath = new Map<string, EditorTab>();

  for (const tab of tabs) {
    const path = normalizeEditorTabPath(tab.path);
    const previous = byPath.get(path);
    const name = tab.name || path.split("/").pop() || path;

    byPath.set(path, {
      ...previous,
      ...tab,
      path,
      name,
      isDirty: Boolean(previous?.isDirty || tab.isDirty),
      last_modified:
        previous?.last_modified && tab.last_modified
          ? Math.max(previous.last_modified, tab.last_modified)
          : (tab.last_modified ?? previous?.last_modified),
    });
  }

  return Array.from(byPath.values());
};

interface ViewerPanelContextType {
  openTabs: EditorTab[];
  activeTabPath: string | null;
  openTab: (file: FileDescriptor, mode?: ViewerMode) => Promise<void>;
  closeTab: (path: string) => void;
  setActiveTabPath: (path: string | null) => void;
  setTabDirty: (path: string, isDirty: boolean) => void;
  getDocument: (path: string) => ViewerDocument | undefined;
  getProvider: (path: string) => ViewerProvider | undefined;
  updateTabPath: (oldPath: string, newPath: string, newName: string) => void;
  updateTabLastModified: (path: string, lastModified: number) => void;
  reloadDocument: (file: FileDescriptor) => Promise<void>;
  undo: (path: string) => Promise<void>;
  redo: (path: string) => Promise<void>;
  canUndo: (path: string) => boolean;
  canRedo: (path: string) => boolean;
  saveDocument: (path: string) => Promise<void>;
  revertDocument: (path: string) => Promise<void>;
  resetViewer: () => void;
}

const ViewerPanelContext = createContext<ViewerPanelContextType | null>(null);

export const useViewerPanel = () => {
  const ctx = useContext(ViewerPanelContext);
  if (!ctx) {
    throw new Error("useViewerPanel must be used within ViewerPanelProvider");
  }
  return ctx;
};

const createDummyCancellationToken = () => ({
  isCancellationRequested: false,
  onCancellationRequested: () => ({ dispose: () => {} }),
});

export const ViewerPanelProvider: React.FC<{ children: React.ReactNode }> = ({
  children,
}) => {
  const { state: chatState } = useChat();
  const [openTabs, setOpenTabs] = useState<EditorTab[]>([]);
  const [activeTabPath, setActiveTabPath] = useState<string | null>(null);
  const [documents, setDocuments] = useState<Map<string, ViewerDocument>>(
    new Map(),
  );
  const [providers, setProviders] = useState<Map<string, ViewerProvider>>(
    new Map(),
  );
  const [undoStacks, setUndoStacks] = useState<Map<string, ViewerEdit[]>>(
    new Map(),
  );
  const [redoStacks, setRedoStacks] = useState<Map<string, ViewerEdit[]>>(
    new Map(),
  );

  const subscriptionsRef = React.useRef<Map<string, Disposable>>(new Map());
  const backupHandlesRef = React.useRef<Map<string, BackupHandle>>(new Map());

  const resetViewer = useCallback(() => {
    for (const sub of subscriptionsRef.current.values()) {
      try {
        sub.dispose();
      } catch (e) {
        console.error("Failed to dispose subscription on session switch:", e);
      }
    }
    subscriptionsRef.current.clear();

    for (const backupHandle of backupHandlesRef.current.values()) {
      try {
        backupHandle.delete().catch(() => {});
      } catch (e) {
        console.error("Failed to delete backup on session switch:", e);
      }
    }
    backupHandlesRef.current.clear();

    setDocuments((prev) => {
      for (const doc of prev.values()) {
        try {
          doc.dispose();
        } catch (e) {
          console.error("Failed to dispose document on session switch:", e);
        }
      }
      return new Map();
    });

    setProviders(new Map());
    setUndoStacks(new Map());
    setRedoStacks(new Map());
    setOpenTabs([]);
    setActiveTabPath(null);
  }, []);

  const activateTabPath = useCallback((path: string | null) => {
    setActiveTabPath(path ? normalizeEditorTabPath(path) : null);
  }, []);

  React.useEffect(() => {
    // Clear all open tabs and resource references when active session changes
    resetViewer();
  }, [chatState.activeSessionId, resetViewer]);

  const setTabDirty = useCallback((path: string, isDirty: boolean) => {
    const normalizedPath = normalizeEditorTabPath(path);
    setOpenTabs((prev) =>
      prev.map((t) => (t.path === normalizedPath ? { ...t, isDirty } : t)),
    );
  }, []);

  const openTab = useCallback(
    async (file: FileDescriptor, mode: ViewerMode = "preview") => {
      const normalizedUri = normalizeEditorTabPath(file.uri);
      const normalizedFile: FileDescriptor = {
        ...file,
        id: normalizedUri,
        uri: normalizedUri,
        name: file.name || normalizedUri.split("/").pop() || normalizedUri,
      };

      // 1. Check if tab is already open
      const existing = openTabs.find((t) => t.path === normalizedUri);
      if (existing) {
        activateTabPath(normalizedUri);
        return;
      }

      // 2. Resolve provider
      const contrib = viewerRegistry.getDefaultViewer(normalizedFile, mode);
      if (!contrib) {
        console.warn("No viewer provider registered for file", normalizedFile);
        return;
      }

      const provider = contrib.providerFactory();
      const doc = await provider.openDocument(normalizedFile, {
        sessionId: chatState.activeSessionId || undefined,
      });

      // Save document and provider refs
      setDocuments((prev) => {
        const next = new Map(prev);
        next.set(normalizedUri, doc);
        return next;
      });
      setProviders((prev) => {
        const next = new Map(prev);
        next.set(normalizedUri, provider);
        return next;
      });

      // Subscribe to change events
      const sub = provider.onDidChangeDocument(
        (event: ViewerDocumentChangeEvent) => {
          if (normalizeEditorTabPath(event.document.uri) !== normalizedUri) {
            return;
          }

          setTabDirty(normalizedUri, event.document.isDirty());

          if (event.document.isDirty()) {
            const cancelToken = createDummyCancellationToken();
            provider
              .backup(event.document, { destination: "" }, cancelToken)
              .then((handle) => {
                const oldHandle = backupHandlesRef.current.get(normalizedUri);
                if (oldHandle) {
                  oldHandle.delete().catch(() => {});
                }
                backupHandlesRef.current.set(normalizedUri, handle);
              })
              .catch((err) => console.error("Auto-backup failed:", err));
          }

          if (event.edit) {
            setUndoStacks((prev) => {
              const next = new Map(prev);
              const currentStack = next.get(normalizedUri) || [];
              next.set(normalizedUri, [...currentStack, event.edit!]);
              return next;
            });
            setRedoStacks((prev) => {
              const next = new Map(prev);
              next.delete(normalizedUri); // clear redo history on new edit
              return next;
            });
          }
        },
      );
      subscriptionsRef.current.set(normalizedUri, sub);

      const newTab: EditorTab = {
        name: normalizedFile.name,
        path: normalizedUri,
        type: normalizedFile.extension,
        isDirty: false,
        last_modified: normalizedFile.metadata?.last_modified as
          | number
          | undefined,
      };

      setOpenTabs((prev) => dedupeEditorTabs([...prev, newTab]));
      activateTabPath(normalizedUri);
    },
    [openTabs, chatState.activeSessionId, setTabDirty, activateTabPath],
  );

  const closeTab = useCallback(
    (path: string) => {
      const normalizedPath = normalizeEditorTabPath(path);
      setOpenTabs((prev) => {
        const remaining = prev.filter((t) => t.path !== normalizedPath);
        if (activeTabPath === normalizedPath) {
          setActiveTabPath(
            remaining.length > 0 ? remaining[remaining.length - 1].path : null,
          );
        }
        return remaining;
      });

      // Clean up subscription
      const sub = subscriptionsRef.current.get(normalizedPath);
      if (sub) {
        sub.dispose();
        subscriptionsRef.current.delete(normalizedPath);
      }

      // Clean up backup handle if exists
      const backupHandle = backupHandlesRef.current.get(normalizedPath);
      if (backupHandle) {
        backupHandle.delete().catch(() => {});
        backupHandlesRef.current.delete(normalizedPath);
      }

      // Clean up document reference
      setDocuments((prev) => {
        const next = new Map(prev);
        const doc = next.get(normalizedPath);
        if (doc) {
          doc.dispose();
          next.delete(normalizedPath);
        }
        return next;
      });
      setProviders((prev) => {
        const next = new Map(prev);
        next.delete(normalizedPath);
        return next;
      });
      setUndoStacks((prev) => {
        const next = new Map(prev);
        next.delete(normalizedPath);
        return next;
      });
      setRedoStacks((prev) => {
        const next = new Map(prev);
        next.delete(normalizedPath);
        return next;
      });
    },
    [activeTabPath],
  );

  const updateTabPath = useCallback(
    (oldPath: string, newPath: string, newName: string) => {
      const normalizedOldPath = normalizeEditorTabPath(oldPath);
      const normalizedNewPath = normalizeEditorTabPath(newPath);

      setOpenTabs((prev) =>
        dedupeEditorTabs(
          prev.map((t) =>
            t.path === normalizedOldPath
              ? { ...t, path: normalizedNewPath, name: newName }
              : t,
          ),
        ),
      );
      if (activeTabPath === normalizedOldPath) {
        activateTabPath(normalizedNewPath);
      }
      setDocuments((prev) => {
        const next = new Map(prev);
        const doc = next.get(normalizedOldPath);
        if (doc) {
          next.set(normalizedNewPath, doc);
          next.delete(normalizedOldPath);
        }
        return next;
      });
      setProviders((prev) => {
        const next = new Map(prev);
        const provider = next.get(normalizedOldPath);
        if (provider) {
          next.set(normalizedNewPath, provider);
          next.delete(normalizedOldPath);
        }
        return next;
      });
      // Move subscription and stacks
      const sub = subscriptionsRef.current.get(normalizedOldPath);
      if (sub) {
        subscriptionsRef.current.set(normalizedNewPath, sub);
        subscriptionsRef.current.delete(normalizedOldPath);
      }
      setUndoStacks((prev) => {
        const next = new Map(prev);
        const stack = next.get(normalizedOldPath);
        if (stack) {
          next.set(normalizedNewPath, stack);
          next.delete(normalizedOldPath);
        }
        return next;
      });
      setRedoStacks((prev) => {
        const next = new Map(prev);
        const stack = next.get(normalizedOldPath);
        if (stack) {
          next.set(normalizedNewPath, stack);
          next.delete(normalizedOldPath);
        }
        return next;
      });
    },
    [activeTabPath, activateTabPath],
  );

  const updateTabLastModified = useCallback(
    (path: string, lastModified: number) => {
      const normalizedPath = normalizeEditorTabPath(path);
      setOpenTabs((prev) =>
        prev.map((t) =>
          t.path === normalizedPath ? { ...t, last_modified: lastModified } : t,
        ),
      );
    },
    [],
  );

  const reloadDocument = useCallback(
    async (file: FileDescriptor) => {
      const normalizedUri = normalizeEditorTabPath(file.uri);
      const normalizedFile: FileDescriptor = {
        ...file,
        id: normalizedUri,
        uri: normalizedUri,
        name: file.name || normalizedUri.split("/").pop() || normalizedUri,
      };
      const mode = "preview";
      const contrib = viewerRegistry.getDefaultViewer(normalizedFile, mode);
      if (!contrib) return;
      const provider = contrib.providerFactory();
      const doc = await provider.openDocument(normalizedFile, {
        sessionId: chatState.activeSessionId || undefined,
      });
      setDocuments((prev) => {
        const next = new Map(prev);
        next.set(normalizedUri, doc);
        return next;
      });
      setOpenTabs((prev) =>
        prev.map((t) =>
          t.path === normalizedUri
            ? {
                ...t,
                last_modified: normalizedFile.metadata?.last_modified as
                  | number
                  | undefined,
              }
            : t,
        ),
      );
    },
    [chatState.activeSessionId],
  );

  const getDocument = useCallback(
    (path: string) => {
      return documents.get(normalizeEditorTabPath(path));
    },
    [documents],
  );

  const getProvider = useCallback(
    (path: string) => {
      return providers.get(normalizeEditorTabPath(path));
    },
    [providers],
  );

  const undo = useCallback(
    async (path: string) => {
      const normalizedPath = normalizeEditorTabPath(path);
      const uStack = undoStacks.get(normalizedPath) || [];
      if (uStack.length === 0) return;
      const rStack = redoStacks.get(normalizedPath) || [];

      const edit = uStack[uStack.length - 1];
      const newUStack = uStack.slice(0, -1);

      await edit.undo();

      const newRStack = [...rStack, edit];

      setUndoStacks((prev) => {
        const next = new Map(prev);
        next.set(normalizedPath, newUStack);
        return next;
      });
      setRedoStacks((prev) => {
        const next = new Map(prev);
        next.set(normalizedPath, newRStack);
        return next;
      });

      const doc = documents.get(normalizedPath);
      if (doc) {
        setTabDirty(normalizedPath, doc.isDirty());
      }
    },
    [undoStacks, redoStacks, documents, setTabDirty],
  );

  const redo = useCallback(
    async (path: string) => {
      const normalizedPath = normalizeEditorTabPath(path);
      const rStack = redoStacks.get(normalizedPath) || [];
      if (rStack.length === 0) return;
      const uStack = undoStacks.get(normalizedPath) || [];

      const edit = rStack[rStack.length - 1];
      const newRStack = rStack.slice(0, -1);

      await edit.redo();

      const newUStack = [...uStack, edit];

      setUndoStacks((prev) => {
        const next = new Map(prev);
        next.set(normalizedPath, newUStack);
        return next;
      });
      setRedoStacks((prev) => {
        const next = new Map(prev);
        next.set(normalizedPath, newRStack);
        return next;
      });

      const doc = documents.get(normalizedPath);
      if (doc) {
        setTabDirty(normalizedPath, doc.isDirty());
      }
    },
    [undoStacks, redoStacks, documents, setTabDirty],
  );

  const canUndo = useCallback(
    (path: string) => {
      return (undoStacks.get(normalizeEditorTabPath(path))?.length ?? 0) > 0;
    },
    [undoStacks],
  );

  const canRedo = useCallback(
    (path: string) => {
      return (redoStacks.get(normalizeEditorTabPath(path))?.length ?? 0) > 0;
    },
    [redoStacks],
  );

  const saveDocument = useCallback(
    async (path: string) => {
      const normalizedPath = normalizeEditorTabPath(path);
      const doc = documents.get(normalizedPath);
      const provider = providers.get(normalizedPath);
      if (!doc || !provider) return;

      const token = createDummyCancellationToken();
      await provider.save(doc, token);

      // Delete backup if exists
      const handle = backupHandlesRef.current.get(normalizedPath);
      if (handle) {
        await handle.delete().catch(() => {});
        backupHandlesRef.current.delete(normalizedPath);
      }

      setTabDirty(normalizedPath, false);
    },
    [documents, providers, setTabDirty],
  );

  const revertDocument = useCallback(
    async (path: string) => {
      const normalizedPath = normalizeEditorTabPath(path);
      const doc = documents.get(normalizedPath);
      const provider = providers.get(normalizedPath);
      if (!doc || !provider) return;

      const token = createDummyCancellationToken();
      await provider.revert(doc, token);

      // Delete backup if exists
      const handle = backupHandlesRef.current.get(normalizedPath);
      if (handle) {
        await handle.delete().catch(() => {});
        backupHandlesRef.current.delete(normalizedPath);
      }

      // Clear undo/redo stacks on revert
      setUndoStacks((prev) => {
        const next = new Map(prev);
        next.delete(normalizedPath);
        return next;
      });
      setRedoStacks((prev) => {
        const next = new Map(prev);
        next.delete(normalizedPath);
        return next;
      });

      setTabDirty(normalizedPath, false);
    },
    [documents, providers, setTabDirty],
  );

  return (
    <ViewerPanelContext.Provider
      value={{
        openTabs,
        activeTabPath,
        openTab,
        closeTab,
        setActiveTabPath: activateTabPath,
        setTabDirty,
        getDocument,
        getProvider,
        updateTabPath,
        updateTabLastModified,
        reloadDocument,
        undo,
        redo,
        canUndo,
        canRedo,
        saveDocument,
        revertDocument,
        resetViewer,
      }}
    >
      {children}
    </ViewerPanelContext.Provider>
  );
};
