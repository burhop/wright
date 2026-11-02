(() => {
  "use strict";
  const {
    review: r,
    manifest,
    viewerModels = {},
    viewerDocuments = {},
  } = JSON.parse(document.getElementById("wright-trace-data").textContent);
  const esc = (value) =>
    String(value ?? "").replace(
      /[&<>"']/g,
      (char) =>
        ({
          "&": "&amp;",
          "<": "&lt;",
          ">": "&gt;",
          '"': "&quot;",
          "'": "&#39;",
        })[char],
    );
  const doc = (id) =>
    r.documents.find((item) => item.id === id && !item.archive_only);
  const step = (id) => r.steps.find((item) => item.id === id);
  const entry = (item) =>
    manifest.entries.find((value) => value.subject_id === item?.subject_id);
  const localPath = (item) => {
    const path = entry(item)?.package_path;
    return path &&
      /^(inputs|outputs|assets|evidence)\/[A-Za-z0-9._/-]+$/.test(path) &&
      !path.split("/").includes("..")
      ? path
      : null;
  };
  const date = (value, seconds = false) => {
    const parsed = new Date(value);
    return value && !Number.isNaN(parsed.valueOf())
      ? new Intl.DateTimeFormat("en", {
          dateStyle: "medium",
          timeStyle: seconds ? "medium" : "short",
          timeZone: "UTC",
        }).format(parsed) + " UTC"
      : "Not recorded";
  };
  const state = (value) =>
    ({
      succeeded: "Completed",
      completed: "Completed",
      failed: "Failed",
      blocked: "Blocked",
      cancelled: "Cancelled",
      skipped: "Skipped",
      running: "In progress",
    })[value] || "Recorded";
  const duration = (value) =>
    Number.isFinite(value)
      ? `${Math.floor(Math.round(value / 1000) / 60)} min ${Math.round(value / 1000) % 60} sec`
      : "Not recorded";
  const kind = (item) =>
    item.review_visualization
      ? "Derived engineering visualization"
      : item.media_type.startsWith("image/")
        ? "Recorded image"
        : /\.(stl|step|stp|3mf)$/i.test(item.name)
          ? "Engineering model"
          : item.tables.length
            ? "Engineering record"
            : "Supporting file";
  const documentButton = (id) => {
    const item = doc(id);
    return item
      ? `<button class="document-link" data-document="${esc(id)}">${/^image\/(png|jpeg|gif|webp)$/.test(item.media_type) && localPath(item) ? `<img class="document-thumbnail" src="${esc(localPath(item))}" alt="">` : ""}<span><strong>${esc(item.title)}</strong><small>${esc(kind(item))}</small></span><span class="document-arrow" aria-hidden="true">&#8599;</span></button>`
      : "";
  };
  const pictures = r.previews.map(doc).filter((item) => localPath(item));
  const image = (item) =>
    `<img src="${esc(localPath(item))}" alt="${esc(item.title)}" loading="eager">`;
  const models = (r.interactive_models || [])
    .map(doc)
    .filter((item) => item && viewerModels[item.id]);
  const modelViewer = (item, className = "") =>
    `<div class="stl-viewer${className ? ` ${esc(className)}` : ""}" data-stl-viewer="${esc(item.id)}" aria-label="Interactive 3D view of ${esc(item.title)}"></div>`;
  const pdfViewer = (item) =>
    `<div class="pdf-viewer" data-pdf-viewer="${esc(item.id)}" aria-label="${esc(item.title)}"></div>`;
  const resultVisualCount = pictures.length + models.length;
  const allInputs = r.inputs || [];
  const inputs = allInputs.filter((item) => !item.variant_of);
  const suppliedInputs = inputs.filter((item) => !item.reconstructed);
  const reconstructedInputs = inputs.filter((item) => item.reconstructed);
  const inputStatus = (item) =>
    item.reconstructed
      ? "Reassembled context"
      : item.identity_only
        ? "Fingerprint only"
        : item.redacted
          ? "Redacted record"
          : !item.complete
            ? "Partial record"
            : item.text || item.tables.length
              ? "Recorded input"
              : item.document_id && localPath(doc(item.document_id))
                ? "Included file"
                : item.document_id
                  ? "Original not included"
                  : "Referenced only";
  const inputButton = (item) =>
    `<button class="input-link" data-input="${esc(item.id)}"><span><strong>${esc(item.title)}</strong><small>${item.format_note ? `${esc(item.format_note)} / ` : ""}${esc(inputStatus(item))}</small></span><span aria-hidden="true">&#8599;</span></button>`;
  const groupOrder = ["Prompts", "Images", "Documents", "Models", "Parameters"];
  const inputCounts = groupOrder
    .map((group) => {
      const count = suppliedInputs.filter(
        (item) => item.group === group,
      ).length;
      return count
        ? `${count} ${count === 1 ? group.slice(0, -1).toLowerCase() : group.toLowerCase()}`
        : "";
    })
    .filter(Boolean)
    .join(" / ");
  const brief =
    suppliedInputs.find((item) => item.group === "Prompts" && item.text) ||
    suppliedInputs.find((item) => item.group === "Prompts");
  const briefLong =
    brief?.text && (brief.text.length > 240 || brief.text.includes("\n"));
  const briefAvailability = brief?.identity_only
    ? "Only the prompt fingerprint was retained."
    : brief?.document_id && localPath(doc(brief.document_id))
      ? "The original prompt is included as a document."
      : "The original prompt was not retained; its input reference is recorded.";
  const attachments = suppliedInputs.filter((item) => item !== brief);
  const visualInputs = attachments
    .filter((item) => {
      const original = doc(item.document_id);
      return (
        original &&
        /^image\/(png|jpeg|gif|webp|svg\+xml)$/.test(original.media_type) &&
        localPath(original)
      );
    })
    .slice(0, 2);
  const linkedInputs = attachments.filter(
    (item) => !visualInputs.includes(item),
  );
  const filesOnly = linkedInputs.every((item) =>
    ["Images", "Documents", "Models"].includes(item.group),
  );
  const remainingInputs = linkedInputs.slice(3);
  const inputVisual = (item) => {
    const original = doc(item.document_id);
    return `<figure class="input-visual">${image(original)}<figcaption><span><strong>${esc(item.title)}</strong><small>${esc(inputStatus(item))}</small></span><button class="source-button" data-input="${esc(item.id)}">View</button></figcaption></figure>`;
  };
  const inputOverview = `<section class="inputs-section" aria-labelledby="inputs-heading">
    <div class="section-heading"><div><h2 id="inputs-heading">Inputs</h2>${inputCounts ? `<p>${esc(inputCounts)}</p>` : ""}</div></div>
    ${brief ? `<div class="input-brief"><h3>${esc(brief.title)}</h3>${brief.text ? `<p class="input-excerpt${briefLong ? " clipped" : ""}">${esc(brief.text)}</p>${briefLong ? `<button class="source-button" data-input="${esc(brief.id)}">Read full prompt</button>` : ""}${!brief.complete || brief.redacted ? `<p class="input-status">${esc(inputStatus(brief))}</p>` : ""}` : `<p class="input-missing">${esc(briefAvailability)}</p><button class="source-button" data-input="${esc(brief.id)}">View prompt record</button>`}</div>` : ""}
    ${visualInputs.length ? `<div class="input-visual-list" aria-label="Supplied visual inputs">${visualInputs.map(inputVisual).join("")}</div>` : ""}
    ${linkedInputs.length ? `<div class="input-attachments"><h3>${filesOnly ? "Other supplied files" : "Additional inputs"}</h3><div class="input-preview-list">${linkedInputs.slice(0, 3).map(inputButton).join("")}</div>${remainingInputs.length ? `<details class="input-more"><summary>${remainingInputs.length} more ${filesOnly ? "files" : "inputs"}</summary><div class="input-preview-list">${remainingInputs.map(inputButton).join("")}</div></details>` : ""}</div>` : ""}
    ${reconstructedInputs.length ? `<details class="input-context"><summary>Reassembled context</summary><div class="input-preview-list">${reconstructedInputs.map(inputButton).join("")}</div></details>` : ""}
    ${!inputs.length ? '<p class="input-missing">Input records were not retained for this run.</p>' : ""}
  </section>`;
  const node = (item, index) => {
    const latest = item.attempts.at(-1);
    const files = item.documents.filter(doc);
    const visualFiles = files
      .map(doc)
      .filter(
        (value) =>
          value &&
          /^image\/(png|jpeg|gif|webp|svg\+xml)$/.test(value.media_type) &&
          localPath(value),
      )
      .slice(0, 2);
    const visualIds = new Set(visualFiles.map((value) => value.id));
    const outputs = (latest?.documents || item.documents)
      .filter((id) => doc(id) && !visualIds.has(id))
      .slice(0, 2);
    const tool =
      item.software && !/not (recorded|retained)/i.test(item.software)
        ? item.software
        : "Not recorded";
    const summary =
      item.summary && item.summary !== "Recorded workflow activity."
        ? `<small>${esc(item.summary)}</small>`
        : "";
    return `<div class="activity-column"><div id="${esc(item.id)}" class="step-block${item.decision ? " decision" : ""}${item.state === "failed" ? " failed" : ""}"><button class="step-node${item.decision ? " decision" : ""}${item.state === "failed" ? " failed" : ""}" data-step="${esc(item.id)}" aria-label="${esc(item.title)}"><span class="node-line"><i></i>${index + 1}. ${esc(state(item.state))}</span><strong>${esc(item.title)}</strong>${summary}<span class="node-tool"><span>Tool used</span><b>${esc(tool)}</b></span>${item.attempts.length > 1 ? `<span class="node-passes">${item.attempts.length} recorded passes</span>` : ""}</button></div>${files.length ? `<div class="step-outputs"><span class="output-caption">Evidence &amp; outputs${item.attempts.length > 1 ? " / latest pass" : ""}</span>${visualFiles.length ? `<div class="step-visuals">${visualFiles.map((value) => `<button data-document="${esc(value.id)}" aria-label="View ${esc(value.title)}">${image(value)}<span>${esc(value.title)}</span></button>`).join("")}</div>` : ""}${outputs.map((id) => `<button class="output-link" data-document="${esc(id)}">${esc(doc(id)?.title)} <span aria-hidden="true">&#8599;</span></button>`).join("")}<button class="node-documents" data-step-files="${esc(item.id)}" aria-label="Files from ${esc(item.title)} (${files.length})"><span>All ${files.length} ${files.length === 1 ? "file" : "files"}</span><span aria-hidden="true">&#8599;</span></button></div>` : ""}</div>`;
  };
  const feeds = r.steps
    .filter((item) => item.input_ids?.length)
    .map((item) => ({
      target: item,
      inputs: inputs.filter((input) => item.input_ids.includes(input.id)),
      scope: "activity",
    }));
  const assignedInputs = new Set(
    feeds.flatMap((feed) => feed.inputs.map((input) => input.id)),
  );
  const runInputs = inputs.filter((input) => !assignedInputs.has(input.id));
  if (runInputs.length)
    feeds.unshift({
      target: r.steps[0] || null,
      inputs: runInputs,
      scope: "run",
    });
  const laneToggle = (title) =>
    `<button class="lane-title lane-toggle" data-lane-toggle aria-expanded="false" title="Expand ${esc(title)}"><span class="lane-chevron" aria-hidden="true">&#9656;</span><span>${esc(title)}</span></button>`;
  const inputCard = (item) => {
    const original = doc(item.document_id);
    const picture =
      original &&
      /^image\/(png|jpeg|webp)$/.test(original.media_type) &&
      localPath(original);
    const sources = (item.source_document_ids || []).map(doc).filter(Boolean);
    const type =
      {
        Prompts: "Prompt",
        Images: "Image",
        Documents: "Document",
        Models: "Model",
        Parameters: "Parameters",
      }[item.group] || "Input";
    return `<article class="input-card"><button class="input-card-heading" data-input="${esc(item.id)}" aria-label="${esc(item.title)}"><span class="input-card-kind">${esc(type)}</span><strong>${esc(item.title)}</strong><span class="input-card-status">${esc(inputStatus(item))}</span></button><div class="input-card-details">
      ${picture ? `<button class="input-card-image" data-input="${esc(item.id)}" aria-label="View ${esc(item.title)}">${image(original)}</button>` : ""}
      ${item.text && !sources.length ? `<p class="process-request-text">${esc(item.text)}</p>` : ""}
      ${sources.length ? `<p class="input-source-label">${item.reconstructed ? "Assembled from" : "Source documents"}</p><div class="input-card-sources">${sources.map((source) => `<button class="source-button" data-document="${esc(source.id)}">${esc(source.title)}</button>`).join("")}</div>${item.reconstructed ? '<p class="input-source-note">Reassembled for this review; original execution snapshot unavailable.</p>' : ""}` : ""}
      <button class="source-button" data-input="${esc(item.id)}">${item.group === "Prompts" ? "Read supplied request" : "View input & source"}</button>
    </div></article>`;
  };
  const inputLanes = feeds
    .map((feed, index) => {
      const ordered = [...feed.inputs].sort(
        (a, b) => groupOrder.indexOf(a.group) - groupOrder.indexOf(b.group),
      );
      const visible = ordered.slice(0, 3);
      const remaining = ordered.length - visible.length;
      const all =
        feed.target && feed.scope === "activity"
          ? `data-step-inputs="${esc(feed.target.id)}"`
          : "data-inputs";
      return `<div class="input-lane" data-expanded="false">${laneToggle("Supplied inputs")}<div class="input-feed" id="input-feed-${index}" style="--feed-count:${Math.max(1, visible.length + (remaining ? 1 : 0))}"><div class="feed-cards">
      ${visible.map(inputCard).join("")}
      ${remaining ? `<article class="input-card input-card-more"><button class="input-card-heading" ${all}><span class="input-card-kind">Input set</span><strong>${remaining} more inputs</strong><span class="input-card-status">${ordered.length} in total</span></button><div class="input-card-details"><button class="source-button" ${all}>Review all inputs</button></div></article>` : ""}
      ${!visible.length ? '<p class="input-missing">Input references could not be resolved.</p>' : ""}
    </div><div class="feed-recipient"><div>${feed.target ? `${feed.scope === "run" ? "Process begins with" : "Used by"} <button class="source-button" data-step="${esc(feed.target.id)}">${esc(feed.target.title)}</button>` : "No recorded activities"}</div><div class="feed-input-access">${feed.target && feed.scope === "activity" ? `<button class="source-button" ${all}>All activity inputs</button>` : ""}${index === 0 ? `<button class="source-button" data-inputs>${reconstructedInputs.length ? "Run inputs & context" : "All run inputs"}</button>` : ""}</div></div></div></div>`;
    })
    .join("");
  const assignedDocuments = new Set(r.steps.flatMap((item) => item.documents));
  const runDocuments = r.documents.filter(
    (item) =>
      !item.archive_only &&
      !item.input_only &&
      !item.review_source &&
      !assignedDocuments.has(item.id),
  );
  const factList = (values) =>
    `<dl>${values.map(([label, value]) => `<div><dt>${esc(label)}</dt><dd>${esc(value)}</dd></div>`).join("")}</dl>`;
  const printingOverview = r.printing
    ? `<section class="printing-summary" aria-labelledby="printing-heading">
    <h3 id="printing-heading">3D printing</h3>${factList(r.printing.facts)}
    ${r.printing.settings_id ? `<button class="source-button" data-document="${esc(r.printing.settings_id)}">Print settings</button>` : ""}
    <section class="supports-summary" aria-labelledby="supports-heading"><h4 id="supports-heading">Supports</h4>
      <p class="support-status">${esc(r.printing.support_summary)}</p>${factList(r.printing.support_facts || [])}
      <p class="preview-availability">${esc(r.printing.support_preview_note)}</p>
      <div class="printing-links">${r.printing.evidence_id ? `<button class="source-button" data-document="${esc(r.printing.evidence_id)}">Slicing results</button>` : ""}</div>
    </section>
    ${r.printing.preparation?.length ? `<details class="preparation-summary"><summary>Model preparation</summary>${factList(r.printing.preparation)}${r.printing.preparation_id ? `<button class="source-button" data-document="${esc(r.printing.preparation_id)}">Source: Mesh repair and measurement report</button>` : ""}</details>` : ""}
  </section>`
    : "";

  document.getElementById("report").innerHTML = `
    <div class="topbar"><div class="topbar-inner"><span class="wordmark">wright</span><span class="topbar-label">Engineering review</span><span class="topbar-date">${esc(date(r.date))}</span></div></div>
    <div class="page">
      <header><p class="kicker">${esc(r.subtitle)}</p><h1>${esc(r.title)}</h1></header>
      ${inputOverview}
      <section class="section outputs-section" aria-labelledby="outputs-heading"><div class="section-heading"><h2 id="outputs-heading">Outputs</h2><span class="badge${r.simulated_handoff ? " test" : ""}">${esc(r.outcome)}</span></div><p class="outcome">${esc(r.summary)}</p>
      <div class="result-band${resultVisualCount === 0 ? " no-preview" : ""}" role="region" aria-label="Engineering results">
        ${
          resultVisualCount
            ? `<div class="result-visuals">
          ${models.length ? `<section class="visual-group" aria-labelledby="geometry-results-heading"><h3 id="geometry-results-heading">Geometry</h3><div class="visual-grid model-grid">${models.map((item) => `<figure class="model-frame">${modelViewer(item)}<figcaption><span>${esc(item.title)}<small>Interactive STL / drag to rotate</small></span><button class="source-button" data-document="${esc(item.id)}">Details</button></figcaption></figure>`).join("")}</div></section>` : ""}
          ${pictures.length ? `<section class="visual-group" aria-labelledby="visual-results-heading"><h3 id="visual-results-heading">Engineering visualizations</h3><div class="visual-grid image-grid">${pictures.map((item) => `<figure class="image-frame">${image(item)}<figcaption><span>${esc(item.title)}${item.caption ? `<small>${esc(item.caption)}</small>` : ""}</span><button class="source-button" data-document="${esc(item.id)}">Inspect</button></figcaption></figure>`).join("")}</div></section>` : ""}
        </div>`
            : ""
        }
        <div class="facts">${factList(r.facts)}${printingOverview}<div>${r.deliverables.map((id) => `<button class="file-action" data-document="${esc(id)}">${esc(doc(id)?.title)} <span aria-hidden="true">&#8599;</span></button>`).join("")}${r.simulated_handoff ? '<p class="test-status">Test handoff only<br>No physical printer dispatch</p>' : ""}</div></div>
      </div></section>
      ${r.diagnostic ? `<section class="error-summary"><h2>Execution stopped</h2><p>${esc(typeof r.diagnostic === "string" ? r.diagnostic : r.diagnostic.summary || r.diagnostic.message || "See the recorded failure details.")}</p></section>` : ""}
      <section class="section" aria-labelledby="process-heading"><div class="section-heading"><div><h2 id="process-heading">Process &amp; handoffs</h2><p>${r.steps.length} activities${r.simulated_handoff ? " / final handoff simulated" : ""}</p></div><div class="process-controls"><div class="diagram-zoom"><label>Zoom<input type="range" min="10" max="150" step="1" value="100" data-diagram-zoom aria-label="Process zoom"></label><output data-zoom-value>100%</output><button data-fit-diagram title="Fit all activity columns">Fit width</button></div><div class="legend"><span><i></i>Completed activity</span><span><i class="test-dot"></i>Authorization</span></div></div></div>
        <div class="diagram-scroll" tabindex="0" aria-label="Process swimlanes"><div class="diagram" style="--count:${Math.max(1, r.steps.length)}">
          <div class="phase-head"><span>Responsibility</span>${r.steps.map((item, index) => `<span>${index + 1}. ${esc({ design: "Geometry", repair: "Mesh preparation", slice: "Manufacturing", authorization: "Authorization" }[item.stage] || "Activity")}</span>`).join("")}</div>
          ${inputLanes}
          ${r.lanes.map((lane) => `<div class="lane" data-expanded="false" style="--lane-steps:${r.steps.filter((item) => item.lane === lane).length}">${laneToggle(lane)}${r.steps.map((item, index) => `<div class="lane-cell">${item.lane === lane ? node(item, index) : ""}</div>`).join("")}</div>`).join("")}
          <svg class="connectors" aria-hidden="true"><defs><marker id="arrow" markerWidth="7" markerHeight="7" refX="6" refY="3.5" orient="auto"><path d="M0 0 L7 3.5 L0 7 Z" fill="#668d82"/></marker></defs><g id="paths"></g></svg><div id="edge-labels"></div>
        </div></div>
        <p class="process-foot">${esc(r.graph_note || "Activities from the recorded execution; handoffs supported by retained source records.")}</p>
        ${runDocuments.length ? `<button class="source-button" data-run-files>Run-level files (${runDocuments.length})</button>` : ""}
      </section>
      <footer><span>Wright / Engineering process record</span><span>${manifest.mode === "full_data" ? "Report and retained data" : "Report with recorded images / originals excluded"}</span></footer>
    </div>`;

  function mountViewers(root = document) {
    root.querySelectorAll("[data-pdf-viewer]").forEach((element) => {
      const item = doc(element.dataset.pdfViewer);
      const payload = viewerDocuments[element.dataset.pdfViewer];
      if (item && payload?.base64 && window.WrightPDFViewer)
        window.WrightPDFViewer.mount(
          element,
          payload.base64,
          item.title,
          localPath(item),
        );
    });
    root.querySelectorAll(".readable-document").forEach((element) => {
      const item = doc(element.dataset.documentText);
      if (!item?.source_text) return;
      if (item.media_type === "text/markdown" && window.WrightDocumentViewer) {
        const content = document.createElement("template");
        content.innerHTML = window.WrightDocumentViewer.markdown(
          item.source_text,
        );
        content.content.querySelectorAll("img").forEach((img) => {
          const text = document.createElement("span");
          text.textContent = img.alt || "Referenced image";
          img.replaceWith(text);
        });
        content.content.querySelectorAll("a").forEach((link) => {
          const href = link.getAttribute("href") || "";
          const related = r.documents.filter((value) =>
            value.subject_id.endsWith(`:${href}`),
          );
          if (related.length === 1) {
            const button = document.createElement("button");
            button.className = "source-button";
            button.dataset.document = related[0].id;
            button.textContent = link.textContent;
            link.replaceWith(button);
          } else if (/^https?:\/\//i.test(href)) {
            link.target = "_blank";
            link.rel = "noopener noreferrer";
          } else {
            link.removeAttribute("href");
            link.title = "Referenced location: " + href;
          }
        });
        element.replaceChildren(content.content);
      } else element.textContent = item.source_text;
    });
    root.querySelectorAll("[data-stl-viewer]").forEach((element) => {
      const item = doc(element.dataset.stlViewer);
      const payload = viewerModels[element.dataset.stlViewer];
      if (item && payload?.base64 && window.WrightSTLViewer) {
        window.WrightSTLViewer.mount(element, payload.base64, item.title);
      }
    });
  }
  function disposeViewers(root) {
    root
      .querySelectorAll("[data-stl-viewer],[data-pdf-viewer]")
      .forEach((element) => element.viewerDispose?.());
  }
  mountViewers(document.getElementById("report"));

  const diagram = document.querySelector(".diagram");
  const zoomInput = document.querySelector("[data-diagram-zoom]");
  function setZoom(value) {
    const percent = Math.max(10, Math.min(150, Math.round(value)));
    diagram.dataset.zoom = String(percent / 100);
    diagram.style.zoom = percent / 100;
    zoomInput.value = percent;
    document.querySelector("[data-zoom-value]").textContent = `${percent}%`;
    drawEdges();
  }
  function drawEdges() {
    const zoom = Number(diagram.dataset.zoom || 1);
    const box = (element) => {
      if (!element) return null;
      const rect = element.getBoundingClientRect();
      return Object.fromEntries(
        ["left", "right", "top", "bottom", "width", "height"].map((key) => [
          key,
          rect[key] / zoom,
        ]),
      );
    };
    const origin = box(diagram);
    const paths = [],
      labels = [];
    r.edges.forEach((item) => {
      const sourceNode = document.getElementById(item.source);
      const sourceColumn = box(sourceNode?.closest(".activity-column"));
      const a = box(sourceNode);
      const b = box(document.getElementById(item.target));
      if (!a || !b) return;
      const x1 = a.right - origin.left,
        y1 = a.top + a.height / 2 - origin.top;
      const x2 = b.left - origin.left,
        y2 = b.top + b.height / 2 - origin.top;
      let path, labelX, labelY;
      if (window.matchMedia("(max-width: 520px)").matches) {
        const center = a.left + a.width / 2 - origin.left;
        const start = sourceColumn.bottom - origin.top,
          end = b.top - origin.top;
        const targetCenter = b.left + b.width / 2 - origin.left;
        if (end > start)
          path = `M${center} ${start} V${(start + end) / 2} H${targetCenter} V${end - 3}`;
        else
          path = `M${a.right - origin.left} ${y1} H${origin.width - 7} V${y2} H${b.right - origin.left + 3}`;
        labelX = center;
        labelY = (start + end) / 2;
      } else if (
        sourceNode.closest(".lane") ===
        document.getElementById(item.target).closest(".lane")
      ) {
        const targetColumn = box(
          document.getElementById(item.target).closest(".activity-column"),
        );
        const routeY =
          Math.max(sourceColumn.bottom, targetColumn.bottom) - origin.top + 24;
        path = `M${x1} ${y1} H${x1 + 9} V${routeY} H${x2 - 9} V${y2} H${x2 - 3}`;
        labelX = (x1 + x2) / 2;
        labelY = routeY;
      } else {
        const mid = (x1 + x2) / 2;
        const upperNode =
          a.top < b.top ? sourceNode : document.getElementById(item.target);
        const laneBottom = box(upperNode.closest(".lane")).bottom - origin.top;
        path = `M${x1} ${y1} H${mid} V${y2} H${x2 - 3}`;
        labelX = mid;
        labelY = laneBottom - 30;
      }
      paths.push(
        `<path class="edge-line" d="${path}" marker-end="url(#arrow)"/><path class="edge-hit" data-edge="${esc(item.id)}" d="${path}"><title>${esc(item.label)}</title></path>`,
      );
      labels.push(
        `<button class="edge-tag" data-edge="${esc(item.id)}" style="left:${labelX}px;top:${labelY}px;transform:translate(-50%,-50%)">${esc(item.label)}</button>`,
      );
    });
    feeds.forEach((feed, index) => {
      if (!feed.target) return;
      const element = document.getElementById(`input-feed-${index}`);
      const a = box(element);
      const b = box(document.getElementById(feed.target.id));
      if (!a || !b) return;
      const cards = [...element.querySelectorAll(".input-card")].map(box);
      const x1 = a.left + Math.min(a.width / 2, 100) - origin.left,
        y1 = a.bottom - origin.top;
      const x2 = b.left + b.width / 2 - origin.left,
        y2 = b.top - origin.top;
      const y = y1 + Math.min(20, (y2 - y1) / 2);
      const label = feed.scope === "run" ? "Run inputs" : "Inputs used";
      const connection = (path) => {
        paths.push(
          `<path class="input-line" data-input-scope="${feed.scope}" d="${path}" marker-end="url(#arrow)"/><path class="edge-hit" data-input-connection="${index}" d="${path}"><title>${label}</title></path>`,
        );
      };
      if (
        cards.length &&
        element.closest(".input-lane").dataset.expanded === "false"
      ) {
        const mobile = window.matchMedia("(max-width: 520px)").matches;
        // Join the supplied set before the consumer; these are not separate activities.
        const railY = y1 + 10;
        const railX =
          Math.max(...cards.map((card) => card.right)) - origin.left + 8;
        cards.forEach((card) => {
          const cx = card.left + card.width / 2 - origin.left;
          paths.push(
            `<path class="input-line" d="${mobile ? `M${card.right - origin.left} ${card.top + card.height / 2 - origin.top} H${railX} V${railY} H${x2}` : `M${cx} ${card.bottom - origin.top} V${railY} H${x2}`}"/>`,
          );
        });
        connection(`M${x2} ${railY} V${y2 - 3}`);
      } else {
        connection(`M${x1} ${y1} V${y} H${x2} V${y2 - 3}`);
      }
      labels.push(
        `<button class="input-edge-tag" data-input-connection="${index}" style="left:${x2 + 12}px;top:${y1 + 10}px;transform:translateY(-50%)" aria-label="${label}: ${esc(feed.target.title)}">${label}</button>`,
      );
    });
    document.getElementById("paths").innerHTML = paths.join("");
    document.getElementById("edge-labels").innerHTML = labels.join("");
  }
  new ResizeObserver(drawEdges).observe(diagram);
  drawEdges();

  const dialog = document.getElementById("detail");
  let current,
    history = [];
  const paragraph = (value) => `<p>${esc(value)}</p>`;
  const tables = (items, subject) =>
    items
      .map((table) => {
        const content = `<table><thead><tr>${table.columns.map((value) => `<th scope="col">${esc(value)}</th>`).join("")}</tr></thead><tbody>${table.rows.map((row) => `<tr>${row.map((value) => `<td>${esc(value)}</td>`).join("")}</tr>`).join("")}</tbody></table>${table.source && table.source !== subject ? `<button class="source-button" data-document="${esc(table.source)}">Source: ${esc(doc(table.source)?.title || "Supporting document")}</button>` : ""}`;
        return table.collapsed
          ? `<details class="record-table"><summary>${esc(table.title)} <span>${table.rows.length}</span></summary>${content}</details>`
          : `<section><h3>${esc(table.title)}</h3>${content}</section>`;
      })
      .join("");
  const documentList = (ids) =>
    `<div>${ids.map(documentButton).join("")}</div>`;
  const readableDocument = (item) =>
    `<div class="readable-document" data-document-text="${esc(item.id)}"></div>`;
  const evidenceContent = (item) => {
    if (viewerDocuments[item.id]) return pdfViewer(item);
    if (viewerModels[item.id]) return modelViewer(item, "detail-model-viewer");
    if (item.media_type.startsWith("image/") && localPath(item))
      return image(item);
    if (item.source_text) return readableDocument(item);
    return (
      item.paragraphs.map(paragraph).join("") + tables(item.tables, item.id)
    );
  };
  const sourceContext = (item) => {
    if (!item.source_url) return "";
    let source;
    try {
      source = new URL(item.source_url);
    } catch {
      return "";
    }
    if (!["http:", "https:"].includes(source.protocol)) return "";
    return `<p class="evidence-source">Retrieved reference <a href="${esc(source.href)}" target="_blank" rel="noopener noreferrer">${esc(source.hostname)}</a>${item.retrieved_at ? ` / ${esc(date(item.retrieved_at))}` : ""} <button class="source-button" data-document="${esc(item.source_manifest_id)}">Source record</button></p>`;
  };
  const assumptionList = (items, citations = false, selected = "") =>
    `<ul class="assumption-list">${items.map((item) => `<li data-assumption-row="${esc(item.id)}"${item.id === selected ? ' class="cited-statement"' : ""}><p>${esc(item.text)}</p>${citations ? `<button class="source-button" data-document="${esc(item.source_document_id)}" data-assumption="${esc(item.id)}">Source: ${esc(doc(item.source_document_id)?.title || "Recorded document")}</button>` : ""}</li>`).join("")}</ul>`;
  function inputGroups(query = "") {
    const matching = inputs.filter((item) =>
      `${item.title} ${item.name} ${item.group}`
        .toLowerCase()
        .includes(query.toLowerCase().trim()),
    );
    return matching.length
      ? [...groupOrder, "Reassembled context"]
          .map((group) => {
            const items = matching.filter((item) =>
              group === "Reassembled context"
                ? item.reconstructed
                : !item.reconstructed && item.group === group,
            );
            return items.length
              ? `<details class="input-group"${inputs.length <= 8 || query ? " open" : ""}><summary>${esc(group)} <span>${items.length}</span></summary>${items.map(inputButton).join("")}</details>`
              : "";
          })
          .join("")
      : '<p class="input-missing">No matching inputs.</p>';
  }

  function openView(view, push = true) {
    if (push && dialog.open && current) history.push(current);
    if (!dialog.open) history = [];
    current = view;
    let title = "",
      subtitle = "",
      body = "";
    if (view.type === "input-connection") {
      const feed = feeds[view.index];
      if (!feed) return;
      title = feed.scope === "run" ? "Run inputs" : "Inputs used";
      subtitle = feed.scope === "run" ? "Workflow entry" : feed.target.title;
      body =
        feed.scope === "run"
          ? "<p>These inputs belong to this run. The connector marks the start of the recorded process; activity-specific consumption was not retained for these inputs.</p>"
          : `<p>Recorded inputs used by ${esc(feed.target.title)}.</p>`;
      body += feed.inputs.map(inputButton).join("");
      if (feed.target)
        body += `<button class="source-button" data-step="${esc(feed.target.id)}">${feed.scope === "run" ? "First recorded activity" : "Consuming activity"}: ${esc(feed.target.title)}</button>`;
    } else if (view.type === "inputs") {
      title = reconstructedInputs.length
        ? "Run inputs & context"
        : "Run inputs";
      subtitle = inputCounts;
      body = `${inputs.length > 8 ? `<label class="input-search">Find an input<input type="search" data-input-search placeholder="Name or type" autocomplete="off" value="${esc(view.query || "")}"></label>` : ""}<div id="input-groups">${inputGroups(view.query || "")}</div>`;
    } else if (view.type === "input") {
      const item = allInputs.find((value) => value.id === view.id);
      if (!item) return;
      title = item.title;
      subtitle = `${item.group} / ${inputStatus(item)}`;
      body = item.text ? `<p class="prompt-text">${esc(item.text)}</p>` : "";
      if (item.format_note)
        body += `<p class="activity-time">${esc(item.format_note)}</p>`;
      if (item.provenance)
        body += `<p class="activity-time">${esc(item.provenance)}</p>`;
      if (item.source_document_ids?.length)
        body += `<h3>Source documents</h3>${documentList(item.source_document_ids)}`;
      body += tables(item.tables, null);
      const original = doc(item.document_id);
      if (original) {
        if (
          /^image\/(png|jpeg|gif|webp|svg\+xml)$/.test(original.media_type) &&
          localPath(original)
        )
          body += image(original);
        body += documentList([original.id]);
      } else if (!item.text && !item.tables.length)
        body += `<p class="note">${item.identity_only ? "Only an input fingerprint was retained; the original content is unavailable." : "This input is referenced in the retained record, but its original content is not included in this package."}</p>`;
      if (!item.complete || item.redacted)
        body += `<p class="note">${item.redacted ? "This recorded input contains redactions." : "Only part of this input was retained."}</p>`;
      if (item.variant_ids?.length)
        body += `<details class="input-formats"><summary>Editable source</summary><p class="activity-time">The PNG was rendered from the SVG for image upload. They are two formats of the same sketch, not separate design inputs.</p>${item.variant_ids
          .map((id) => allInputs.find((input) => input.id === id))
          .filter(Boolean)
          .map(inputButton)
          .join("")}</details>`;
      if (item.reference)
        body += `<details><summary>Recorded reference</summary><p class="prompt-text">${esc(item.reference)}</p></details>`;
      if (item.source_document_id)
        body += `<button class="source-button" data-document="${esc(item.source_document_id)}">Source: ${esc(doc(item.source_document_id)?.title || "Supporting document")}</button>`;
    } else if (view.type === "run-files") {
      title = "Run-level files";
      subtitle = "Producing activity not recorded";
      body = documentList(runDocuments.map((item) => item.id));
    } else if (
      view.type === "step" ||
      view.type === "step-files" ||
      view.type === "step-inputs"
    ) {
      const item = step(view.id);
      if (!item) return;
      const iteration = Math.min(
        view.iteration ?? item.attempts.length - 1,
        item.attempts.length - 1,
      );
      const attempt = item.attempts[iteration];
      const filesOnly = view.type === "step-files";
      const inputsOnly = view.type === "step-inputs";
      const activityInputs = inputs.filter((input) =>
        (attempt?.input_ids || []).includes(input.id),
      );
      const inputDocuments = attempt?.input_documents || [];
      title = filesOnly
        ? "Documents & outputs"
        : inputsOnly
          ? "Inputs used"
          : item.title;
      subtitle = filesOnly || inputsOnly ? item.title : item.owner;
      if (!filesOnly && !inputsOnly)
        body =
          item.objective ||
          (item.summary && item.summary !== "Recorded workflow activity.")
            ? `<p class="activity-purpose">${esc(item.objective || item.summary)}</p>`
            : "";
      if (item.attempts.length > 1) {
        body += `<div class="attempts" aria-label="Activity iterations">${item.attempts.map((value, index) => `<button data-iteration="${index}" aria-pressed="${iteration === index}">Iteration ${index + 1} / ${esc(state(value.state))}</button>`).join("")}</div>`;
      }
      body += `<p class="activity-time">${esc(state(attempt?.state))} / ${esc(date(attempt?.completed_at || attempt?.started_at))}</p>`;
      if (inputsOnly) {
        body +=
          activityInputs.map(inputButton).join("") +
          documentList(inputDocuments);
        if (!activityInputs.length && !inputDocuments.length)
          body +=
            '<p class="note">The consumed inputs were not retained for this activity.</p>';
      } else if (filesOnly) {
        body += documentList(attempt?.documents || item.documents);
        body += `<button class="source-button" data-step="${esc(item.id)}" data-step-iteration="${iteration}">View activity details</button>`;
      } else {
        const files = (attempt?.documents || item.documents)
          .map(doc)
          .filter(Boolean);
        const geometry = (attempt?.geometry || []).filter(
          (value) => viewerModels[value.document_id],
        );
        const evidenceFiles = [
          ...new Set([
            ...geometry.map((value) => value.document_id),
            ...files.map((value) => value.id),
          ]),
        ]
          .map(doc)
          .filter(Boolean);
        const visual =
          evidenceFiles.find((value) => value.id === view.evidenceId) ||
          (geometry.length ? doc(geometry[0].document_id) : null) ||
          files.find((value) => viewerModels[value.id]) ||
          files.find((value) => viewerDocuments[value.id]) ||
          files.find(
            (value) => value.review_visualization && localPath(value),
          ) ||
          files.find(
            (value) =>
              value.media_type.startsWith("image/") && localPath(value),
          ) ||
          files.find(
            (value) => value.source_text && /\.md$/i.test(value.name),
          ) ||
          files.find((value) => value.paragraphs.length || value.tables.length);
        subtitle = [
          item.software,
          state(attempt?.state),
          Number.isFinite(attempt?.duration_ms)
            ? duration(attempt.duration_ms)
            : null,
        ]
          .filter(Boolean)
          .join(" / ");
        body += '<div class="activity-review">';
        if (visual) {
          const association = geometry.find(
            (value) => value.document_id === visual.id,
          );
          const origin =
            association?.relation === "later_run_result"
              ? `Later CAD result / ${step(association.step_id)?.title}`
              : association?.relation === "inspected"
                ? "Geometry inspected in this activity"
                : association
                  ? "Geometry produced in this activity"
                  : "";
          body += `<section class="activity-evidence" aria-label="Activity evidence"><div class="evidence-heading"><label>${association ? "Geometry" : "Evidence"} <select data-activity-evidence aria-label="Activity evidence">${evidenceFiles.map((value) => `<option value="${esc(value.id)}"${value.id === visual.id ? " selected" : ""}>${esc(value.title)}</option>`).join("")}</select></label><button class="source-button" data-document="${esc(visual.id)}">Open document</button></div>${association ? `<p class="geometry-origin">${esc(origin)}${association.step_id && association.step_id !== item.id ? ` <button class="source-button" data-step="${esc(association.step_id)}">View producing activity</button>` : ""}${association.source_id ? ` <button class="source-button" data-document="${esc(association.source_id)}">Source record</button>` : ""}</p>` : ""}${sourceContext(visual)}${evidenceContent(visual) || documentList([visual.id])}${association && attempt.geometry_note ? `<p class="geometry-note">${esc(attempt.geometry_note)}</p>` : ""}</section>`;
        }
        body +=
          '<section class="activity-account" aria-label="Engineering account"><h3>Inputs</h3>';
        const used =
          activityInputs.map(inputButton).join("") +
          documentList(inputDocuments);
        body +=
          activityInputs.length || inputDocuments.length
            ? used
            : '<p class="activity-time">Run-level input context; individual consumption was not captured.</p>' +
              suppliedInputs.slice(0, 3).map(inputButton).join("");
        const actions = attempt?.research_actions || [];
        body += "<h3>Work performed</h3>";
        if (attempt?.operations?.length)
          body += `<ol class="engineering-actions">${attempt.operations.map((operation) => `<li><p>${esc(operation.text)}</p><button class="source-button" data-document="${esc(operation.source)}">Source record</button></li>`).join("")}</ol>`;
        else if (actions.length)
          body += `<ul class="engineering-actions">${actions.map((action) => `<li><strong>${esc(action.title)}</strong><p>${action.documents.length} references retained.</p>${action.documents.map((id) => `<button class="source-button" data-select-evidence="${esc(id)}">${esc(doc(id).title)}</button>`).join("")}</li>`).join("")}</ul><p class="activity-time">From the retained retrieval records; not a complete tool-call transcript.</p>`;
        else if (item.paragraphs?.length)
          body += item.paragraphs.map(paragraph).join("");
        else
          body +=
            '<p class="activity-time">The retained results are shown alongside. A detailed operation account was not included in this record.</p>';
        const account = files.find(
          (value) =>
            value.source_text &&
            /\.md$/i.test(value.name) &&
            value.id !== visual?.id,
        );
        const outputs = [
          account,
          ...files.filter(
            (value) =>
              value.id !== account?.id &&
              value.origin !== "Retrieved reference",
          ),
        ].filter(Boolean);
        body +=
          "<h3>Outputs</h3>" +
          outputs
            .slice(0, 3)
            .map(
              (value) =>
                `<button class="source-button" data-select-evidence="${esc(value.id)}">${esc(value.title)}</button>`,
            )
            .join("");
        body += "</section></div>";
        if (account)
          body += `<section class="activity-report"><h3>${esc(account.title)}</h3>${readableDocument(account)}</section>`;
        if (item.sections?.length)
          body += tables(
            item.sections.filter(
              (section) =>
                !visual?.tables.some(
                  (table) =>
                    table.source === section.source &&
                    table.title === section.title,
                ),
            ),
            null,
          );
        if (attempt?.assumptions?.length)
          body += `<details class="assumptions-detail"${view.assumptionsOpen ? " open" : ""}><summary>Recorded design assumptions</summary><p class="activity-time">Recorded in this activity's outputs; approval is not implied.</p>${assumptionList(attempt.assumptions, true)}</details>`;
        body += `<details class="execution-record"><summary>Execution details</summary><h3>Tool &amp; execution</h3><dl class="execution-facts"><div><dt>Software used</dt><dd>${esc(item.software || "Not recorded")}</dd></div><div><dt>Software version</dt><dd>${esc(item.software_version || "Not recorded")}</dd></div><div><dt>Recorded activity passes</dt><dd>${item.attempts.length}</dd></div><div><dt>Elapsed time / selected pass</dt><dd>${esc(duration(attempt?.duration_ms))}</dd></div></dl>`;
        if (item.software_source)
          body += `<button class="source-button" data-document="${esc(item.software_source)}">Execution source: ${esc(doc(item.software_source)?.title)}</button>`;
        if (item.software_note)
          body += `<p class="activity-time">${esc(item.software_note)}</p>`;
        body += `<details class="execution-record"><summary>Recorded execution</summary>${attempt?.events?.length ? `<ol class="execution-events">${attempt.events.map((event) => `<li>${esc(event.label)}<time>${esc(date(event.at, true))}</time></li>`).join("")}</ol><p class="activity-time">Source: saved execution record</p>` : '<p class="activity-time">Detailed execution events were not retained.</p>'}`;
        if (attempt?.operations?.length)
          body += `<h3>Reported operations</h3><ol class="execution-events">${attempt.operations.map((operation) => `<li>${esc(operation.text)}</li>`).join("")}</ol>${[...new Set(attempt.operations.map((operation) => operation.source))].map((id) => `<button class="source-button" data-document="${esc(id)}">Source: ${esc(doc(id)?.title)}</button>`).join("")}`;
        body +=
          '<p class="activity-time">Internal tool-call retries and CAD revision counts were not retained. Activity passes are not a count of internal design iterations.</p>';
        if (r.ai_usage?.models?.length)
          body += `<h3>Run-level AI usage</h3><p class="activity-time">Recorded routing alias: ${esc(r.ai_usage.models.join(", "))}. Underlying model and version were not retained.</p><p class="activity-time">${esc(r.ai_usage.request_count ?? "Unknown")} requests across the whole run, not this activity's revision count.</p>`;
        if (typeof item.prompt === "string")
          body += `<details><summary>Recorded task instructions</summary><p class="prompt-text">${esc(item.prompt)}</p></details>`;
        body += "</details>";
        body += "</details>";
        body += `<details class="activity-files"><summary>All ${files.length} files${item.attempts.length > 1 ? ` / iteration ${iteration + 1}` : ""}</summary>${documentList(attempt?.documents || item.documents)}</details>`;
        if (item.source_note)
          body += `<p class="note">${esc(item.source_note)}</p>`;
      }
    } else if (view.type === "edge") {
      const item = r.edges.find((value) => value.id === view.id);
      if (!item) return;
      title = item.label;
      subtitle = `${step(item.source)?.title} to ${step(item.target)?.title}`;
      body =
        paragraph(item.summary) +
        "<h3>Transferred information</h3>" +
        documentList(item.documents);
      if (item.traversals.length)
        body += `<h3>Recorded passages</h3><ol>${item.traversals.map((value, index) => `<li>Pass ${index + 1}${value.state ? ` / ${esc(state(value.state))}` : ""}</li>`).join("")}</ol>`;
      else
        body +=
          '<p class="note">This handoff is supported by the retained records. Separate connection-traversal events were not retained.</p>';
    } else {
      const item = doc(view.id);
      if (!item) return;
      title = item.title;
      subtitle = `${item.origin || "Retained file"} / ${kind(item)}`;
      if (viewerDocuments[item.id]) body += pdfViewer(item);
      body += sourceContext(item);
      const producers = r.steps.filter((value) =>
        value.documents.includes(item.id),
      );
      const producer = producers.length === 1 ? producers[0] : null;
      const sourceIterations = producer
        ? producer.attempts.flatMap((attempt, index) =>
            attempt.documents.includes(item.id) ? [index] : [],
          )
        : [];
      const sourceIteration =
        sourceIterations.length === 1 ? sourceIterations[0] : -1;
      const sourceAttempt = producer?.attempts[sourceIteration];
      if (producer)
        body += `<p class="activity-time">${item.source_url ? "Retrieved during" : "Recorded with"} ${esc(producer.title)}${producer.attempts.length > 1 && sourceIteration >= 0 ? ` / pass ${sourceIteration + 1}` : ""}.</p>`;
      if (item.application)
        body += `<p class="activity-time">Package producer: ${esc(item.application)} (recorded in package metadata).</p>`;
      if (item.source_text) body += readableDocument(item);
      if (item.assumptions?.length) {
        body += `<section class="assumption-source" aria-label="Recorded design assumptions"><h3>Recorded design assumptions</h3><p class="activity-time">Verbatim from this record; approval is not implied.</p>`;
        if (producer)
          body += `<button class="source-button" data-step="${esc(producer.id)}"${sourceIteration >= 0 ? ` data-step-iteration="${sourceIteration}"` : ""}>Recorded during: ${esc(producer.title)}</button><p class="activity-time">${sourceIterations.length > 1 ? "Recorded in multiple iterations of this activity." : `${sourceAttempt?.completed_at ? "Activity completed" : "Activity started"}: ${esc(date(sourceAttempt?.completed_at || sourceAttempt?.started_at))}`}</p>`;
        body +=
          assumptionList(item.assumptions, false, view.assumption) +
          "</section>";
        const citedInputs = inputs.filter((input) =>
          (item.input_ids || []).includes(input.id),
        );
        if (citedInputs.length)
          body += `<section class="source-inputs"><h3>Inputs cited by this record</h3>${citedInputs.map(inputButton).join("")}</section>`;
      }
      const isImage = /^image\/(png|jpeg|gif|webp|svg\+xml)$/.test(
        item.media_type,
      );
      if (isImage && localPath(item)) body += image(item);
      if (item.review_visualization) {
        if (item.provenance)
          body += `<p class="visualization-provenance">${esc(item.provenance)}</p>`;
        if (item.source_document_ids?.length)
          body += `<h3>Source evidence</h3>${documentList(item.source_document_ids)}`;
      }
      if (/\.stl$/i.test(item.name) && viewerModels[item.id]) {
        body += modelViewer(item, "detail-model-viewer");
        body +=
          '<p class="activity-time">Drag to rotate. Scroll or pinch to zoom. This viewer uses the retained STL geometry embedded in the report.</p>';
      } else if (/\.(stl|step|stp|3mf)$/i.test(item.name)) {
        const preview =
          !item.name.endsWith(".3mf") &&
          pictures.find((value) => value.name === "mesh-preview.png");
        if (preview && item.name !== "source_mesh.stl")
          body +=
            image(preview) +
            `<p class="activity-time">${item.name.endsWith(".3mf") ? "Slicer model thumbnail, not a layer-by-layer view." : "Generated model after digital mesh cleanup."}</p>`;
        body +=
          '<p class="note">An interactive view is not available for this retained model. Open the original file in a compatible CAD or manufacturing viewer.</p>';
      }
      if (item.assumptions?.length && item.paragraphs.length)
        body += "<h3>Recorded operations</h3>";
      body +=
        item.paragraphs.map(paragraph).join("") + tables(item.tables, item.id);
      if (
        !item.tables.length &&
        !item.source_text &&
        !viewerDocuments[item.id] &&
        !isImage &&
        !/\.(stl|step|stp|3mf)$/i.test(item.name)
      )
        body += paragraph(
          item.reconstructed
            ? "This file was reassembled for review from the verified source inputs."
            : "The original supporting file is retained below.",
        );
      if (item.viewer_unavailable_reason)
        body += paragraph(item.viewer_unavailable_reason);
      const path = localPath(item);
      body += path
        ? `<a class="download" href="${esc(path)}" download="${esc(item.name)}">${item.reconstructed ? "Download reassembled context" : `Download original ${esc(item.name.match(/\.(pdf|stl|step|stp|3mf|png|svg)$/i)?.[1]?.toUpperCase() || "file")}`}</a><p class="activity-time">${esc(item.name)}</p>`
        : `<p class="note">The ${item.reconstructed ? "reassembled" : "original"} file is not included in this report-only package or was unavailable at export.</p>`;
      if (producer)
        body += `<button class="source-button" data-step="${esc(producer.id)}" data-step-iteration="${Math.max(
          0,
          producer.attempts.findIndex((attempt) =>
            attempt.documents.includes(item.id),
          ),
        )}">Activity: ${esc(producer.title)}</button>`;
    }
    disposeViewers(dialog);
    dialog.classList.toggle(
      "engineering-detail",
      view.type === "step" ||
        !!viewerDocuments[view.id] ||
        !!doc(view.id)?.source_text,
    );
    dialog.innerHTML = `<div class="detail-head"><div>${history.length ? '<button class="source-button" data-back>Back</button>' : ""}<h2 id="detail-title">${esc(title)}</h2><p>${esc(subtitle)}</p></div><button class="icon-button" data-close aria-label="Close details" title="Close details">&#215;</button></div><div class="detail-body">${body}</div>`;
    if (!dialog.open) dialog.showModal();
    mountViewers(dialog);
    dialog.scrollTop = 0;
    dialog.querySelector("[data-close]").focus({ preventScroll: true });
    const cited = dialog.querySelector(".cited-statement");
    if (cited) {
      const bottom = cited.getBoundingClientRect().bottom;
      if (bottom > window.innerHeight)
        dialog.scrollTop += bottom - window.innerHeight + 24;
    }
  }
  document.addEventListener("click", (event) => {
    const target = event.target.closest(
      "[data-step],[data-document],[data-select-evidence],[data-edge],[data-close],[data-back],[data-iteration],[data-input],[data-inputs],[data-input-connection],[data-step-files],[data-step-inputs],[data-run-files],[data-lane-toggle],[data-fit-diagram]",
    );
    if (!target) return;
    if (target.dataset.selectEvidence && current?.type === "step") {
      openView(
        { ...current, evidenceId: target.dataset.selectEvidence },
        false,
      );
      return;
    }
    if (target.hasAttribute("data-fit-diagram")) {
      setZoom(100);
      setZoom(
        Math.min(
          100,
          Math.floor(
            (diagram.parentElement.clientWidth /
              diagram.getBoundingClientRect().width) *
              100,
          ),
        ),
      );
      diagram.parentElement.scrollLeft = 0;
      return;
    }
    if (target.hasAttribute("data-lane-toggle")) {
      const expanded = target.getAttribute("aria-expanded") !== "true";
      target.setAttribute("aria-expanded", String(expanded));
      target.title = `${expanded ? "Collapse" : "Expand"} ${target.lastElementChild.textContent}`;
      target.closest(".lane,.input-lane").dataset.expanded = String(expanded);
      drawEdges();
      return;
    }
    if (target.hasAttribute("data-close")) {
      disposeViewers(dialog);
      dialog.close();
      current = null;
      return;
    }
    if (target.hasAttribute("data-back")) {
      const previous = history.pop();
      if (previous) openView(previous, false);
      return;
    }
    if (target.hasAttribute("data-iteration")) {
      openView(
        { ...current, iteration: Number(target.dataset.iteration) },
        false,
      );
      return;
    }
    if (target.dataset.step)
      openView({
        type: "step",
        id: target.dataset.step,
        iteration: target.hasAttribute("data-step-iteration")
          ? Number(target.dataset.stepIteration)
          : undefined,
      });
    if (target.dataset.document) {
      if (target.closest(".assumptions-detail") && current)
        current.assumptionsOpen = true;
      openView({
        type: "document",
        id: target.dataset.document,
        assumption: target.dataset.assumption,
      });
    }
    if (target.dataset.edge)
      openView({ type: "edge", id: target.dataset.edge });
    if (target.dataset.input)
      openView({ type: "input", id: target.dataset.input });
    if (target.hasAttribute("data-input-connection"))
      openView({
        type: "input-connection",
        index: Number(target.dataset.inputConnection),
      });
    if (target.hasAttribute("data-inputs")) openView({ type: "inputs" });
    if (target.dataset.stepFiles)
      openView({ type: "step-files", id: target.dataset.stepFiles });
    if (target.dataset.stepInputs)
      openView({ type: "step-inputs", id: target.dataset.stepInputs });
    if (target.hasAttribute("data-run-files")) openView({ type: "run-files" });
  });
  document.addEventListener("input", (event) => {
    if (event.target.matches("[data-diagram-zoom]"))
      setZoom(Number(event.target.value));
    if (event.target.matches("[data-input-search]")) {
      current.query = event.target.value;
      document.getElementById("input-groups").innerHTML = inputGroups(
        current.query,
      );
    }
  });
  document.addEventListener("change", (event) => {
    if (
      event.target.matches("[data-activity-evidence]") &&
      current?.type === "step"
    )
      openView({ ...current, evidenceId: event.target.value }, false);
  });
  dialog.addEventListener("close", () => disposeViewers(dialog));
})();
