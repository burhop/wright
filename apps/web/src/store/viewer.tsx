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

  React.useEffect(() => {
    // Clear all open tabs and resource references when active session changes
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
  }, [chatState.activeSessionId]);

  const setTabDirty = useCallback((path: string, isDirty: boolean) => {
    setOpenTabs((prev) =>
      prev.map((t) => (t.path === path ? { ...t, isDirty } : t)),
    );
  }, []);

  const openTab = useCallback(
    async (file: FileDescriptor, mode: ViewerMode = "preview") => {
      // 1. Check if tab is already open
      const existing = openTabs.find((t) => t.path === file.uri);
      if (existing) {
        setActiveTabPath(file.uri);
        return;
      }

      // 2. Resolve provider
      const contrib = viewerRegistry.getDefaultViewer(file, mode);
      if (!contrib) {
        console.warn("No viewer provider registered for file", file);
        return;
      }

      const provider = contrib.providerFactory();
      const doc = await provider.openDocument(file, {
        sessionId: chatState.activeSessionId || undefined,
      });

      // Save document and provider refs
      setDocuments((prev) => {
        const next = new Map(prev);
        next.set(file.uri, doc);
        return next;
      });
      setProviders((prev) => {
        const next = new Map(prev);
        next.set(file.uri, provider);
        return next;
      });

      // Subscribe to change events
      const sub = provider.onDidChangeDocument(
        (event: ViewerDocumentChangeEvent) => {
          if (event.document.uri !== file.uri) return;

          setTabDirty(file.uri, event.document.isDirty());

          if (event.document.isDirty()) {
            const cancelToken = createDummyCancellationToken();
            provider
              .backup(event.document, { destination: "" }, cancelToken)
              .then((handle) => {
                const oldHandle = backupHandlesRef.current.get(file.uri);
                if (oldHandle) {
                  oldHandle.delete().catch(() => {});
                }
                backupHandlesRef.current.set(file.uri, handle);
              })
              .catch((err) => console.error("Auto-backup failed:", err));
          }

          if (event.edit) {
            setUndoStacks((prev) => {
              const next = new Map(prev);
              const currentStack = next.get(file.uri) || [];
              next.set(file.uri, [...currentStack, event.edit!]);
              return next;
            });
            setRedoStacks((prev) => {
              const next = new Map(prev);
              next.delete(file.uri); // clear redo history on new edit
              return next;
            });
          }
        },
      );
      subscriptionsRef.current.set(file.uri, sub);

      const newTab: EditorTab = {
        name: file.name,
        path: file.uri,
        type: file.extension,
        isDirty: false,
        last_modified: file.metadata?.last_modified as number | undefined,
      };

      setOpenTabs((prev) => [...prev, newTab]);
      setActiveTabPath(file.uri);
    },
    [openTabs, chatState.activeSessionId, setTabDirty],
  );

  const closeTab = useCallback(
    (path: string) => {
      setOpenTabs((prev) => {
        const remaining = prev.filter((t) => t.path !== path);
        if (activeTabPath === path) {
          setActiveTabPath(
            remaining.length > 0 ? remaining[remaining.length - 1].path : null,
          );
        }
        return remaining;
      });

      // Clean up subscription
      const sub = subscriptionsRef.current.get(path);
      if (sub) {
        sub.dispose();
        subscriptionsRef.current.delete(path);
      }

      // Clean up backup handle if exists
      const backupHandle = backupHandlesRef.current.get(path);
      if (backupHandle) {
        backupHandle.delete().catch(() => {});
        backupHandlesRef.current.delete(path);
      }

      // Clean up document reference
      setDocuments((prev) => {
        const next = new Map(prev);
        const doc = next.get(path);
        if (doc) {
          doc.dispose();
          next.delete(path);
        }
        return next;
      });
      setProviders((prev) => {
        const next = new Map(prev);
        next.delete(path);
        return next;
      });
      setUndoStacks((prev) => {
        const next = new Map(prev);
        next.delete(path);
        return next;
      });
      setRedoStacks((prev) => {
        const next = new Map(prev);
        next.delete(path);
        return next;
      });
    },
    [activeTabPath],
  );

  const updateTabPath = useCallback(
    (oldPath: string, newPath: string, newName: string) => {
      setOpenTabs((prev) =>
        prev.map((t) =>
          t.path === oldPath ? { ...t, path: newPath, name: newName } : t,
        ),
      );
      if (activeTabPath === oldPath) {
        setActiveTabPath(newPath);
      }
      setDocuments((prev) => {
        const next = new Map(prev);
        const doc = next.get(oldPath);
        if (doc) {
          next.set(newPath, doc);
          next.delete(oldPath);
        }
        return next;
      });
      setProviders((prev) => {
        const next = new Map(prev);
        const provider = next.get(oldPath);
        if (provider) {
          next.set(newPath, provider);
          next.delete(oldPath);
        }
        return next;
      });
      // Move subscription and stacks
      const sub = subscriptionsRef.current.get(oldPath);
      if (sub) {
        subscriptionsRef.current.set(newPath, sub);
        subscriptionsRef.current.delete(oldPath);
      }
      setUndoStacks((prev) => {
        const next = new Map(prev);
        const stack = next.get(oldPath);
        if (stack) {
          next.set(newPath, stack);
          next.delete(oldPath);
        }
        return next;
      });
      setRedoStacks((prev) => {
        const next = new Map(prev);
        const stack = next.get(oldPath);
        if (stack) {
          next.set(newPath, stack);
          next.delete(oldPath);
        }
        return next;
      });
    },
    [activeTabPath],
  );

  const updateTabLastModified = useCallback(
    (path: string, lastModified: number) => {
      setOpenTabs((prev) =>
        prev.map((t) =>
          t.path === path ? { ...t, last_modified: lastModified } : t,
        ),
      );
    },
    [],
  );

  const reloadDocument = useCallback(
    async (file: FileDescriptor) => {
      const mode = "preview";
      const contrib = viewerRegistry.getDefaultViewer(file, mode);
      if (!contrib) return;
      const provider = contrib.providerFactory();
      const doc = await provider.openDocument(file, {
        sessionId: chatState.activeSessionId || undefined,
      });
      setDocuments((prev) => {
        const next = new Map(prev);
        next.set(file.uri, doc);
        return next;
      });
      setOpenTabs((prev) =>
        prev.map((t) =>
          t.path === file.uri
            ? {
                ...t,
                last_modified: file.metadata?.last_modified as
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
      return documents.get(path);
    },
    [documents],
  );

  const getProvider = useCallback(
    (path: string) => {
      return providers.get(path);
    },
    [providers],
  );

  const undo = useCallback(
    async (path: string) => {
      const uStack = undoStacks.get(path) || [];
      if (uStack.length === 0) return;
      const rStack = redoStacks.get(path) || [];

      const edit = uStack[uStack.length - 1];
      const newUStack = uStack.slice(0, -1);

      await edit.undo();

      const newRStack = [...rStack, edit];

      setUndoStacks((prev) => {
        const next = new Map(prev);
        next.set(path, newUStack);
        return next;
      });
      setRedoStacks((prev) => {
        const next = new Map(prev);
        next.set(path, newRStack);
        return next;
      });

      const doc = documents.get(path);
      if (doc) {
        setTabDirty(path, doc.isDirty());
      }
    },
    [undoStacks, redoStacks, documents, setTabDirty],
  );

  const redo = useCallback(
    async (path: string) => {
      const rStack = redoStacks.get(path) || [];
      if (rStack.length === 0) return;
      const uStack = undoStacks.get(path) || [];

      const edit = rStack[rStack.length - 1];
      const newRStack = rStack.slice(0, -1);

      await edit.redo();

      const newUStack = [...uStack, edit];

      setUndoStacks((prev) => {
        const next = new Map(prev);
        next.set(path, newUStack);
        return next;
      });
      setRedoStacks((prev) => {
        const next = new Map(prev);
        next.set(path, newRStack);
        return next;
      });

      const doc = documents.get(path);
      if (doc) {
        setTabDirty(path, doc.isDirty());
      }
    },
    [undoStacks, redoStacks, documents, setTabDirty],
  );

  const canUndo = useCallback(
    (path: string) => {
      return (undoStacks.get(path)?.length ?? 0) > 0;
    },
    [undoStacks],
  );

  const canRedo = useCallback(
    (path: string) => {
      return (redoStacks.get(path)?.length ?? 0) > 0;
    },
    [redoStacks],
  );

  const saveDocument = useCallback(
    async (path: string) => {
      const doc = documents.get(path);
      const provider = providers.get(path);
      if (!doc || !provider) return;

      const token = createDummyCancellationToken();
      await provider.save(doc, token);

      // Delete backup if exists
      const handle = backupHandlesRef.current.get(path);
      if (handle) {
        await handle.delete().catch(() => {});
        backupHandlesRef.current.delete(path);
      }

      setTabDirty(path, false);
    },
    [documents, providers, setTabDirty],
  );

  const revertDocument = useCallback(
    async (path: string) => {
      const doc = documents.get(path);
      const provider = providers.get(path);
      if (!doc || !provider) return;

      const token = createDummyCancellationToken();
      await provider.revert(doc, token);

      // Delete backup if exists
      const handle = backupHandlesRef.current.get(path);
      if (handle) {
        await handle.delete().catch(() => {});
        backupHandlesRef.current.delete(path);
      }

      // Clear undo/redo stacks on revert
      setUndoStacks((prev) => {
        const next = new Map(prev);
        next.delete(path);
        return next;
      });
      setRedoStacks((prev) => {
        const next = new Map(prev);
        next.delete(path);
        return next;
      });

      setTabDirty(path, false);
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
        setActiveTabPath,
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
      }}
    >
      {children}
    </ViewerPanelContext.Provider>
  );
};
