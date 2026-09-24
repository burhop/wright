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

interface Package {
  path: string;
  sha256: string;
}

function findPackage(results: WorkspaceEngineeringResult[] | undefined): Package | null {
  const representations = results?.flatMap((result) => result.representations ?? []) ?? [];
  const matches = representations.filter((rep) =>
    rep.kind === "workspace_file" && rep.location.endsWith("slice_package.gcode.3mf") &&
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

export function PrintPartDemoPage({ sessionId, workspaceId, onOpenWorkflow, onClose }: Props) {
  const [prompt, setPrompt] = useState("");
  const [image, setImage] = useState<File | null>(null);
  const [targetMm, setTargetMm] = useState(50);
  const [busy, setBusy] = useState(false);
  const [printing, setPrinting] = useState(false);
  const [sent, setSent] = useState(false);
  const [error, setError] = useState("");
  const [step, setStep] = useState("Describe the part");
  const [workflowPath, setWorkflowPath] = useState("");
  const [run, setRun] = useState<WorkspaceWorkflowSourceRun | null>(null);
  const [artifactRoot, setArtifactRoot] = useState("");
  const [printer, setPrinter] = useState<{
    status: string; progress: number | null; time_remaining_minutes: number | null;
    current_layer: number | null; total_layers: number | null;
  } | null>(null);
  const [printerError, setPrinterError] = useState("");
  const [cameraError, setCameraError] = useState(false);
  const packageFile = useMemo(() => findPackage(run?.results), [run]);
  const hasPreview = Boolean(run?.status === "completed" && packageFile && artifactRoot);

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
    setStep("Preparing Wright workflow");
    try {
      let imagePath: string | null = null;
      if (image) {
        if (image.size > 4 * 1024 * 1024) throw new Error("Choose an image under 4 MiB.");
        imagePath = await workspaceService.uploadPrintDemoImage(sessionId, image);
      }
      const prepared = await workspaceService.preparePrintPartDemo(sessionId, prompt, imagePath, targetMm);
      if (prepared.workspace_id !== workspaceId) throw new Error("The prepared workflow belongs to another workspace.");
      setWorkflowPath(prepared.workflow_path);
      setArtifactRoot(prepared.artifact_root);
      setStep("Running Blender and Bambu Studio");
      const result = await workspaceService.runWorkspaceWorkflowSource(
        sessionId, prepared.workflow_path, prepared.storage_digest,
        (event: WorkspaceWorkflowRunEvent) => {
          if (event.kind === "step_started" || event.kind === "task_progress" || event.kind === "operation_progress") {
            setStep(event.task_title || event.message || "Running workflow");
          }
        },
      );
      if (result.workflow_path !== prepared.workflow_path || result.workspace_id !== workspaceId) {
        throw new Error("Wright returned a run for another workflow.");
      }
      setRun(result);
      setStep(result.status === "completed" ? "Review the part and slice" : "Workflow needs review");
    } catch (reason) {
      setError(reason instanceof Error ? reason.message : "The print workflow could not complete.");
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
        {image && <span className="print-demo__muted">{image.name}</span>}
        <label htmlFor="print-demo-size">Largest dimension · mm</label>
        <input id="print-demo-size" type="number" min={5} max={250} value={targetMm} onChange={(event) => setTargetMm(Number(event.target.value))} disabled={busy} />
        <button type="button" className="print-demo__primary" onClick={() => void generate()} disabled={busy || (!prompt.trim() && !image) || !Number.isFinite(targetMm) || targetMm < 5 || targetMm > 250}>{busy ? "Creating part…" : "Create printable part"}</button>
        <p className="print-demo__muted">Wright saves each request as its own workflow and runs Blender MCP, mesh repair MCP, and Bambu Studio CLI with the P1S profile.</p>
      </section>
      <section className="print-demo__card print-demo__result" aria-label="Part and slice review">
        <div className="print-demo__section-head"><span className="print-demo__step">02 / REVIEW</span><span className="print-demo__pill">{step}</span></div>
        {hasPreview ? <div className="print-demo__previews">
          <div><strong>3D part</strong><PartPreview sessionId={sessionId} path={`${artifactRoot}/repaired_mesh.stl`} /><small>Drag to rotate · scroll to zoom</small></div>
          <div><strong>Support and toolpath preview</strong><img className="print-demo__support" src={workspaceContentUrl(`${artifactRoot}/support-preview.svg`, sessionId)} alt="Actual support and toolpath preview from the P1S slice" /><small>Generated by the actual slicer; supports appear where needed.</small></div>
        </div> : <div className="print-demo__empty">{busy ? "Engineering tools are working on your request…" : "The part and its slice will appear here."}</div>}
        {packageFile && <p className="print-demo__file">Sliced 3MF · <a href={workspaceContentUrl(packageFile.path, sessionId)} download>Download package</a><br /><code>SHA-256 {packageFile.sha256.slice(0, 16)}…</code></p>}
        {workflowPath && <button type="button" className="print-demo__text-button" onClick={() => onOpenWorkflow?.(workflowPath)}>Open saved Wright workflow</button>}
        {error && <p className="print-demo__error" role="alert">{error}</p>}
      </section>
      <section className="print-demo__card print-demo__printer" aria-label="Print and monitor">
        <span className="print-demo__step">03 / PRINT & MONITOR</span>
        <h2>Bambu P1S</h2>
        <p className="print-demo__muted">Check the build plate, selected PETG HF spool, and support preview before starting.</p>
        <button type="button" className="print-demo__primary" disabled={!hasPreview || !run?.run_id || printing || sent} onClick={() => void print()}>{printing ? "Sending to printer…" : sent ? "Print sent" : "Print on P1S"}</button>
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
