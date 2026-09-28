import { useEffect, useMemo, useRef, useState } from "react";
import * as THREE from "three";
import { OrbitControls } from "three/addons/controls/OrbitControls.js";
import { STLLoader } from "three/addons/loaders/STLLoader.js";
import {
  workspaceService,
  type PrintDemoPrinterStatus,
  type WorkspaceEngineeringResult,
  type WorkspaceWorkflowRunEvent,
  type WorkspaceWorkflowSourceRun,
} from "../../services/workspace-service";
import { workspaceContentUrl } from "../../services/viewer-panel/providers/workspace-content-url";
import "./PrintPartDemoPage.css";

interface Props {
  sessionId: string;
  workspaceId: string;
  initialWorkflowPath?: string;
  initialRunLogPath?: string | null;
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

export function PrintPartDemoPage({ sessionId, workspaceId, initialWorkflowPath, initialRunLogPath, onOpenWorkflow, onClose }: Props) {
  const startedAt = useRef(0);
  const currentStage = useRef("Preparing the request");
  const [prompt, setPrompt] = useState("");
  const [image, setImage] = useState<File | null>(null);
  const [targetMm, setTargetMm] = useState(50);
  const [designFilament, setDesignFilament] = useState("PETG");
  const [selectedSlot, setSelectedSlot] = useState<number | null>(null);
  const [busy, setBusy] = useState(false);
  const [printing, setPrinting] = useState(false);
  const [stopping, setStopping] = useState(false);
  const [confirmCancel, setConfirmCancel] = useState(false);
  const [stopMessage, setStopMessage] = useState("");
  const [stopError, setStopError] = useState("");
  const [sent, setSent] = useState(false);
  const [dispatchState, setDispatchState] = useState("not_sent");
  const [dispatchMessage, setDispatchMessage] = useState("");
  const [dispatchReply, setDispatchReply] = useState<Record<string, unknown> | null>(null);
  const [retryChecked, setRetryChecked] = useState(false);
  const [allowingRetry, setAllowingRetry] = useState(false);
  const [monitorNow, setMonitorNow] = useState(Date.now());
  const [error, setError] = useState("");
  const [errorDetails, setErrorDetails] = useState("");
  const [step, setStep] = useState("Describe the part");
  const [activity, setActivity] = useState<string[]>([]);
  const [elapsedSeconds, setElapsedSeconds] = useState(0);
  const [imagePreview, setImagePreview] = useState("");
  const [workflowPath, setWorkflowPath] = useState("");
  const [runLogPath, setRunLogPath] = useState("");
  const [run, setRun] = useState<WorkspaceWorkflowSourceRun | null>(null);
  const [artifactRoot, setArtifactRoot] = useState("");
  const [printer, setPrinter] = useState<PrintDemoPrinterStatus | null>(null);
  const [printerError, setPrinterError] = useState("");
  const [cameraError, setCameraError] = useState(false);
  const [printerEnabled, setPrinterEnabled] = useState(false);
  const [monitorEnabled, setMonitorEnabled] = useState(false);
  const [sliceMetrics, setSliceMetrics] = useState<{ orientation_selected: string; estimated_seconds: number; filament_g: number; support_moves: number; preview_layer: number; filament?: { name?: string } } | null>(null);
  const sourceFile = useMemo(() => findArtifact(run?.results, artifactRoot, "source_mesh.stl"), [run, artifactRoot]);
  const repairedFile = useMemo(() => findArtifact(run?.results, artifactRoot, "repaired_mesh.stl"), [run, artifactRoot]);
  const orientedFile = useMemo(() => findArtifact(run?.results, artifactRoot, "oriented_mesh.stl"), [run, artifactRoot]);
  const supportFile = useMemo(() => findArtifact(run?.results, artifactRoot, "support-preview.svg"), [run, artifactRoot]);
  const toolpathFile = useMemo(() => findArtifact(run?.results, artifactRoot, "toolpaths.json"), [run, artifactRoot]);
  const evidenceFile = useMemo(() => findArtifact(run?.results, artifactRoot, "slice-evidence.json"), [run, artifactRoot]);
  const repairReportFile = useMemo(() => findArtifact(run?.results, artifactRoot, "repair-model-report.json"), [run, artifactRoot]);
  const packageFile = useMemo(() => findArtifact(run?.results, artifactRoot, "slice_package.gcode.3mf"), [run, artifactRoot]);
  const hasPreview = Boolean(run?.status === "completed" && sourceFile && repairedFile && orientedFile && supportFile && toolpathFile && evidenceFile && packageFile);
  const resultUrl = workflowPath && runLogPath
    ? `/workspace/${encodeURIComponent(workspaceId)}?${new URLSearchParams({ workflow: "canonical", workflowPath, printDemoRun: runLogPath })}`
    : "";
  const [baseTrimMm, setBaseTrimMm] = useState(0);
  const [polygonReduction, setPolygonReduction] = useState<{ before: number; after: number } | null>(null);
  const slicedFilament = sliceMetrics?.filament?.name?.replace(/^Generic /, "").toUpperCase() ?? null;
  const selectedTray = printer?.trays.find((tray) => tray.slot === selectedSlot) ?? null;
  const materialMatches = Boolean(selectedTray && !selectedTray.empty && selectedTray.type === slicedFilament);
  const designMaterialLoaded = !printer || printer.trays.some((tray) => !tray.empty && tray.type === designFilament);
  const telemetryStale = Boolean(printer?.telemetry_stale || (printer?.telemetry_at && monitorNow - Date.parse(printer.telemetry_at) > 30000));
  const printReady = Boolean(printerEnabled && printer?.ready && !telemetryStale && materialMatches && hasPreview && run?.run_id && !printing && !sent);
  const activeJob = Boolean(printer && ["RUNNING", "PREPARE", "SLICING", "PAUSE"].includes(printer.status));
  const expectedJob = packageFile ? `wright_${packageFile.sha256.slice(0, 12)}.gcode.3mf` : null;
  const matchingJob = Boolean(sent && expectedJob && printer && !telemetryStale &&
    [printer.job_name, printer.gcode_file].some((name) => name?.replaceAll("\\", "/").split("/").pop() === expectedJob));
  const thisJobActive = activeJob && matchingJob;
  const observedJob = matchingJob ? printer : null;
  const jobPhase = printer?.status === "FINISH" ? "Completed" : printer?.status === "PAUSE" ? "Paused" :
    printer?.status === "FAILED" ? "Stopped / failed" :
    (printer?.bed_target_c ?? 0) > (printer?.bed_c ?? 0) + 5 && !printer?.current_layer ? "Heating bed" :
    (printer?.nozzle_target_c ?? 0) > (printer?.nozzle_c ?? 0) + 5 && !printer?.current_layer ? "Heating nozzle" :
    printer?.status === "PREPARE" || printer?.status === "SLICING" || (activeJob && !printer?.current_layer) ? "Preparing" :
    printer?.status === "RUNNING" ? "Printing" : printer?.status ?? "Unknown";
  const monitorState = !printer ? "Connection unavailable" : telemetryStale ? "Updates delayed" :
    matchingJob ? jobPhase :
    dispatchState === "printer_rejected" ? "Start rejected" : "Start not confirmed";
  const printBlockReason = sent || printing ? "" :
    !printerEnabled ? "Wright is waiting for print access. This page checks again automatically." :
    !printer ? "Checking the printer and AMS before printing." :
    telemetryStale ? "Printer updates are delayed. Waiting for fresh telemetry before printing." :
    !printer.ready ? printer.readiness_reason :
    !hasPreview || !run?.run_id ? "Create and review a sliced 3MF before printing." :
    !selectedTray ? `Choose a loaded ${slicedFilament ?? "matching"} AMS slot before printing.` :
    !materialMatches ? `This 3MF requires ${slicedFilament ?? "a different material"}. ${selectedTray.label} contains ${selectedTray.type}; choose a matching loaded slot.` : "";

  useEffect(() => {
    if (slicedFilament && ["PLA", "PETG", "ABS", "ASA"].includes(slicedFilament)) setDesignFilament(slicedFilament);
  }, [run?.run_id, slicedFilament]);

  useEffect(() => {
    if (!initialRunLogPath) return;
    let active = true;
    const slug = initialWorkflowPath?.match(/^workflows\/(prompt-to-print-[0-9a-f]{12})\.workflow\.wflow$/)?.[1];
    if (!slug || !new RegExp(`^runs/${slug}/[0-9]{8}T[0-9]{6}Z-[0-9a-f]{12}\\.json$`).test(initialRunLogPath)) {
      setError("This saved-result link is invalid. Open the workflow from the workspace files.");
      return;
    }
    startedAt.current = Date.now();
    setBusy(true);
    setStep("Opening saved result");
    void fetch(workspaceContentUrl(initialRunLogPath, sessionId)).then((response) => {
      if (!response.ok) throw new Error("The saved run is unavailable.");
      return response.json();
    }).then((wrapper) => {
      const record = JSON.parse(wrapper.content) as {
        workflow_path?: string; status?: string; run_id?: string;
        result?: WorkspaceWorkflowSourceRun;
      };
      const saved = record.result;
      if (record.workflow_path !== initialWorkflowPath || record.status !== "completed" || saved?.status !== "completed" || saved.run_id !== record.run_id || !Array.isArray(saved.results)) {
        throw new Error("The saved run does not contain a completed result for this workflow.");
      }
      const packages = saved.results.flatMap((item) => item.representations ?? []).filter((rep) =>
        rep.kind === "workspace_file" && /^campaign\/printed-replacement-part-01\/demo-[0-9a-f]{12}\/artifacts\/slice_package\.gcode\.3mf$/.test(rep.location),
      );
      if (packages.length !== 1) throw new Error("The saved run does not identify one sliced 3MF package.");
      if (!active) return;
      setWorkflowPath(record.workflow_path);
      setArtifactRoot(packages[0].location.slice(0, -"/slice_package.gcode.3mf".length));
      setRun(saved);
      setRunLogPath(initialRunLogPath);
      setStep("Review the saved part and slice");
      setActivity(["Saved Wright run loaded"]);
    }).catch(() => {
      if (active) { setError("This saved result could not be opened. Open the workflow from the workspace files to inspect its run."); setStep("Needs attention"); }
    }).finally(() => { if (active) setBusy(false); });
    return () => { active = false; };
  }, [initialWorkflowPath, initialRunLogPath, sessionId]);

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
    if (!repairReportFile) { setBaseTrimMm(0); setPolygonReduction(null); return; }
    let active = true;
    void fetch(workspaceContentUrl(repairReportFile.path, sessionId)).then((response) => response.json()).then((wrapper) => {
      const file = typeof wrapper.content === "string" ? JSON.parse(wrapper.content) : wrapper;
      const value = typeof file?.content?.[0]?.text === "string" ? JSON.parse(file.content[0].text) : file;
      const trim = value?.repair?.printable_base?.trimmed_mm;
      const reduction = value?.repair?.polygon_reduction;
      if (active) {
        setBaseTrimMm(typeof trim === "number" && Number.isFinite(trim) ? trim : 0);
        setPolygonReduction(reduction?.used === true && Number.isInteger(reduction.triangles_before) && Number.isInteger(reduction.triangles_after)
          ? { before: reduction.triangles_before, after: reduction.triangles_after } : null);
      }
    }).catch(() => { if (active) { setBaseTrimMm(0); setPolygonReduction(null); } });
    return () => { active = false; };
  }, [repairReportFile?.path, sessionId]);

  useEffect(() => {
    let active = true;
    const refresh = () => {
      void workspaceService.getPrintDemoCapabilities().then((value) => {
        if (active) { setPrinterEnabled(value.printer_enabled); setMonitorEnabled(value.monitor_enabled); }
      }).catch(() => { if (active) { setPrinterEnabled(false); setMonitorEnabled(false); } });
    };
    refresh();
    window.addEventListener("focus", refresh);
    const timer = window.setInterval(refresh, 5000);
    return () => { active = false; window.removeEventListener("focus", refresh); window.clearInterval(timer); };
  }, []);

  useEffect(() => {
    if (!monitorEnabled) return;
    let active = true;
    const clock = window.setInterval(() => setMonitorNow(Date.now()), 1000);
    let timer: number | undefined;
    const refresh = async (fresh = false) => {
      await workspaceService.getPrintDemoPrinterStatus(sessionId, fresh).then((value) => {
        if (active) { setPrinter(value); setPrinterError(""); }
      }).catch((reason: unknown) => {
        if (active) { setPrinter(null); setPrinterError(reason instanceof Error ? reason.message : "Printer status unavailable."); }
      });
      if (active) timer = window.setTimeout(() => void refresh(), 5000);
    };
    void refresh(true);
    return () => { active = false; window.clearTimeout(timer); window.clearInterval(clock); };
  }, [monitorEnabled, sessionId]);

  useEffect(() => {
    if (!run?.run_id || !packageFile || !workflowPath) return;
    let active = true;
    void workspaceService.getPrintDemoDispatch(sessionId, workflowPath, run.run_id, packageFile.sha256).then((value) => {
      if (!active) return;
      setDispatchState(value.state);
      setDispatchMessage(value.printer_response?.message ?? "");
      setDispatchReply(value.printer_response?.command_response ?? null);
      setSent(!["not_sent", "dispatch_failed_before_start", "retry_authorized_by_user"].includes(value.state));
      if (value.state !== "not_sent") {
        if (typeof value.ams_slot === "number") setSelectedSlot(value.ams_slot);
        if (value.error) setError(value.error);
      }
    }).catch(() => {});
    return () => { active = false; };
  }, [run?.run_id, packageFile?.sha256, workflowPath, sessionId]);

  const generate = async () => {
    if ((!prompt.trim() && !image) || busy || !designMaterialLoaded) return;
    setBusy(true);
    setRun(null);
    setRunLogPath("");
    setSent(false);
    setDispatchState("not_sent");
    setDispatchMessage("");
    setDispatchReply(null);
    setStopMessage("");
    setStopError("");
    setConfirmCancel(false);
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
      const prepared = await workspaceService.preparePrintPartDemo(sessionId, prompt, imagePath, targetMm, designFilament);
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
      if (result.run_log_path) setRunLogPath(result.run_log_path);
      else if (result.run_id) {
        void workspaceService.getWorkspaceWorkflowRuns(sessionId, prepared.workflow_path, { latestOnly: true, workspaceId }).then((history) => {
          if (history[0]?.run_id === result.run_id) setRunLogPath(history[0].path);
        }).catch(() => {});
      }
      setStep(result.status === "completed" ? "Review the part and slice" : "Workflow needs review");
      if (result.status === "completed") setActivity((current) => [...current, "3D model and sliced package ready"].slice(-8));
    } catch (reason) {
      const detail = reason instanceof Error ? reason.message : "The print workflow could not complete.";
      setErrorDetails(detail);
      const stage = currentStage.current.toLowerCase();
      setError(stage.includes("slice") || stage.includes("support")
        ? "Wright created the part, but Bambu Studio could not finish its slice. Open the saved workflow for the run details, then retry. Rounded parts need a small flat base to sit on the plate."
        : stage.includes("repair")
          ? "Wright created the mesh, but could not finish preparing it for printing. Open the saved workflow for details, then use Create printable part for a fresh attempt."
          : `Wright could not finish ${stage}. Open the saved workflow for the run details, then use Create printable part for a fresh attempt.`);
      setStep("Needs attention");
    } finally {
      setBusy(false);
    }
  };

  const print = async () => {
    if (!run?.run_id || !packageFile || !workflowPath || !printReady || selectedSlot == null) return;
    setPrinting(true);
    setError("");
    try {
      const response = await workspaceService.printDemoPackage(sessionId, workflowPath, run.run_id, packageFile.sha256, selectedSlot);
      setSent(true);
      setDispatchState(response.state);
      setDispatchMessage(response.printer_response?.message ?? "");
      setDispatchReply(response.printer_response?.command_response ?? null);
      setStep(response.state === "printer_rejected" ? "Printer rejected start" : "Print command sent");
    } catch (reason) {
      setError(reason instanceof Error ? reason.message : "The printer did not accept the job.");
      setStep("Check printer dispatch");
      void workspaceService.getPrintDemoDispatch(sessionId, workflowPath, run.run_id, packageFile.sha256).then((value) => {
        setDispatchState(value.state);
        setSent(!["not_sent", "dispatch_failed_before_start", "retry_authorized_by_user"].includes(value.state));
      }).catch(() => {});
    } finally {
      setPrinting(false);
    }
  };

  const cancelPrint = async () => {
    if (!run?.run_id || !packageFile || !workflowPath || !sent || !thisJobActive || stopping) return;
    setStopping(true);
    setStopMessage("");
    setStopError("");
    try {
      const result = await workspaceService.cancelPrintDemo(sessionId, workflowPath, run.run_id, packageFile.sha256);
      setDispatchState(result.state);
      setStopMessage(result.message);
    } catch (reason) {
      setStopError(reason instanceof Error ? reason.message : "The P1S did not accept the stop request.");
    } finally {
      setStopping(false);
      setConfirmCancel(false);
    }
  };

  const allowRetry = async () => {
    if (!retryChecked || !printer?.ready || telemetryStale || matchingJob || !run?.run_id || !packageFile || !workflowPath) return;
    setAllowingRetry(true);
    try {
      const value = await workspaceService.allowPrintDemoRetry(sessionId, workflowPath, run.run_id, packageFile.sha256);
      setDispatchState(value.state);
      setSent(false);
      setRetryChecked(false);
      setError("");
      setStep("Ready for another print attempt");
    } catch (reason) {
      setError(reason instanceof Error ? reason.message : "Unable to allow another attempt.");
    } finally { setAllowingRetry(false); }
  };

  return <div className="print-demo" data-testid="print-part-demo">
    <header className="print-demo__header">
      <div><span className="print-demo__eyebrow">WRIGHT · ADDITIVE MANUFACTURING</span><h1>Prompt to printed part</h1><p>Describe a part, review the generated mesh and supported slice, then start the P1S print.</p></div>
      <button type="button" className="print-demo__text-button" onClick={onClose}>Back to Workflows</button>
    </header>
    <div className="print-demo__grid">
      <section className="print-demo__card" aria-label="Part request">
        <span className="print-demo__step">01 / {initialRunLogPath ? "NEW DESIGN REQUEST" : "DESIGN REQUEST"}</span>
        {initialRunLogPath && run && <p className="print-demo__muted">Viewing saved run {run.run_id?.slice(0, 12)}. The fields below start a new part.</p>}
        <label htmlFor="print-demo-prompt">What part should Wright make?</label>
        <textarea id="print-demo-prompt" value={prompt} onChange={(event) => setPrompt(event.target.value)} placeholder="A replacement knob, 50 mm wide, with a 6 mm D-shaped shaft socket…" rows={6} disabled={busy} />
        <label htmlFor="print-demo-image">Reference image <small>(optional)</small></label>
        <input id="print-demo-image" type="file" accept="image/png,image/jpeg,image/gif,image/webp" onChange={(event) => setImage(event.target.files?.[0] ?? null)} disabled={busy} />
        {image && <div className="print-demo__image-preview">{imagePreview && <img src={imagePreview} alt="Uploaded part reference" />}<span className="print-demo__muted">{image.name}</span></div>}
        <label htmlFor="print-demo-size">Largest dimension · mm</label>
        <input id="print-demo-size" type="number" min={5} max={250} value={targetMm} onChange={(event) => setTargetMm(Number(event.target.value))} disabled={busy} />
        <small className="print-demo__muted">This value controls the part's scale. For a 10 cm part, enter 100 mm.</small>
        <label htmlFor="print-demo-filament">Filament type for this slice</label>
        <select id="print-demo-filament" value={designFilament} onChange={(event) => setDesignFilament(event.target.value)} disabled={busy}>
          {["PLA", "PETG", "ABS", "ASA"].map((material) => <option key={material} value={material} disabled={Boolean(printer && !printer.trays.some((tray) => !tray.empty && tray.type === material))}>{material}{printer && !printer.trays.some((tray) => !tray.empty && tray.type === material) ? " · not loaded" : ""}</option>)}
        </select>
        <small className="print-demo__muted">Choose a material loaded in the AMS. The sliced 3MF uses this material's temperatures and settings. {printer?.trays.length ? `Loaded now: ${printer.trays.filter((tray) => !tray.empty).map((tray) => `${tray.label} ${tray.type}`).join("; ")}.` : ""}</small>
        <button type="button" className="print-demo__primary" onClick={() => void generate()} disabled={busy || !designMaterialLoaded || (sent && activeJob) || (!prompt.trim() && !image) || !Number.isFinite(targetMm) || targetMm < 5 || targetMm > 250}>{busy ? "Creating part…" : "Create printable part"}</button>
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
        {hasPreview && polygonReduction && <p className="print-demo__notice">Wright reduced the mesh from {polygonReduction.before.toLocaleString()} to {polygonReduction.after.toLocaleString()} triangles for the P1S process. Review the detail before printing.</p>}
        {hasPreview && <p className="print-demo__muted">Review functional surfaces and layer strength; the orientation comparison measures bed contact, supports, time, and filament.</p>}
        {hasPreview && <p className="print-demo__file">Mesh · <a href={workspaceContentUrl(sourceFile!.path, sessionId)} download>Source STL</a> · <a href={workspaceContentUrl(repairedFile!.path, sessionId)} download>Repaired STL</a> · <a href={workspaceContentUrl(orientedFile!.path, sessionId)} download>Selected STL</a> · <a href={workspaceContentUrl(evidenceFile!.path, sessionId)} download>Orientation comparison</a></p>}
        {packageFile && <p className="print-demo__file">Sliced 3MF · <a href={workspaceContentUrl(packageFile.path, sessionId)} download>Download package</a><br /><code>SHA-256 {packageFile.sha256.slice(0, 16)}…</code></p>}
        {workflowPath && <button type="button" className="print-demo__text-button" onClick={() => onOpenWorkflow?.(workflowPath)}>Open saved Wright workflow</button>}
        {hasPreview && resultUrl && <a className="print-demo__text-button" href={resultUrl}>Link to this result</a>}
        {error && <div className="print-demo__error" role="alert">{error}{errorDetails && <details><summary>Technical details</summary><pre>{errorDetails}</pre></details>}</div>}
      </section>
      <section className="print-demo__card print-demo__printer" aria-label="Print and monitor">
        <span className="print-demo__step">03 / PRINT & MONITOR</span>
        <h2>Bambu P1S</h2>
        <div className={`print-demo__readiness ${printer?.ready && !telemetryStale ? "print-demo__readiness--ready" : ""}`} role="status" aria-live="polite">
          <strong>{telemetryStale ? "Printer updates delayed" : printer?.ready ? "Printer available" : printer ? `Printer ${printer.status.toLowerCase()}` : monitorEnabled && !printerError ? "Checking printer…" : "Printer status unavailable"}</strong>
          <small>{telemetryStale ? "Waiting for fresh telemetry before printing." : printer?.readiness_reason ?? (monitorEnabled ? "Checking the P1S connection…" : "Enable printer monitoring to see live status and AMS inventory.")}</small>
        </div>
        {printer && activeJob && <p className="print-demo__muted">Current job: {printer.job_name || "name unavailable"}{printer.progress != null ? ` · ${printer.progress}% complete` : ""}{printer.time_remaining_minutes != null ? ` · ${printer.time_remaining_minutes} min remaining` : ""}</p>}
        {printer?.telemetry_at && <p className="print-demo__muted">Last printer report: {new Date(printer.telemetry_at).toLocaleTimeString()}{telemetryStale ? " · Updates are delayed" : " · Monitoring automatically"}</p>}
        {printer && ((printer.print_error ?? 0) !== 0 || Boolean(printer.hms?.length)) && <div className="print-demo__error" role="alert">Printer diagnostic: {printer.print_error ? `print error ${printer.print_error}. ` : ""}{printer.hms?.map((item) => [item.attr, item.code].map((value) => typeof value === "number" ? value.toString(16).padStart(8, "0").match(/.{4}/g)?.join("-") : "unknown").join("-")).join(", ")}. Check the printer screen for the corresponding message.</div>}
        {monitorEnabled && <button type="button" className="print-demo__text-button" onClick={() => void workspaceService.getPrintDemoPrinterStatus(sessionId, true).then((value) => { setPrinter(value); setPrinterError(""); }).catch((reason: unknown) => { setPrinter(null); setPrinterError(reason instanceof Error ? reason.message : "Printer status unavailable."); })}>Refresh printer and AMS</button>}
        <label htmlFor="print-demo-ams-slot">AMS filament for this print</label>
        {printer?.trays.length ? <div className="print-demo__ams-inventory" aria-label="Live AMS inventory">{printer.trays.map((tray) => <span key={tray.slot}><i aria-hidden="true" style={{ backgroundColor: tray.color ? `#${tray.color.slice(0, 6)}` : undefined }} />{tray.label}: {tray.empty ? "empty" : tray.type}</span>)}</div> : null}
        <select id="print-demo-ams-slot" value={selectedSlot ?? ""} disabled={!printer || sent} onChange={(event) => {
          const slot = event.target.value === "" ? null : Number(event.target.value);
          setSelectedSlot(slot);
          const tray = printer?.trays.find((item) => item.slot === slot);
          if (tray?.supported && tray.type) setDesignFilament(tray.type);
        }}>
          <option value="">Choose a loaded AMS slot</option>
          {printer?.trays.map((tray) => <option key={tray.slot} value={tray.slot} disabled={tray.empty || !tray.supported}>{tray.label} · {tray.empty ? "empty" : tray.type}{tray.color ? ` · #${tray.color.slice(0, 6)}` : ""}{!tray.empty && !tray.supported ? " · no demo profile" : ""}</option>)}
        </select>
        {printer?.trays.length === 0 && <p className="print-demo__muted">No AMS trays were reported. Check the AMS connection and refresh.</p>}
        {hasPreview && slicedFilament && <p className="print-demo__muted">This 3MF is sliced for {slicedFilament}. {selectedTray && !materialMatches ? `To use ${selectedTray.type}, create a new printable part with that material selected.` : "Choose a matching loaded slot."}</p>}
        <p className="print-demo__muted">Review the build plate, selected orientation, sliced layer and loaded filament before starting.</p>
        <button type="button" className="print-demo__primary" disabled={!printReady} onClick={() => void print()}>{printing ? "Uploading and requesting print…" : sent ? matchingJob ? "Print sent" : "Start not confirmed" : dispatchState === "dispatch_failed_before_start" ? "Retry print on P1S" : "Print on P1S"}</button>
        {printBlockReason && <p className="print-demo__notice" role="status">{printBlockReason}</p>}
        {printerError && <p className="print-demo__error" role="status">{printerError}</p>}
        {sent && <div className="print-demo__monitor">
          <p className="print-demo__notice" role="status">{matchingJob ? "The printer is reporting this Wright job." : dispatchMessage || "The command was sent, but the printer has not confirmed this Wright job. Sending a command alone does not confirm a print start."}</p>
          {sent && !matchingJob && printer?.ready && <p className="print-demo__muted">The printer is idle; this part has not been observed starting. {printer.job_name ? `Its last reported job is “${printer.job_name}”.` : ""} Progress from that job is excluded below.</p>}
          {dispatchReply && <details><summary>Printer command response</summary><pre>{JSON.stringify(dispatchReply, null, 2)}</pre></details>}
          {!matchingJob && printer?.ready && !telemetryStale && <div className="print-demo__notice print-demo__retry"><label><input type="checkbox" checked={retryChecked} onChange={(event) => setRetryChecked(event.target.checked)} /> I checked the P1S: this Wright job never started and the build plate is clear.</label><button type="button" className="print-demo__text-button" disabled={!retryChecked || allowingRetry} onClick={() => void allowRetry()}>{allowingRetry ? "Checking printer…" : "Allow another attempt"}</button><small>This checks live readiness and preserves the previous attempt. Then use Print on P1S to send again.</small></div>}
          <div className="print-demo__stats"><span><b>{monitorState}</b><small>This print</small></span><span><b>{observedJob?.progress == null ? "—" : `${observedJob.progress}%`}</b><small>Complete</small></span><span><b>{observedJob?.time_remaining_minutes == null ? "—" : `${observedJob.time_remaining_minutes} min`}</b><small>Estimated remaining</small></span></div>
          {observedJob?.progress != null && <progress max={100} value={observedJob.progress} aria-label="Print progress" />}
          {observedJob?.current_layer != null && <p className="print-demo__muted">Layer {observedJob.current_layer}{observedJob.total_layers != null ? ` of ${observedJob.total_layers}` : ""}</p>}
          {printer?.nozzle_c != null && <p className="print-demo__muted">Nozzle: {Math.round(printer.nozzle_c)} °C (target {printer.nozzle_target_c || "off"}) · Bed: {printer.bed_c == null ? "—" : Math.round(printer.bed_c)} °C (target {printer.bed_target_c || "off"})</p>}
          {!confirmCancel ? <button type="button" className="print-demo__cancel" disabled={!printerEnabled || !thisJobActive || stopping} onClick={() => setConfirmCancel(true)}>Cancel this print</button> : <div className="print-demo__cancel-confirm" role="group" aria-label="Confirm print cancellation"><p>Stop this Wright print on the P1S?</p><button type="button" className="print-demo__cancel" disabled={stopping || !thisJobActive} onClick={() => void cancelPrint()}>{stopping ? "Sending stop request…" : "Confirm stop"}</button><button type="button" className="print-demo__text-button" disabled={stopping} onClick={() => setConfirmCancel(false)}>Keep printing</button></div>}
          {stopMessage && <p className="print-demo__notice" role="status">{stopMessage}</p>}
          {stopError && <p className="print-demo__error" role="alert">{stopError}</p>}
          <div className="print-demo__camera"><img src={`/api/workspace/print-demo/camera.mjpeg?session_id=${encodeURIComponent(sessionId)}`} alt="Live P1S chamber camera" onError={() => setCameraError(true)} />{cameraError && <span>Camera unavailable. Enable P1S LAN liveview and check the printer MCP connection.</span>}</div>
        </div>}
      </section>
    </div>
  </div>;
}
