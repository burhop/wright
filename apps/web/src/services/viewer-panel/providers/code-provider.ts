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

export interface CodeDocument extends ViewerDocument {
  content: string;
  initialContent: string;
  sessionId: string;
  setDirty(val: boolean): void;
}

class CodeDocumentImpl implements CodeDocument {
  readonly uri: string;
  readonly type = "code";
  public content: string;
  public initialContent: string;
  public sessionId: string;
  private dirty = false;

  constructor(uri: string, content: string, sessionId: string) {
    this.uri = uri;
    this.content = content;
    this.initialContent = content;
    this.sessionId = sessionId;
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

export class CodeProvider implements ViewerProvider<CodeDocument> {
  readonly id = "code-editor";
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
  ): Promise<CodeDocument> {
    const sessionId = context.sessionId;
    if (!sessionId) {
      throw new Error("No active session ID provided");
    }
    const text = await workspaceService.getFileContentText(
      sessionId,
      file.uri,
      context.backupId,
    );
    return new CodeDocumentImpl(file.uri, text, sessionId);
  }

  disposeDocument(doc: CodeDocument) {
    doc.dispose();
  }

  async resolveViewer(
    document: CodeDocument,
    panel: PanelHost,
    _mode: string,
    _token: CancellationToken,
  ): Promise<void> {
    const container = panel.container;
    container.innerHTML = "";

    const editorWrapper = window.document.createElement("div");
    editorWrapper.style.display = "flex";
    editorWrapper.style.flexDirection = "column";
    editorWrapper.style.height = "100%";
    editorWrapper.style.backgroundColor = "#1e1e1e";
    editorWrapper.style.color = "#d4d4d4";
    editorWrapper.style.fontFamily = "var(--font-code, monospace)";

    // Header / Toolbar
    const toolbar = window.document.createElement("div");
    toolbar.style.display = "flex";
    toolbar.style.justifyContent = "space-between";
    toolbar.style.alignItems = "center";
    toolbar.style.padding = "var(--space-xs, 4px) var(--space-md, 12px)";
    toolbar.style.backgroundColor = "#252526";
    toolbar.style.borderBottom = "1px solid var(--color-border, #2e2e2e)";
    toolbar.style.fontSize = "0.75rem";
    toolbar.style.color = "var(--color-secondary, #aaaaaa)";

    const pathLabel = window.document.createElement("span");
    pathLabel.textContent = document.uri;
    toolbar.appendChild(pathLabel);

    const controls = window.document.createElement("div");
    controls.style.display = "flex";
    controls.style.alignItems = "center";
    controls.style.gap = "var(--space-md, 12px)";

    const statusText = window.document.createElement("span");
    statusText.style.opacity = "0.6";
    statusText.textContent = document.isDirty() ? "Unsaved Changes" : "Saved";
    controls.appendChild(statusText);

    // Run Button (Only for Python files)
    const runButton = window.document.createElement("button");
    runButton.textContent = "Run";
    runButton.style.backgroundColor = "var(--color-success, #10b981)";
    runButton.style.color = "white";
    runButton.style.border = "none";
    runButton.style.borderRadius = "var(--radius-xs, 2px)";
    runButton.style.padding = "2px 8px";
    runButton.style.cursor = "pointer";
    runButton.style.fontWeight = "600";
    runButton.setAttribute("data-testid", "run-python-btn");
    const isPython = document.uri.toLowerCase().endsWith(".py");
    runButton.style.display = isPython ? "inline-block" : "none";
    controls.appendChild(runButton);

    const saveButton = window.document.createElement("button");
    saveButton.textContent = "Save Changes";
    saveButton.style.backgroundColor = "var(--color-accent, #4f46e5)";
    saveButton.style.color = "white";
    saveButton.style.border = "none";
    saveButton.style.borderRadius = "var(--radius-xs, 2px)";
    saveButton.style.padding = "2px 8px";
    saveButton.style.cursor = "pointer";
    saveButton.style.fontWeight = "600";
    saveButton.style.display = document.isDirty() ? "inline-block" : "none";
    controls.appendChild(saveButton);

    toolbar.appendChild(controls);
    editorWrapper.appendChild(toolbar);

    // Body container
    const body = window.document.createElement("div");
    body.style.flex = "1";
    body.style.display = "flex";
    body.style.overflow = "hidden";
    body.style.padding = "var(--space-sm, 8px) 0";

    // Gutter
    const gutter = window.document.createElement("pre");
    gutter.style.margin = "0";
    gutter.style.padding = "0 var(--space-sm, 8px)";
    gutter.style.width = "40px";
    gutter.style.textAlign = "right";
    gutter.style.color = "#858585";
    gutter.style.fontSize = "0.85rem";
    gutter.style.lineHeight = "1.5";
    gutter.style.borderRight = "1px solid #3c3c3c";
    gutter.style.userSelect = "none";
    gutter.style.overflow = "hidden";
    body.appendChild(gutter);

    // Text Area Wrapper
    const textWrapper = window.document.createElement("div");
    textWrapper.style.position = "relative";
    textWrapper.style.flex = "1";
    textWrapper.style.height = "100%";
    textWrapper.style.overflow = "hidden";

    // Highlight Overlay Pre
    const pre = window.document.createElement("pre");
    pre.style.margin = "0";
    pre.style.padding = "0 var(--space-md, 12px)";
    pre.style.position = "absolute";
    pre.style.top = "0";
    pre.style.left = "0";
    pre.style.right = "0";
    pre.style.bottom = "0";
    pre.style.background = "transparent";
    pre.style.color = "#d4d4d4";
    pre.style.fontFamily = "var(--font-code, monospace)";
    pre.style.fontSize = "0.85rem";
    pre.style.lineHeight = "1.5";
    pre.style.pointerEvents = "none";
    pre.style.whiteSpace = "pre";
    pre.style.overflow = "hidden";
    pre.style.boxSizing = "border-box";
    pre.setAttribute("data-testid", "code-editor-highlight-overlay");

    // Text Area
    const textarea = window.document.createElement("textarea");
    textarea.value = document.content;
    textarea.style.position = "absolute";
    textarea.style.top = "0";
    textarea.style.left = "0";
    textarea.style.right = "0";
    textarea.style.bottom = "0";
    textarea.style.margin = "0";
    textarea.style.padding = "0 var(--space-md, 12px)";
    textarea.style.backgroundColor = "transparent";
    textarea.style.color = "transparent"; // transparent text to see overlay behind it
    textarea.style.fontFamily = "var(--font-code, monospace)";
    textarea.style.caretColor = "#ffffff";
    textarea.style.border = "none";
    textarea.style.outline = "none";
    textarea.style.fontSize = "0.85rem";
    textarea.style.lineHeight = "1.5";
    textarea.style.resize = "none";
    textarea.style.whiteSpace = "pre";
    textarea.style.overflow = "auto";
    textarea.style.width = "100%";
    textarea.style.height = "100%";
    textarea.style.boxSizing = "border-box";
    textarea.setAttribute("data-testid", "code-editor-textarea");

    textWrapper.appendChild(pre);
    textWrapper.appendChild(textarea);
    body.appendChild(textWrapper);
    editorWrapper.appendChild(body);

    // Console output panel
    const consoleOutput = window.document.createElement("div");
    consoleOutput.style.display = "none";
    consoleOutput.style.height = "120px";
    consoleOutput.style.backgroundColor = "#151515";
    consoleOutput.style.borderTop = "1px solid var(--color-border, #2e2e2e)";
    consoleOutput.style.color = "#d4d4d4";
    consoleOutput.style.fontFamily = "var(--font-code, monospace)";
    consoleOutput.style.fontSize = "0.75rem";
    consoleOutput.style.flexDirection = "column";
    consoleOutput.style.boxSizing = "border-box";
    consoleOutput.setAttribute("data-testid", "code-editor-console");

    const consoleHeader = window.document.createElement("div");
    consoleHeader.style.display = "flex";
    consoleHeader.style.justifyContent = "space-between";
    consoleHeader.style.alignItems = "center";
    consoleHeader.style.padding = "4px 12px";
    consoleHeader.style.backgroundColor = "#1c1c1c";
    consoleHeader.style.borderBottom = "1px solid var(--color-border, #2e2e2e)";
    consoleHeader.style.color = "var(--color-secondary, #aaaaaa)";
    consoleHeader.style.fontWeight = "600";
    consoleHeader.style.fontSize = "0.7rem";
    consoleHeader.style.textTransform = "uppercase";

    const titleSpan = window.document.createElement("span");
    titleSpan.textContent = "Execution Output";
    consoleHeader.appendChild(titleSpan);

    const headerActions = window.document.createElement("div");
    headerActions.style.display = "flex";
    headerActions.style.alignItems = "center";
    headerActions.style.gap = "8px";

    const fixBtn = window.document.createElement("button");
    fixBtn.textContent = "Fix with Agent";
    fixBtn.style.backgroundColor = "var(--color-accent, #4f46e5)";
    fixBtn.style.color = "white";
    fixBtn.style.border = "none";
    fixBtn.style.borderRadius = "2px";
    fixBtn.style.padding = "2px 6px";
    fixBtn.style.cursor = "pointer";
    fixBtn.style.fontSize = "0.65rem";
    fixBtn.style.display = "none";
    fixBtn.setAttribute("data-testid", "fix-error-btn");
    headerActions.appendChild(fixBtn);

    const closeConsoleBtn = window.document.createElement("button");
    closeConsoleBtn.textContent = "x";
    closeConsoleBtn.style.background = "none";
    closeConsoleBtn.style.border = "none";
    closeConsoleBtn.style.color = "inherit";
    closeConsoleBtn.style.cursor = "pointer";
    closeConsoleBtn.addEventListener("click", () => {
      consoleOutput.style.display = "none";
    });
    headerActions.appendChild(closeConsoleBtn);

    consoleHeader.appendChild(headerActions);
    consoleOutput.appendChild(consoleHeader);

    const consoleBody = window.document.createElement("pre");
    consoleBody.style.margin = "0";
    consoleBody.style.padding = "8px 12px";
    consoleBody.style.flex = "1";
    consoleBody.style.overflow = "auto";
    consoleBody.style.whiteSpace = "pre-wrap";
    consoleBody.style.wordBreak = "break-all";
    consoleBody.setAttribute("data-testid", "code-editor-console-body");
    consoleOutput.appendChild(consoleBody);

    editorWrapper.appendChild(consoleOutput);
    container.appendChild(editorWrapper);

    const highlightPython = (code: string): string => {
      const escapeHtml = (text: string) => {
        return text
          .replace(/&/g, "&amp;")
          .replace(/</g, "&lt;")
          .replace(/>/g, "&gt;");
      };

      if (!isPython) return escapeHtml(code);

      const tokenRegex =
        /(#[^\n]*)|(f?"""[\s\S]*?"""|r?"""[\s\S]*?"""|f?'''[\s\S]*?'''|r?'''[\s\S]*?'''|f?"[^"\\]*(?:\\.[^"\\]*)*"|r?"[^"\\]*(?:\\.[^"\\]*)*"|f?'[^'\\]*(?:\\.[^'\\]*)*'|r?'[^'\\]*(?:\\.[^'\\]*)*')|(\b(?:def|class|import|from|as|return|if|elif|else|try|except|finally|raise|assert|for|while|in|is|not|and|or|pass|break|continue|lambda|with|yield|global|nonlocal|True|False|None|print)\b)|(\b[a-zA-Z_]\w*(?=\())|(\b\d+(?:\.\d+)?\b)/g;

      let lastIndex = 0;
      let html = "";

      code.replace(
        tokenRegex,
        (match, comment, stringVal, keyword, funcName, numberVal, offset) => {
          if (offset > lastIndex) {
            html += escapeHtml(code.slice(lastIndex, offset));
          }

          const escapedMatch = escapeHtml(match);
          if (comment) {
            html += `<span style="color: #6a9955;">${escapedMatch}</span>`;
          } else if (stringVal) {
            html += `<span style="color: #ce9178;">${escapedMatch}</span>`;
          } else if (keyword) {
            html += `<span style="color: #569cd6; font-weight: 600;">${escapedMatch}</span>`;
          } else if (funcName) {
            html += `<span style="color: #dcdcaa;">${escapedMatch}</span>`;
          } else if (numberVal) {
            html += `<span style="color: #b5cea8;">${escapedMatch}</span>`;
          } else {
            html += escapedMatch;
          }

          lastIndex = offset + match.length;
          return match;
        },
      );

      if (lastIndex < code.length) {
        html += escapeHtml(code.slice(lastIndex));
      }

      return html;
    };

    const updateHighlighting = () => {
      pre.innerHTML = highlightPython(textarea.value);
    };

    const updateLineNumbers = () => {
      const lineCount = textarea.value.split("\n").length;
      gutter.textContent = Array.from(
        { length: Math.max(lineCount, 1) },
        (_, i) => i + 1,
      ).join("\n");
    };

    updateHighlighting();
    updateLineNumbers();

    textarea.addEventListener("scroll", () => {
      pre.scrollTop = textarea.scrollTop;
      pre.scrollLeft = textarea.scrollLeft;
    });

    const triggerSave = async () => {
      if (!document.isDirty()) return;
      saveButton.disabled = true;
      statusText.textContent = "Saving...";
      try {
        await this.save(document, {
          isCancellationRequested: false,
          onCancellationRequested: () => ({ dispose: () => {} }),
        });
        saveButton.style.display = "none";
        statusText.textContent = "Saved";
      } catch (err: any) {
        statusText.textContent = "Error saving";
        console.error(err);
      } finally {
        saveButton.disabled = false;
      }
    };

    const handleInput = () => {
      document.content = textarea.value;
      const wasDirty = document.isDirty();
      const isNowDirty = document.content !== document.initialContent;

      if (wasDirty !== isNowDirty) {
        document.setDirty(isNowDirty);
        saveButton.style.display = isNowDirty ? "inline-block" : "none";
        statusText.textContent = isNowDirty ? "Unsaved Changes" : "Saved";

        // Notify registry/listeners of document change
        for (const callback of this.changeCallbacks) {
          callback({
            document,
            edit: {
              undo: () => {
                textarea.value = document.initialContent;
                handleInput();
              },
              redo: () => {
                textarea.value = document.content;
                handleInput();
              },
            },
          });
        }
      }
      updateHighlighting();
      updateLineNumbers();
    };

    textarea.addEventListener("input", handleInput);
    saveButton.addEventListener("click", triggerSave);

    // Keyboard Save shortcut (Ctrl+S / Cmd+S)
    const handleKeyDown = (e: KeyboardEvent) => {
      if ((e.ctrlKey || e.metaKey) && e.key === "s") {
        e.preventDefault();
        triggerSave();
      }
    };
    textarea.addEventListener("keydown", handleKeyDown);

    const handleRunClick = async () => {
      consoleOutput.style.display = "flex";
      consoleBody.textContent = "Running script...\n";
      consoleBody.style.color = "#d4d4d4";
      runButton.disabled = true;

      try {
        const result = await workspaceService.runFile(
          document.sessionId,
          document.uri,
        );
        if (result.success) {
          consoleBody.style.color = "var(--color-success, #10b981)";
          consoleBody.textContent = `[Exit Code 0]\n\n${result.stdout || "(No output)"}`;
          fixBtn.style.display = "none";
        } else {
          consoleBody.style.color = "var(--color-error, #ef4444)";
          const errOutput = result.stderr || result.stdout || "(No output)";
          consoleBody.textContent = `[Exit Code ${result.exit_code}]\n\n${errOutput}`;
          fixBtn.style.display = "inline-block";
          fixBtn.onclick = () => {
            const fileName = document.uri.split("/").pop() || document.uri;
            const event = new CustomEvent("viewer-message", {
              detail: {
                type: "create-prompt",
                content: `When executing @${fileName} we got this output. Fix any problems: ${errOutput}`,
              },
              bubbles: true,
            });
            consoleHeader.dispatchEvent(event);
          };
        }
      } catch (err: any) {
        consoleBody.style.color = "var(--color-error, #ef4444)";
        const errMsg = err.message || err;
        consoleBody.textContent = `Execution failed:\n${errMsg}`;
        fixBtn.style.display = "inline-block";
        fixBtn.onclick = () => {
          const fileName = document.uri.split("/").pop() || document.uri;
          const event = new CustomEvent("viewer-message", {
            detail: {
              type: "create-prompt",
              content: `When executing @${fileName} we got this output. Fix any problems: ${errMsg}`,
            },
            bubbles: true,
          });
          consoleHeader.dispatchEvent(event);
        };
      } finally {
        runButton.disabled = false;
      }
    };
    runButton.addEventListener("click", handleRunClick);

    panel.onDidDispose(() => {
      textarea.removeEventListener("input", handleInput);
      saveButton.removeEventListener("click", triggerSave);
      textarea.removeEventListener("keydown", handleKeyDown);
      runButton.removeEventListener("click", handleRunClick);
    });
  }

  async save(document: CodeDocument, _token: CancellationToken): Promise<void> {
    await workspaceService.saveFileContent(
      document.sessionId,
      document.uri,
      document.content,
    );
    document.initialContent = document.content;
    document.markClean();

    // Trigger changes update
    for (const callback of this.changeCallbacks) {
      callback({ document });
    }
  }

  async saveAs(
    document: CodeDocument,
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
    document: CodeDocument,
    _token: CancellationToken,
  ): Promise<void> {
    document.content = document.initialContent;
    document.markClean();
    for (const callback of this.changeCallbacks) {
      callback({ document });
    }
  }

  async backup(
    document: CodeDocument,
    _context: BackupContext,
    _token: CancellationToken,
  ): Promise<BackupHandle> {
    const backupId = await workspaceService.backupFileContent(
      document.sessionId,
      document.uri,
      document.content,
    );
    return {
      id: backupId,
      delete: async () => {
        try {
          await workspaceService.deleteBackup(document.sessionId, backupId);
        } catch (err) {
          console.error("Failed to delete backup", err);
        }
      },
    };
  }

  getCapabilities(_file: FileDescriptor, _mode: string) {
    return {
      canEdit: true,
      canAnnotate: false,
      supports3DControls: false,
      prefersIsolation: false,
      supportsMultiView: false,
    };
  }
}

export default CodeProvider;
