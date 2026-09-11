import type { PanelHost } from "../types";

function hasUnsafeWorkspacePathCharacter(value: string): boolean {
  // eslint-disable-next-line no-control-regex -- reject ASCII control characters in workspace paths
  return /[\\%<>:"|?*\u0000-\u001f\u007f]/.test(value);
}

/** Bare report paths are workspace-relative; explicit ./ and ../ are document-relative. */
export function workspaceHtmlLinkPath(
  documentUri: string,
  href: string,
): string | null {
  if (
    !href ||
    href !== href.trim() ||
    href.length > 2048 ||
    href.startsWith("#") ||
    href.startsWith("//") ||
    /^[a-z][a-z0-9+.-]*:/i.test(href) ||
    href.includes("?")
  )
    return null;
  let path: string;
  try {
    path = decodeURIComponent(href.split("#", 1)[0]);
  } catch {
    return null;
  }
  if (!path || hasUnsafeWorkspacePathCharacter(path) || path.startsWith("//"))
    return null;
  const parts =
    path.startsWith("./") || path.startsWith("../")
      ? documentUri.replace(/^\//, "").split("/").slice(0, -1)
      : [];
  for (const part of path.split("/")) {
    if (!part || part === ".") continue;
    if (part === "..") {
      if (!parts.length) return null;
      parts.pop();
    } else parts.push(part);
  }
  if (
    !parts.length ||
    parts.some(
      (part) =>
        /[. ]$/.test(part) ||
        /^(?:\.git|\.wright|con|prn|aux|nul|com[1-9]|lpt[1-9])(?:\.|$)/i.test(
          part,
        ) ||
        hasUnsafeWorkspacePathCharacter(part),
    )
  )
    return null;
  return "/" + parts.join("/");
}

export function bindWorkspaceHtmlLinks(
  preview: Document,
  documentUri: string,
  sessionId: string,
  panel: PanelHost,
): () => void {
  const paths = new Map<string, string>();
  const renderId = crypto.randomUUID();
  const authoredBase = preview
    .querySelector("base[href]")
    ?.getAttribute("href");
  // Preserve authored bases, especially external manuals with their own URL semantics.
  const hasAuthoredBase = Boolean(
    authoredBase && authoredBase !== "about:srcdoc",
  );
  for (const anchor of preview.querySelectorAll<HTMLAnchorElement>("a[href]")) {
    anchor.removeAttribute("data-wright-file-link");
    anchor.removeAttribute("data-wright-blocked-link");
    const href = anchor.getAttribute("href") ?? "";
    if (
      href.startsWith("#") ||
      /^(?:https?:|mailto:|tel:)/i.test(href) ||
      href.startsWith("//")
    )
      continue;
    if (hasAuthoredBase && !/^[a-z][a-z0-9+.-]*:/i.test(href)) continue;
    const path = workspaceHtmlLinkPath(documentUri, href);
    if (path) {
      const id = `${renderId}:${paths.size}`;
      paths.set(id, path);
      anchor.setAttribute("data-wright-file-link", id);
    } else anchor.setAttribute("data-wright-blocked-link", "true");
  }
  const script = preview.createElement("script");
  script.textContent = `window.addEventListener("click", function(event) {
    var anchor = event.target instanceof Element ? event.target.closest("a") : null;
    if (!anchor) return;
    var id = anchor.getAttribute("data-wright-file-link");
    if (!id && !anchor.hasAttribute("data-wright-blocked-link")) return;
    event.preventDefault();
    if (id && event.isTrusted) parent.postMessage({type:"wright-open-workspace-file", id:id}, "*");
  }, true);`;
  preview.head.prepend(script);
  // PanelHost verifies event.source against its current iframe.contentWindow.
  // No path/session supplied by frame content is accepted and no bytes return to it.
  const subscription = panel.onDidReceiveMessage((value) => {
    if (!value || typeof value !== "object") return;
    const message = value as { type?: unknown; id?: unknown };
    if (
      message.type !== "wright-open-workspace-file" ||
      typeof message.id !== "string"
    )
      return;
    const path = paths.get(message.id);
    if (path)
      panel.container.dispatchEvent(
        new CustomEvent("viewer-message", {
          detail: { type: "open-workspace-file", path, sessionId },
          bubbles: true,
        }),
      );
  });
  return () => {
    paths.clear();
    subscription.dispose();
  };
}
