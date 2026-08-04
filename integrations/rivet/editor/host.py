"""Bounded localhost host for Wright's pinned Rivet editor artifact."""

from __future__ import annotations

import argparse
import json
from http import HTTPStatus
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

MINIMAL_CSS = """
:root {
  --wright-rivet-hosted: 1;
}
[aria-label*="Community" i],
[title*="Community" i],
[aria-label*="Prompt Designer" i],
[title*="Prompt Designer" i],
[aria-label*="Trivet" i],
[title*="Trivet" i],
[aria-label*="Chat Viewer" i],
[title*="Chat Viewer" i],
[aria-label*="Data Studio" i],
[title*="Data Studio" i],
[aria-label*="New Project" i],
[title*="New Project" i],
[aria-label*="Open Project" i],
[title*="Open Project" i],
[aria-label*="Save Project" i],
[title*="Save Project" i],
[data-testid*="community" i],
[data-testid*="prompt" i],
[data-testid*="trivet" i],
[data-testid*="chat" i],
[data-testid*="data-studio" i] {
  display: none !important;
}
""".strip()

MINIMAL_JS = """
(() => {
  const params = new URLSearchParams(window.location.search);
  const workflowSlug = params.get("workflow") || "rivet";
  const workflowTitle = params.get("title") || workflowSlug
    .split("-")
    .filter(Boolean)
    .map((part) => part.charAt(0).toUpperCase() + part.slice(1))
    .join(" ") || "Rivet";
  const projectPath = `${workflowSlug}.rivet-project`;
  const projectId = `wright-${workflowSlug}`;
  let activeProjectText = localStorage.getItem(`wright.rivet.project.${workflowSlug}`)
    || localStorage.getItem("wright.activeRivetProject")
    || "";

  const blankProjectFile = () => JSON.stringify({
    version: 4,
    data: {
      graphs: {
        main: {
          metadata: { id: "main", name: "Main", description: "" },
          nodes: {},
        },
      },
      metadata: {
        id: projectId,
        title: workflowTitle,
        description: "",
        mainGraphId: "main",
      },
      plugins: [],
    },
  }, null, 2) + "\\n";

  const normalizeGraph = (id, graph) => {
    const source = graph && typeof graph === "object" ? graph : {};
    const metadata = source.metadata && typeof source.metadata === "object"
      ? source.metadata
      : {};
    const rawNodes = source.nodes || {};
    const nodes = Array.isArray(rawNodes)
      ? rawNodes
      : Object.entries(rawNodes).map(([nodeId, node]) => ({
          ...(node && typeof node === "object" ? node : {}),
          id: (node && typeof node === "object" && node.id) || nodeId,
        }));
    return {
      metadata: {
        id: metadata.id || id,
        name: metadata.name || (id === "main" ? "Main" : id),
        description: metadata.description || "",
      },
      nodes,
      connections: Array.isArray(source.connections) ? source.connections : [],
    };
  };

  const projectFromText = (text) => {
    try {
      const raw = JSON.parse(text);
      const data = raw.data && typeof raw.data === "object" ? raw.data : raw;
      const metadata = data.metadata && typeof data.metadata === "object"
        ? data.metadata
        : {};
      const rawGraphs = data.graphs && typeof data.graphs === "object"
        ? data.graphs
        : {};
      const graphs = Object.fromEntries(
        Object.entries(rawGraphs).map(([id, graph]) => [id, normalizeGraph(id, graph)]),
      );
      if (Object.keys(graphs).length === 0) {
        graphs.main = normalizeGraph("main", {});
      }
      return {
        metadata: {
          id: metadata.id || projectId,
          title: metadata.title || workflowTitle,
          description: metadata.description || "",
          mainGraphId: metadata.mainGraphId || "main",
        },
        graphs,
        plugins: Array.isArray(data.plugins) ? data.plugins : [],
      };
    } catch {
      return projectFromText(blankProjectFile());
    }
  };

  const putIndexedState = (key, value) => new Promise((resolve) => {
    if (!window.indexedDB) {
      resolve();
      return;
    }
    const request = indexedDB.open("jotai-store", 1);
    request.onupgradeneeded = () => {
      const db = request.result;
      if (!db.objectStoreNames.contains("state")) db.createObjectStore("state");
    };
    request.onerror = () => resolve();
    request.onsuccess = () => {
      const db = request.result;
      const tx = db.transaction("state", "readwrite");
      tx.objectStore("state").put(JSON.stringify(value), key);
      tx.oncomplete = () => {
        db.close();
        resolve();
      };
      tx.onerror = () => {
        db.close();
        resolve();
      };
    };
  });

  const seedEditorState = async (projectText) => {
    activeProjectText = projectText || blankProjectFile();
    localStorage.setItem("wright.activeRivetProject", activeProjectText);
    localStorage.setItem(`wright.rivet.project.${workflowSlug}`, activeProjectText);
    const project = projectFromText(activeProjectText);
    const graph = project.graphs[project.metadata.mainGraphId] || Object.values(project.graphs)[0] || normalizeGraph("main", {});
    const projectState = {
      projectState: project,
      loadedProjectState: { path: projectPath, loaded: true },
      projectsState: {
        openedProjects: {
          [project.metadata.id]: { project, fsPath: projectPath },
        },
        openedProjectsSortedIds: [project.metadata.id],
      },
    };
    const graphState = {
      graphState: graph,
      lastCanvasPositionByGraph: {
        [graph.metadata.id]: { x: 0, y: 0, zoom: 1 },
      },
    };
    localStorage.setItem("project", JSON.stringify(projectState));
    localStorage.setItem("graph", JSON.stringify(graphState));
    await Promise.all([
      putIndexedState("project", projectState),
      putIndexedState("graph", graphState),
    ]);
  };

  const fileHandle = () => ({
    kind: "file",
    name: projectPath,
    async getFile() {
      return new File([activeProjectText || blankProjectFile()], projectPath, {
        type: "application/json",
        lastModified: Date.now(),
      });
    },
    async createWritable() {
      const chunks = [];
      return {
        async write(chunk) {
          const payload = chunk && typeof chunk === "object" && "data" in chunk
            ? chunk.data
            : chunk;
          if (chunk && typeof chunk === "object" && chunk.type === "truncate") {
            chunks.length = 0;
            return;
          }
          chunks.push(typeof payload === "string" ? payload : await new Response(payload).text());
        },
        async close() {
          await seedEditorState(chunks.join(""));
        },
      };
    },
  });

  window.showOpenFilePicker = async () => [fileHandle()];
  window.showSaveFilePicker = async () => fileHandle();
  seedEditorState(activeProjectText || blankProjectFile());

  const hiddenLabels = [
    "Community",
    "Prompt Designer",
    "Trivet",
    "Chat Viewer",
    "Data Studio",
    "New Project",
    "Open Project",
    "Save Project",
    "Import Project",
    "Export Project",
  ];
  const candidateSelector = "button,a,[role='button'],[role='tab'],[aria-label],[title]";
  const startupLabels = [
    "open a project",
    "open project",
    "choose a project",
    "select a project",
    "import project",
  ];
  const shouldHide = (element) => {
    const text = [
      element.textContent,
      element.getAttribute("aria-label"),
      element.getAttribute("title"),
      element.getAttribute("data-testid"),
    ].filter(Boolean).join(" ");
    return hiddenLabels.some((label) => text.toLowerCase().includes(label.toLowerCase()));
  };
  const hideChrome = () => {
    document.querySelectorAll(candidateSelector).forEach((element) => {
      if (shouldHide(element)) {
        element.setAttribute("data-wright-minimal-hidden", "true");
        element.style.setProperty("display", "none", "important");
      }
    });
    document.querySelectorAll("button,a,[role='button']").forEach((element) => {
      const text = (element.textContent || "").trim().toLowerCase();
      if (startupLabels.some((label) => text.includes(label))) {
        element.setAttribute("data-wright-minimal-hidden", "true");
        element.style.setProperty("display", "none", "important");
      }
    });
  };
  const readProject = () => {
    if (activeProjectText) return activeProjectText;
    for (const key of Object.keys(localStorage)) {
      const value = localStorage.getItem(key) || "";
      if (
        key.toLowerCase().includes("rivet") ||
        key.toLowerCase().includes("project") ||
        value.includes("mainGraphId") ||
        value.includes("graphs:")
      ) {
        if (value.includes("version:") || value.includes('"version"')) return value;
      }
    }
    return null;
  };
  window.addEventListener("message", (event) => {
    const message = event.data || {};
    if (message.type === "wright-rivet:set-project" && typeof message.project === "string") {
      seedEditorState(message.project);
      event.source?.postMessage({ type: "wright-rivet:project-set", requestId: message.requestId }, event.origin);
    }
    if (message.type === "wright-rivet:get-project") {
      event.source?.postMessage({
        type: "wright-rivet:project",
        requestId: message.requestId,
        project: readProject(),
      }, event.origin);
    }
  });
  hideChrome();
  new MutationObserver(hideChrome).observe(document.documentElement, {
    childList: true,
    subtree: true,
  });
})();
""".strip()


def _send_static(handler: SimpleHTTPRequestHandler, body: bytes, content_type: str) -> None:
    handler.send_response(HTTPStatus.OK)
    handler.send_header("Content-Type", content_type)
    handler.send_header("Content-Length", str(len(body)))
    handler.end_headers()
    handler.wfile.write(body)


def _inject_minimal_mode(content: bytes) -> bytes:
    text = content.decode("utf-8")
    css = '<link rel="stylesheet" href="/wright-minimal-mode.css">'
    script = '<script src="/wright-minimal-mode.js"></script>'
    if css not in text:
        text = (
            text.replace("</head>", f"{css}</head>", 1)
            if "</head>" in text
            else f"{css}{text}"
        )
    if script not in text:
        text = (
            text.replace("</head>", f"{script}</head>", 1)
            if "</head>" in text
            else f"{script}{text}"
        )
    return text.encode("utf-8")


class EditorHandler(SimpleHTTPRequestHandler):
    def __init__(self, *args, root: Path, **kwargs) -> None:
        self._root = root
        super().__init__(*args, directory=str(root), **kwargs)

    def do_GET(self) -> None:  # noqa: N802
        requested = self.path.split("?", 1)[0]
        if requested == "/health":
            body = json.dumps({"status": "ok", "mode": "wright-workspace"}).encode()
            _send_static(self, body, "application/json")
            return
        if requested == "/wright-minimal-mode.css":
            _send_static(self, MINIMAL_CSS.encode("utf-8"), "text/css; charset=utf-8")
            return
        if requested == "/wright-minimal-mode.js":
            _send_static(
                self,
                MINIMAL_JS.encode("utf-8"),
                "application/javascript; charset=utf-8",
            )
            return
        if requested != "/" and "." not in Path(requested).name:
            self.path = "/index.html"
        super().do_GET()

    def do_HEAD(self) -> None:  # noqa: N802
        if self.path.split("?", 1)[0] in {
            "/health",
            "/wright-minimal-mode.css",
            "/wright-minimal-mode.js",
        }:
            self.send_response(HTTPStatus.OK)
            self.end_headers()
            return
        super().do_HEAD()

    def send_head(self):  # noqa: ANN001
        requested = self.path.split("?", 1)[0]
        if requested in {"/", "/index.html"}:
            path = self.translate_path("/index.html")
            content = _inject_minimal_mode(Path(path).read_bytes())
            self.send_response(HTTPStatus.OK)
            self.send_header("Content-Type", "text/html; charset=utf-8")
            self.send_header("Content-Length", str(len(content)))
            self.end_headers()
            import io

            return io.BytesIO(content)
        return super().send_head()

    def end_headers(self) -> None:
        self.send_header("Cache-Control", "no-store")
        self.send_header("X-Content-Type-Options", "nosniff")
        super().end_headers()


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", type=Path, required=True)
    parser.add_argument("--host", required=True)
    parser.add_argument("--port", type=int, required=True)
    args = parser.parse_args()
    root = args.root.resolve()
    if not (root / "index.html").is_file():
        raise SystemExit("verified Rivet editor entrypoint is unavailable")
    server = ThreadingHTTPServer(
        (args.host, args.port), lambda *a, **kw: EditorHandler(*a, root=root, **kw)
    )
    server.serve_forever()


if __name__ == "__main__":
    main()
