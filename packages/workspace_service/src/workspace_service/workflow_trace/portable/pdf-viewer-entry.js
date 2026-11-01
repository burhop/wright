import { getDocument, PDFWorker } from "pdfjs-dist/build/pdf.mjs";

const decode = (value) =>
  Uint8Array.from(atob(value), (byte) => byte.charCodeAt(0));
class BundledDataFactory {
  async fetch({ kind, filename }) {
    const value = window.WrightPDFAssets[`${kind}/${filename}`];
    if (!value) throw new Error("This PDF resource is not available offline.");
    return decode(value);
  }
}

function mount(element, base64, title, originalUrl) {
  if (element.viewerDispose) return;
  element.innerHTML = `<div class="pdf-toolbar" role="group" aria-label="PDF controls">
    <button data-pdf-prev title="Previous page" aria-label="Previous page">&#8592;</button>
    <label>Page <input data-pdf-page type="number" min="1" value="1" aria-label="PDF page"></label><span data-pdf-count></span>
    <button data-pdf-next title="Next page" aria-label="Next page">&#8594;</button>
    <button data-pdf-out title="Zoom out" aria-label="Zoom out">&#8722;</button>
    <output data-pdf-scale>100%</output>
    <button data-pdf-in title="Zoom in" aria-label="Zoom in">+</button>
    <button data-pdf-fit title="Fit drawing to view" aria-label="Fit drawing to view">&#8644;</button>
  </div><p class="pdf-status" role="status">Loading document...</p><div class="pdf-viewport"><canvas role="img"></canvas></div>`;
  let canvas = element.querySelector("canvas");
  canvas.setAttribute("aria-label", title);
  const viewport = element.querySelector(".pdf-viewport");
  const status = element.querySelector(".pdf-status");
  const fallback = document.createElement("a");
  fallback.textContent = "Download original PDF";
  fallback.hidden = true;
  if (originalUrl) {
    fallback.href = originalUrl;
    fallback.download = "";
    element.append(fallback);
  }
  const input = element.querySelector("[data-pdf-page]");
  const controls = [...element.querySelectorAll("button,input")];
  controls.forEach((control) => {
    control.disabled = true;
  });
  let disposed = false,
    failed = false,
    pdf,
    renderTask,
    pageNumber = 1,
    zoom = 1;
  let generation = 0,
    requestedKey,
    resizeTimer,
    queue = Promise.resolve();
  const workerUrl = URL.createObjectURL(
    new Blob([window.WrightPDFWorkerSource], { type: "text/javascript" }),
  );
  let port, worker, loading;
  const showError = (error) => {
    if (disposed) return;
    failed = true;
    console.warn("PDF preview failed", error);
    element.setAttribute("aria-busy", "false");
    element.dataset.pdfState = "error";
    viewport.hidden = true;
    fallback.hidden = false;
    status.hidden = false;
    status.textContent =
      "This PDF could not be displayed. The original file is available below.";
    controls.forEach((control) => {
      control.disabled = true;
    });
  };
  function render() {
    if (disposed || failed || !pdf) return;
    const style = getComputedStyle(viewport);
    const width = Math.max(
      1,
      viewport.clientWidth -
        parseFloat(style.paddingLeft) -
        parseFloat(style.paddingRight),
    );
    // Fit against the fixed frame, not the changing horizontal scrollbar area.
    const height = Math.max(
      1,
      Math.floor(
        viewport.getBoundingClientRect().height -
          parseFloat(style.borderTopWidth) -
          parseFloat(style.borderBottomWidth) -
          parseFloat(style.paddingTop) -
          parseFloat(style.paddingBottom),
      ),
    );
    const targetPage = pageNumber;
    const targetZoom = zoom;
    const pixelRatio = Math.min(window.devicePixelRatio || 1, 2);
    const key = [targetPage, targetZoom, width, height, pixelRatio].join(":");
    if (requestedKey === key) return;
    requestedKey = key;
    const revision = ++generation;
    renderTask?.cancel();
    queue = queue
      .catch(() => {})
      .then(async () => {
        if (disposed || !pdf || revision !== generation) return;
        element.dataset.pdfState = "loading";
        element.setAttribute("aria-busy", "true");
        const page = await pdf.getPage(targetPage);
        if (disposed || revision !== generation) return;
        const original = page.getViewport({ scale: 1 });
        const fit = Math.min(width / original.width, height / original.height);
        const view = page.getViewport({
          scale: Math.max(0.1, fit * targetZoom),
        });
        const density = Math.min(
          pixelRatio,
          Math.sqrt(12_000_000 / (view.width * view.height)),
        );
        // Render offscreen so cancellation or resizing cannot erase the drawing.
        const nextCanvas = document.createElement("canvas");
        nextCanvas.width = Math.max(1, Math.floor(view.width * density));
        nextCanvas.height = Math.max(1, Math.floor(view.height * density));
        nextCanvas.style.width = `${view.width}px`;
        nextCanvas.style.height = `${view.height}px`;
        nextCanvas.setAttribute("role", "img");
        nextCanvas.setAttribute(
          "aria-label",
          `${title}, page ${targetPage} of ${pdf.numPages}`,
        );
        renderTask = page.render({
          canvasContext: nextCanvas.getContext("2d"),
          viewport: view,
          transform: [density, 0, 0, density, 0, 0],
        });
        await renderTask.promise;
        if (disposed || revision !== generation) return;
        canvas.replaceWith(nextCanvas);
        canvas = nextCanvas;
        status.hidden = true;
        element.setAttribute("aria-busy", "false");
        element.dataset.pdfState = "ready";
        input.value = String(pageNumber);
        input.max = String(pdf.numPages);
        controls.forEach((control) => {
          control.disabled = false;
        });
        element.querySelector("[data-pdf-prev]").disabled = pageNumber === 1;
        element.querySelector("[data-pdf-next]").disabled =
          pageNumber === pdf.numPages;
        element.querySelector("[data-pdf-count]").textContent =
          `of ${pdf.numPages}`;
        element.querySelector("[data-pdf-scale]").textContent =
          `${Math.round(zoom * 100)}%`;
        element.querySelector("[data-pdf-in]").disabled = zoom >= 4;
        element.querySelector("[data-pdf-out]").disabled = zoom <= 0.5;
      })
      .catch((error) => {
        if (
          error?.name !== "RenderingCancelledException" &&
          revision === generation
        )
          showError(error);
      });
  }
  element.addEventListener("click", (event) => {
    const button = event.target.closest("button");
    if (!button || !pdf) return;
    if (button.hasAttribute("data-pdf-prev"))
      pageNumber = Math.max(1, pageNumber - 1);
    if (button.hasAttribute("data-pdf-next"))
      pageNumber = Math.min(pdf.numPages, pageNumber + 1);
    if (button.hasAttribute("data-pdf-in")) zoom = Math.min(4, zoom + 0.25);
    if (button.hasAttribute("data-pdf-out")) zoom = Math.max(0.5, zoom - 0.25);
    if (button.hasAttribute("data-pdf-fit")) zoom = 1;
    render();
  });
  input.addEventListener("change", () => {
    if (!pdf) return;
    pageNumber = Math.max(
      1,
      Math.min(pdf.numPages, Math.round(Number(input.value)) || 1),
    );
    render();
  });
  const scheduleResize = () => {
    clearTimeout(resizeTimer);
    resizeTimer = setTimeout(render, 80);
  };
  const observer = new ResizeObserver(scheduleResize);
  observer.observe(viewport, { box: "border-box" });
  window.addEventListener("resize", scheduleResize);
  element.viewerDispose = () => {
    disposed = true;
    clearTimeout(resizeTimer);
    window.removeEventListener("resize", scheduleResize);
    observer.disconnect();
    renderTask?.cancel();
    loading?.destroy().catch(() => {});
    worker?.destroy();
    port?.terminate();
    URL.revokeObjectURL(workerUrl);
  };
  try {
    port = new Worker(workerUrl);
    port.addEventListener("error", showError);
    worker = PDFWorker.create({ port });
    loading = getDocument({
      data: decode(base64),
      worker,
      BinaryDataFactory: BundledDataFactory,
      useWorkerFetch: false,
      useWasm: false,
      useSystemFonts: true,
      disableFontFace: true,
      enableXfa: false,
      stopAtErrors: true,
      maxImageSize: 16_000_000,
      verbosity: 0,
    });
    loading.onPassword = () => {
      showError();
      loading.destroy().catch(() => {});
    };
    loading.promise
      .then((document) => {
        if (!disposed) {
          pdf = document;
          render();
        }
      })
      .catch(showError);
  } catch (error) {
    showError(error);
  }
}
window.WrightPDFViewer = { mount };
