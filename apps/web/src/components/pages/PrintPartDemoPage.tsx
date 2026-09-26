import { useEffect, useMemo, useRef, useState } from "react";
import * as THREE from "three";
import { OrbitControls } from "three/addons/controls/OrbitControls.js";
import { STLLoader } from "three/addons/loaders/STLLoader.js";
import {
  workspaceService,
  type WorkspaceEngineeringResult,
  type WorkspaceWorkflowRunEvent,
  type WorkspaceWorkflowSourceRun,
} from "../../services/workspace-service";
import { workspaceContentUrl } from "../../services/viewer-panel/providers/workspace-content-url";
import "./PrintPartDemoPage.css";

interface Props {
  sessionId: string;
  workspaceId: string;
  onOpenWorkflow?: (path: string) => void;
  onClose: () => void;
}

interface Artifact {
  path: string;
  sha256: string;
}

function findArtifact(
  results: WorkspaceEngineeringResult[] | undefined,
  artifactRoot: string,
  filename: string,
): Artifact | null {
  if (!artifactRoot) return null;
  const representations = results?.flatMap((result) => result.representations ?? []) ?? [];
  const matches = representations.filter((rep) =>
    rep.kind === "workspace_file" && rep.location === `${artifactRoot}/${filename}` &&
    typeof rep.sha256 === "string" && /^[0-9a-f]{64}$/.test(rep.sha256),
  );
  return matches.length === 1 ? { path: matches[0].location, sha256: matches[0].sha256! } : null;
}

function PartPreview({ sessionId, path }: { sessionId: string; path: string }) {
  const host = useRef<HTMLDivElement>(null);
  const [error, setError] = useState("");
  useEffect(() => {
    const element = host.current;
    if (!element) return;
    let disposed = false;
    let renderer: THREE.WebGLRenderer | null = null;
    let geometry: THREE.BufferGeometry | null = null;
    let controls: OrbitControls | null = null;
    let resize: ResizeObserver | null = null;
    let frame = 0;
    void fetch(workspaceContentUrl(path, sessionId)).then((response) => {
      if (!response.ok) throw new Error("Mesh unavailable");
      return response.arrayBuffer();
    }).then((bytes) => {
      if (disposed) return;
      geometry = new STLLoader().parse(bytes);
      geometry.computeVertexNormals();
      geometry.computeBoundingBox();
      const box = geometry.boundingBox!;
      const center = box.getCenter(new THREE.Vector3());
      const size = box.getSize(new THREE.Vector3());
      geometry.translate(-center.x, -center.y, -center.z);
      const scene = new THREE.Scene();
      scene.background = new THREE.Color(0x0b1321);
      scene.add(new THREE.HemisphereLight(0xffffff, 0x374151, 2));
      const key = new THREE.DirectionalLight(0xffffff, 2);
      key.position.set(1, 2, 3);
      scene.add(key);
      const part = new THREE.Mesh(geometry, new THREE.MeshStandardMaterial({ color: 0xbce7f7, metalness: 0.1, roughness: 0.45, side: THREE.DoubleSide }));
      part.rotation.x = -Math.PI / 2;
      scene.add(part);
      const span = Math.max(size.x, size.y, size.z, 1);
      const grid = new THREE.GridHelper(span * 1.6, 16, 0x64748b, 0x243248);
      grid.position.y = -Math.max(size.z, 1) / 2 - 1;
      scene.add(grid);
      const camera = new THREE.PerspectiveCamera(45, 1, 0.1, span * 20);
      camera.position.set(span * 1.6, span * 1.2, span * 1.6);
      renderer = new THREE.WebGLRenderer({ antialias: true });
      renderer.setPixelRatio(Math.min(window.devicePixelRatio || 1, 2));
      element.replaceChildren(renderer.domElement);
      controls = new OrbitControls(camera, renderer.domElement);
      controls.enableDamping = true;
      const draw = () => {
        if (disposed) return;
        controls?.update();
        renderer?.render(scene, camera);
        frame = requestAnimationFrame(draw);
      };
      resize = new ResizeObserver(() => {
        const width = Math.max(1, element.clientWidth);
        const height = Math.max(1, element.clientHeight);
        camera.aspect = width / height;
        camera.updateProjectionMatrix();
        renderer?.setSize(width, height);
      });
      resize.observe(element);
      draw();
    }).catch(() => { if (!disposed) setError("The mesh preview could not be opened."); });
    return () => {
      disposed = true;
      cancelAnimationFrame(frame);
      resize?.disconnect();
      controls?.dispose();
      geometry?.dispose();
      renderer?.dispose();
      element.replaceChildren();
    };
  }, [sessionId, path]);
  return <div className="print-demo__model" ref={host} role="img" aria-label="Rotatable 3D part preview">{error && <p role="alert">{error}</p>}</div>;
}

interface ToolpathLayer {
  index: number;
  z: number;
  model: number[][];
  support: number[][];
}

function ToolpathPreview({ sessionId, path, packageHash }: { sessionId: string; path: string; packageHash: string }) {
  const host = useRef<HTMLDivElement>(null);
  const lines = useRef<{ object: THREE.LineSegments; layer: number; kind: "model" | "support" }[]>([]);
  const [layers, setLayers] = useState<ToolpathLayer[]>([]);
  const [visibleThrough, setVisibleThrough] = useState(0);
  const [showModel, setShowModel] = useState(true);
  const [showSupport, setShowSupport] = useState(true);
  const [error, setError] = useState("");
  useEffect(() => {
    let active = true;
    void fetch(workspaceContentUrl(path, sessionId)).then((response) => {
      if (!response.ok) throw new Error("Toolpaths unavailable");
      return response.json();
    }).then((wrapper) => {
      const file = typeof wrapper.content === "string" ? JSON.parse(wrapper.content) : wrapper;
      const value = typeof file?.content?.[0]?.text === "string" ? JSON.parse(file.content[0].text) : file;
      if (value.format !== "wright.gcode.toolpaths.v1" || value.package_sha256 !== packageHash || !Array.isArray(value.layers) || !value.layers.length) {
        throw new Error("Toolpaths do not match the sliced package");
      }
      if (active) { setLayers(value.layers); setVisibleThrough(value.layers.length); }
    }).catch(() => { if (active) setError("The 3D toolpaths could not be opened. Review the sliced 3MF in Bambu Studio before printing."); });
    return () => { active = false; };
  }, [sessionId, path, packageHash]);
  useEffect(() => {
    const element = host.current;
    if (!element || !layers.length) return;
    let disposed = false;
    let frame = 0;
    const scene = new THREE.Scene();
    scene.background = new THREE.Color(0x0b1321);
    const all = layers.flatMap((layer) => [...layer.model, ...layer.support]);
    const bounds = { minX: Infinity, maxX: -Infinity, minY: Infinity, maxY: -Infinity };
    for (const [x1, y1, x2, y2] of all) {
      bounds.minX = Math.min(bounds.minX, x1, x2);
      bounds.maxX = Math.max(bounds.maxX, x1, x2);
      bounds.minY = Math.min(bounds.minY, y1, y2);
      bounds.maxY = Math.max(bounds.maxY, y1, y2);
    }
    const centerX = (bounds.minX + bounds.maxX) / 2;
    const centerY = (bounds.minY + bounds.maxY) / 2;
    const lowZ = Math.min(...layers.map((layer) => layer.z));
    const highZ = Math.max(...layers.map((layer) => layer.z));
    const centerZ = (lowZ + highZ) / 2;
    const span = Math.max(bounds.maxX - bounds.minX, bounds.maxY - bounds.minY, highZ - lowZ, 1);
    const materials = {
      model: new THREE.LineBasicMaterial({ color: 0x8fdbec, transparent: true, opacity: 0.65 }),
      support: new THREE.LineBasicMaterial({ color: 0xff9c62, transparent: true, opacity: 0.9 }),
    };
    const objects: typeof lines.current = [];
    for (const [position, layer] of layers.entries()) {
      for (const kind of ["model", "support"] as const) {
        const segments = layer[kind];
        if (!segments.length) continue;
        const vertices = new Float32Array(segments.length * 6);
        segments.forEach(([x1, y1, x2, y2], index) => {
          vertices.set([x1 - centerX, layer.z - centerZ, centerY - y1, x2 - centerX, layer.z - centerZ, centerY - y2], index * 6);
        });
        const geometry = new THREE.BufferGeometry();
        geometry.setAttribute("position", new THREE.BufferAttribute(vertices, 3));
        const object = new THREE.LineSegments(geometry, materials[kind]);
        scene.add(object);
        objects.push({ object, layer: position + 1, kind });
      }
    }
    lines.current = objects;
    const grid = new THREE.GridHelper(span * 1.4, 16, 0x52687a, 0x273b49);
    grid.position.y = lowZ - centerZ - 0.2;
    scene.add(grid);
    const camera = new THREE.PerspectiveCamera(45, 1, 0.1, span * 30);
    camera.position.set(span * 1.4, span * 1.15, span * 1.4);
    const renderer = new THREE.WebGLRenderer({ antialias: true });
    renderer.setPixelRatio(Math.min(window.devicePixelRatio || 1, 2));
    element.replaceChildren(renderer.domElement);
    const controls = new OrbitControls(camera, renderer.domElement);
    controls.enableDamping = true;
    const resize = new ResizeObserver(() => {
      camera.aspect = Math.max(1, element.clientWidth) / Math.max(1, element.clientHeight);
      camera.updateProjectionMatrix();
      renderer.setSize(Math.max(1, element.clientWidth), Math.max(1, element.clientHeight));
    });
    resize.observe(element);
    const draw = () => {
      if (disposed) return;
      controls.update();
      renderer.render(scene, camera);
      frame = requestAnimationFrame(draw);
    };
    draw();
    return () => {
      disposed = true;
      cancelAnimationFrame(frame);
      resize.disconnect();
      controls.dispose();
      objects.forEach(({ object }) => object.geometry.dispose());
      materials.model.dispose();
      materials.support.dispose();
      grid.geometry.dispose();
      (grid.material as THREE.Material).dispose();
      renderer.dispose();
      element.replaceChildren();
      lines.current = [];
    };
  }, [layers]);
  useEffect(() => {
    for (const item of lines.current) item.object.visible = item.layer <= visibleThrough && (item.kind === "model" ? showModel : showSupport);
  }, [layers, visibleThrough, showModel, showSupport]);
  const selected = layers[Math.max(0, visibleThrough - 1)];
  return <div className="print-demo__toolpath-wrap">
    <div className="print-demo__model" ref={host} role="img" aria-label="Rotatable 3D toolpaths for all sliced layers; model is blue and supports are orange" />
    {error && <p role="alert" className="print-demo__error">{error}</p>}
    {layers.length > 0 && <>
      <div className="print-demo__layer-controls"><label htmlFor="print-demo-layers">Layers 1–{visibleThrough} of {layers.length} · Z {selected?.z.toFixed(2)} mm</label><input id="print-demo-layers" type="range" min={1} max={layers.length} value={visibleThrough} onChange={(event) => setVisibleThrough(Number(event.target.value))} /></div>
      <div className="print-demo__legend"><label><input type="checkbox" checked={showModel} onChange={(event) => setShowModel(event.target.checked)} /> Model</label><label><input type="checkbox" checked={showSupport} onChange={(event) => setShowSupport(event.target.checked)} /> Supports</label></div>
    </>}
  </div>;
}

export function PrintPartDemoPage({ sessionId, workspaceId, onOpenWorkflow, onClose }: Props) {
  const startedAt = useRef(0);
  const currentStage = useRef("Preparing the request");
  const [prompt, setPrompt] = useState("");
  const [image, setImage] = useState<File | null>(null);
  const [targetMm, setTargetMm] = useState(50);
  const [busy, setBusy] = useState(false);
  const [printing, setPrinting] = useState(false);
  const [sent, setSent] = useState(false);
  const [error, setError] = useState("");
  const [errorDetails, setErrorDetails] = useState("");
  const [step, setStep] = useState("Describe the part");
  const [activity, setActivity] = useState<string[]>([]);
  const [elapsedSeconds, setElapsedSeconds] = useState(0);
  const [imagePreview, setImagePreview] = useState("");
  const [workflowPath, setWorkflowPath] = useState("");
  const [run, setRun] = useState<WorkspaceWorkflowSourceRun | null>(null);
  const [artifactRoot, setArtifactRoot] = useState("");
  const [printer, setPrinter] = useState<{
    status: string; progress: number | null; time_remaining_minutes: number | null;
    current_layer: number | null; total_layers: number | null;
  } | null>(null);
  const [printerError, setPrinterError] = useState("");
  const [cameraError, setCameraError] = useState(false);
  const [printerEnabled, setPrinterEnabled] = useState(false);
  const [sliceMetrics, setSliceMetrics] = useState<{ orientation_selected: string; estimated_seconds: number; filament_g: number; support_moves: number; preview_layer: number } | null>(null);
  const sourceFile = useMemo(() => findArtifact(run?.results, artifactRoot, "source_mesh.stl"), [run, artifactRoot]);
  const repairedFile = useMemo(() => findArtifact(run?.results, artifactRoot, "repaired_mesh.stl"), [run, artifactRoot]);
  const orientedFile = useMemo(() => findArtifact(run?.results, artifactRoot, "oriented_mesh.stl"), [run, artifactRoot]);
  const supportFile = useMemo(() => findArtifact(run?.results, artifactRoot, "support-preview.svg"), [run, artifactRoot]);
  const toolpathFile = useMemo(() => findArtifact(run?.results, artifactRoot, "toolpaths.json"), [run, artifactRoot]);
  const evidenceFile = useMemo(() => findArtifact(run?.results, artifactRoot, "slice-evidence.json"), [run, artifactRoot]);
  const repairReportFile = useMemo(() => findArtifact(run?.results, artifactRoot, "repair-model-report.json"), [run, artifactRoot]);
  const packageFile = useMemo(() => findArtifact(run?.results, artifactRoot, "slice_package.gcode.3mf"), [run, artifactRoot]);
  const hasPreview = Boolean(run?.status === "completed" && sourceFile && repairedFile && orientedFile && supportFile && toolpathFile && evidenceFile && packageFile);
  const [baseTrimMm, setBaseTrimMm] = useState(0);

  useEffect(() => {
    if (!image) { setImagePreview(""); return; }
    const url = URL.createObjectURL(image);
    setImagePreview(url);
    return () => URL.revokeObjectURL(url);
  }, [image]);

  useEffect(() => {
    if (!busy) return;
    const timer = window.setInterval(() => setElapsedSeconds(Math.floor((Date.now() - startedAt.current) / 1000)), 1000);
    return () => window.clearInterval(timer);
  }, [busy]);

  useEffect(() => {
    if (!evidenceFile) { setSliceMetrics(null); return; }
    let active = true;
    void fetch(workspaceContentUrl(evidenceFile.path, sessionId)).then((response) => {
      if (!response.ok) throw new Error("Slice evidence unavailable");
      return response.json();
    }).then((value) => {
      if (active) setSliceMetrics(typeof value.content === "string" ? JSON.parse(value.content) : null);
    }).catch(() => { if (active) setSliceMetrics(null); });
    return () => { active = false; };
  }, [evidenceFile?.path, sessionId]);

  useEffect(() => {
    if (!repairReportFile) { setBaseTrimMm(0); return; }
    let active = true;
    void fetch(workspaceContentUrl(repairReportFile.path, sessionId)).then((response) => response.json()).then((wrapper) => {
      const file = typeof wrapper.content === "string" ? JSON.parse(wrapper.content) : wrapper;
      const value = typeof file?.content?.[0]?.text === "string" ? JSON.parse(file.content[0].text) : file;
      const trim = value?.repair?.printable_base?.trimmed_mm;
      if (active) setBaseTrimMm(typeof trim === "number" && Number.isFinite(trim) ? trim : 0);
    }).catch(() => { if (active) setBaseTrimMm(0); });
    return () => { active = false; };
  }, [repairReportFile?.path, sessionId]);

  useEffect(() => {
    let active = true;
    void workspaceService.getPrintDemoCapabilities().then((value) => {
      if (active) setPrinterEnabled(value.printer_enabled);
    }).catch(() => { if (active) setPrinterEnabled(false); });
    return () => { active = false; };
  }, []);

  useEffect(() => {
    if (!sent) return;
    let active = true;
    const refresh = () => {
      void workspaceService.getPrintDemoPrinterStatus(sessionId).then((value) => {
        if (active) { setPrinter(value); setPrinterError(""); }
      }).catch((reason: unknown) => {
        if (active) setPrinterError(reason instanceof Error ? reason.message : "Printer status unavailable.");
      });
    };
    refresh();
    const timer = window.setInterval(refresh, 5000);
    return () => { active = false; window.clearInterval(timer); };
  }, [sent, sessionId]);

  const generate = async () => {
    if ((!prompt.trim() && !image) || busy) return;
    setBusy(true);
    setRun(null);
    setSent(false);
    setPrinter(null);
    setPrinterError("");
    setCameraError(false);
    setError("");
    setErrorDetails("");
    setActivity(["Preparing the request"]);
    startedAt.current = Date.now();
    currentStage.current = "Preparing the request";
    setElapsedSeconds(0);
    setStep("Preparing Wright workflow");
    try {
      let imagePath: string | null = null;
      if (image) {
        if (image.size > 4 * 1024 * 1024) throw new Error("Choose an image under 4 MiB.");
        imagePath = await workspaceService.uploadPrintDemoImage(sessionId, image);
        setActivity((current) => [...current, "Reference image uploaded"]);
      }
      const prepared = await workspaceService.preparePrintPartDemo(sessionId, prompt, imagePath, targetMm);
      if (prepared.workspace_id !== workspaceId) throw new Error("The prepared workflow belongs to another workspace.");
      setWorkflowPath(prepared.workflow_path);
      setArtifactRoot(prepared.artifact_root);
      setStep("Running Blender and Bambu Studio");
      currentStage.current = "Running Blender and Bambu Studio";
      setActivity((current) => [...current, "Saved a Wright workflow for this part"]);
      const result = await workspaceService.runWorkspaceWorkflowSource(
        sessionId, prepared.workflow_path, prepared.storage_digest,
        (event: WorkspaceWorkflowRunEvent) => {
          if (event.kind === "step_started" || event.kind === "task_progress" || event.kind === "operation_progress") {
            const message = event.task_title || event.message || "Running workflow";
            currentStage.current = message;
            setStep(message);
            setActivity((current) => current.at(-1) === message ? current : [...current, message].slice(-8));
          } else if (event.kind === "step_completed") {
            const message = `${event.task_title || "Step"} complete`;
            setActivity((current) => [...current, message].slice(-8));
          }
        },
      );
      if (result.workflow_path !== prepared.workflow_path || result.workspace_id !== workspaceId) {
        throw new Error("Wright returned a run for another workflow.");
      }
      setRun(result);
      setStep(result.status === "completed" ? "Review the part and slice" : "Workflow needs review");
      if (result.status === "completed") setActivity((current) => [...current, "3D model and sliced package ready"].slice(-8));
    } catch (reason) {
      const detail = reason instanceof Error ? reason.message : "The print workflow could not complete.";
      setErrorDetails(detail);
      setError(currentStage.current.toLowerCase().includes("slice") || currentStage.current.toLowerCase().includes("support")
        ? "Wright created the part, but Bambu Studio could not finish its slice. Open the saved workflow for the run details, then retry. Rounded parts need a small flat base to sit on the plate."
        : `Wright could not finish ${currentStage.current.toLowerCase()}. Open the saved workflow for the run details, then retry.`);
      setStep("Needs attention");
    } finally {
      setBusy(false);
    }
  };

  const print = async () => {
    if (!run?.run_id || !packageFile || !workflowPath || printing || sent) return;
    setPrinting(true);
    setError("");
    try {
      await workspaceService.printDemoPackage(sessionId, workflowPath, run.run_id, packageFile.sha256);
      setSent(true);
      setStep("Print sent to P1S");
    } catch (reason) {
      setError(reason instanceof Error ? reason.message : "The printer did not accept the job.");
      setStep("Check printer dispatch");
    } finally {
      setPrinting(false);
    }
  };

  return <div className="print-demo" data-testid="print-part-demo">
    <header className="print-demo__header">
      <div><span className="print-demo__eyebrow">WRIGHT · ADDITIVE MANUFACTURING</span><h1>Prompt to printed part</h1><p>Describe a part, review the generated mesh and supported slice, then start the P1S print.</p></div>
      <button type="button" className="print-demo__text-button" onClick={onClose}>Back to Workflows</button>
    </header>
    <div className="print-demo__grid">
      <section className="print-demo__card" aria-label="Part request">
        <span className="print-demo__step">01 / DESIGN REQUEST</span>
        <label htmlFor="print-demo-prompt">What part should Wright make?</label>
        <textarea id="print-demo-prompt" value={prompt} onChange={(event) => setPrompt(event.target.value)} placeholder="A replacement knob, 50 mm wide, with a 6 mm D-shaped shaft socket…" rows={6} disabled={busy} />
        <label htmlFor="print-demo-image">Reference image <small>(optional)</small></label>
        <input id="print-demo-image" type="file" accept="image/png,image/jpeg,image/gif,image/webp" onChange={(event) => setImage(event.target.files?.[0] ?? null)} disabled={busy} />
        {image && <div className="print-demo__image-preview">{imagePreview && <img src={imagePreview} alt="Uploaded part reference" />}<span className="print-demo__muted">{image.name}</span></div>}
        <label htmlFor="print-demo-size">Largest dimension · mm</label>
        <input id="print-demo-size" type="number" min={5} max={250} value={targetMm} onChange={(event) => setTargetMm(Number(event.target.value))} disabled={busy} />
        <button type="button" className="print-demo__primary" onClick={() => void generate()} disabled={busy || (!prompt.trim() && !image) || !Number.isFinite(targetMm) || targetMm < 5 || targetMm > 250}>{busy ? "Creating part…" : "Create printable part"}</button>
        <p className="print-demo__muted">Wright saves each request as its own workflow and runs Blender MCP, mesh repair MCP, and Bambu Studio CLI with the P1S profile.</p>
      </section>
      <section className="print-demo__card print-demo__result" aria-label="Part and slice review">
        <div className="print-demo__section-head"><span className="print-demo__step">02 / REVIEW</span><span className="print-demo__pill">{step}</span></div>
        {busy && <div className="print-demo__progress" role="status" aria-live="polite"><span className="print-demo__spinner" aria-hidden="true" /><div><strong>Wright is working · {Math.floor(elapsedSeconds / 60)}:{String(elapsedSeconds % 60).padStart(2, "0")}</strong><p>{step}</p></div></div>}
        {activity.length > 0 && <ol className="print-demo__activity" aria-label="Workflow progress">{activity.map((item, index) => <li key={`${index}-${item}`}>{item}</li>)}</ol>}
        {hasPreview ? <div className="print-demo__previews">
          <div><strong>Selected print orientation</strong><PartPreview sessionId={sessionId} path={orientedFile!.path} /><small>Drag to rotate · scroll to zoom</small></div>
          <div><strong>Full 3D toolpaths</strong><ToolpathPreview sessionId={sessionId} path={toolpathFile!.path} packageHash={packageFile!.sha256} /><small>Drag to rotate · scroll to zoom · use the slider to reveal layers. <a href={workspaceContentUrl(supportFile!.path, sessionId)} download>Download 2D layer image</a></small></div>
        </div> : <div className="print-demo__empty">{busy ? "The 3D part and toolpaths will appear when the engineering stages finish." : error ? "The print package is not ready yet. See the message below and open the saved workflow for details." : "The part and its slice will appear here."}</div>}
        {hasPreview && sliceMetrics && <p className="print-demo__file">Orientation: {sliceMetrics.orientation_selected.replaceAll("_", " ")} · Estimated time: {Math.ceil(sliceMetrics.estimated_seconds / 60)} min · Filament: {sliceMetrics.filament_g.toFixed(1)} g · Support moves: {sliceMetrics.support_moves}</p>}
        {hasPreview && baseTrimMm > 0 && <p className="print-demo__notice">Wright trimmed {baseTrimMm.toFixed(1)} mm from the underside to give this rounded part a flat print base. Review that change before printing.</p>}
        {hasPreview && <p className="print-demo__muted">Review functional surfaces and layer strength; the orientation comparison measures bed contact, supports, time, and filament.</p>}
        {hasPreview && <p className="print-demo__file">Mesh · <a href={workspaceContentUrl(sourceFile!.path, sessionId)} download>Source STL</a> · <a href={workspaceContentUrl(repairedFile!.path, sessionId)} download>Repaired STL</a> · <a href={workspaceContentUrl(orientedFile!.path, sessionId)} download>Selected STL</a> · <a href={workspaceContentUrl(evidenceFile!.path, sessionId)} download>Orientation comparison</a></p>}
        {packageFile && <p className="print-demo__file">Sliced 3MF · <a href={workspaceContentUrl(packageFile.path, sessionId)} download>Download package</a><br /><code>SHA-256 {packageFile.sha256.slice(0, 16)}…</code></p>}
        {workflowPath && <button type="button" className="print-demo__text-button" onClick={() => onOpenWorkflow?.(workflowPath)}>Open saved Wright workflow</button>}
        {error && <div className="print-demo__error" role="alert">{error}{errorDetails && <details><summary>Technical details</summary><pre>{errorDetails}</pre></details>}</div>}
      </section>
      <section className="print-demo__card print-demo__printer" aria-label="Print and monitor">
        <span className="print-demo__step">03 / PRINT & MONITOR</span>
        <h2>Bambu P1S</h2>
        <p className="print-demo__muted">Check the build plate, Generic PETG spool, selected orientation, and sliced layer before starting.</p>
        <button type="button" className="print-demo__primary" disabled={!printerEnabled || !hasPreview || !run?.run_id || printing || sent} onClick={() => void print()}>{printing ? "Sending to printer…" : sent ? "Print sent" : "Print on P1S"}</button>
        {!printerEnabled && <p className="print-demo__muted">Print dispatch is disabled during preparation. Download and review the sliced 3MF here; enable printing after the P1S and AMS material checks.</p>}
        {sent && <div className="print-demo__monitor">
          <div className="print-demo__stats"><span><b>{printer?.status ?? "Connecting"}</b><small>Status</small></span><span><b>{printer?.progress == null ? "—" : `${printer.progress}%`}</b><small>Complete</small></span><span><b>{printer?.time_remaining_minutes == null ? "—" : `${printer.time_remaining_minutes} min`}</b><small>Estimated remaining</small></span></div>
          {printer?.progress != null && <progress max={100} value={printer.progress} aria-label="Print progress" />}
          {printer?.current_layer != null && <p className="print-demo__muted">Layer {printer.current_layer}{printer.total_layers != null ? ` of ${printer.total_layers}` : ""}</p>}
          <div className="print-demo__camera"><img src={`/api/workspace/print-demo/camera.mjpeg?session_id=${encodeURIComponent(sessionId)}`} alt="Live P1S chamber camera" onError={() => setCameraError(true)} />{cameraError && <span>Camera unavailable. Enable P1S LAN liveview and check the printer MCP connection.</span>}</div>
          {printerError && <p className="print-demo__error" role="status">{printerError}</p>}
        </div>}
      </section>
    </div>
  </div>;
}
