import type {
  FileDescriptor,
  ViewerMode,
  ViewerContribution,
  Disposable,
} from "./types";

import { TextProvider } from "./providers/text-provider";
import { ThreeDProvider } from "./providers/threed-provider";
import { CodeProvider } from "./providers/code-provider";
import { PdfProvider } from "./providers/pdf-provider";
import { IframeProvider } from "./providers/iframe-provider";
import { ImageProvider } from "./providers/image-provider";
import { MarkdownProvider } from "./providers/markdown-provider";

export class ViewerRegistry {
  private static instance: ViewerRegistry | null = null;
  private contributions: Map<string, ViewerContribution> = new Map();

  constructor() {
    // Keep empty constructor for unit testing isolation
  }

  public static getInstance(): ViewerRegistry {
    if (!ViewerRegistry.instance) {
      ViewerRegistry.instance = new ViewerRegistry();
    }
    return ViewerRegistry.instance;
  }

  public register(contribution: ViewerContribution): Disposable {
    this.contributions.set(contribution.id, contribution);
    return {
      dispose: () => {
        this.contributions.delete(contribution.id);
      },
    };
  }

  public getViewersFor(
    file: FileDescriptor,
    mode: ViewerMode,
  ): ViewerContribution[] {
    const list: ViewerContribution[] = [];
    for (const c of this.contributions.values()) {
      let matched = false;
      for (const rule of c.selector) {
        if (
          rule.extension &&
          file.extension.toLowerCase() ===
            rule.extension.toLowerCase().replace(/^\./, "")
        ) {
          matched = true;
          break;
        }
        if (
          rule.mimeType &&
          file.mimeType.toLowerCase() === rule.mimeType.toLowerCase()
        ) {
          matched = true;
          break;
        }
        if (rule.pattern) {
          // Glob pattern matcher (simple regex helper)
          const regexStr = rule.pattern
            .replace(/\./g, "\\.")
            .replace(/\*/g, ".*")
            .replace(/\?/g, ".");
          const regex = new RegExp(`^${regexStr}$`, "i");
          if (regex.test(file.uri)) {
            matched = true;
            break;
          }
        }
        if (rule.predicate && rule.predicate(file, mode)) {
          matched = true;
          break;
        }
      }
      if (matched) {
        list.push(c);
      }
    }

    // Sort by priority ("default" first, then "option")
    return list.sort((a, b) => {
      if (a.priority === "default" && b.priority !== "default") return -1;
      if (a.priority !== "default" && b.priority === "default") return 1;
      return 0;
    });
  }

  public getDefaultViewer(
    file: FileDescriptor,
    mode: ViewerMode,
  ): ViewerContribution | undefined {
    const matched = this.getViewersFor(file, mode);
    return matched.find((c) => c.priority === "default") || matched[0];
  }
}

export const viewerRegistry = ViewerRegistry.getInstance();

// Register default providers on the singleton instance
viewerRegistry.register({
  id: "threed-viewer",
  label: "STL Viewer",
  selector: [{ extension: "stl" }],
  priority: "default",
  providerFactory: () => new ThreeDProvider(),
});

viewerRegistry.register({
  id: "code-editor",
  label: "Code Editor",
  selector: [
    { extension: "py" },
    { extension: "scad" },
    { extension: "json" },
    { extension: "txt" },
    { extension: "js" },
    { extension: "ts" },
    { extension: "tsx" },
    { extension: "jsx" },
    { extension: "css" },
  ],
  priority: "default",
  providerFactory: () => new CodeProvider(),
});

viewerRegistry.register({
  id: "markdown-viewer",
  label: "Markdown Viewer",
  selector: [
    { extension: "md" },
    { extension: "markdown" },
    { mimeType: "text/markdown" },
  ],
  priority: "default",
  providerFactory: () => new MarkdownProvider(),
});

viewerRegistry.register({
  id: "pdf-viewer",
  label: "PDF Document Viewer",
  selector: [{ extension: "pdf" }, { mimeType: "application/pdf" }],
  priority: "default",
  providerFactory: () => new PdfProvider(),
});

viewerRegistry.register({
  id: "iframe-viewer",
  label: "HTML Previewer",
  selector: [{ extension: "html" }, { extension: "htm" }],
  priority: "default",
  providerFactory: () => new IframeProvider(),
});

viewerRegistry.register({
  id: "image-viewer",
  label: "Image Viewer",
  selector: [
    { extension: "png" },
    { extension: "jpg" },
    { extension: "jpeg" },
    { extension: "webp" },
    { extension: "gif" },
    { extension: "bmp" },
    { extension: "svg" },
    { mimeType: "image/png" },
    { mimeType: "image/jpeg" },
    { mimeType: "image/webp" },
    { mimeType: "image/gif" },
    { mimeType: "image/bmp" },
    { mimeType: "image/svg+xml" },
  ],
  priority: "default",
  providerFactory: () => new ImageProvider(),
});

viewerRegistry.register({
  id: "text-viewer",
  label: "Plain Text Viewer",
  selector: [{ predicate: () => true }],
  priority: "option",
  providerFactory: () => new TextProvider(),
});

export default viewerRegistry;
