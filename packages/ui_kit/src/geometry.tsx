import { useEffect, useId, useRef, useState } from "react";
import * as THREE from "three";
import { OrbitControls } from "three/addons/controls/OrbitControls.js";
import { STLLoader } from "three/addons/loaders/STLLoader.js";
import type { ToolpathDocument } from "./toolpaths";

export const fitCameraToRadius = (
  camera: THREE.PerspectiveCamera,
  radius: number,
) => {
  const safeRadius = Math.max(radius, 0.001);
  const distance =
    (safeRadius / Math.sin(THREE.MathUtils.degToRad(camera.fov) / 2)) * 1.35;
  camera.position.setScalar(distance / Math.sqrt(3));
  camera.lookAt(0, 0, 0);
  camera.near = Math.max(0.00001, safeRadius / 1000);
  camera.far = Math.max(10, distance * 8, safeRadius * 80);
  camera.updateProjectionMatrix();
  return { distance, radius: safeRadius };
};

type Drawable = {
  object: THREE.Mesh | THREE.LineSegments;
  layer?: number;
  kind?: "model" | "support" | "unclassified";
};
function useScene(
  host: React.RefObject<HTMLDivElement | null>,
  create: () => { objects: Drawable[]; radius: number; lowY: number },
  dependency: unknown,
  visibility?: (object: Drawable) => boolean,
) {
  const [error, setError] = useState("");
  const objects = useRef<Drawable[]>([]);
  const display = useRef(visibility);
  display.current = visibility;
  useEffect(() => {
    const element = host.current;
    if (!element) return;
    setError("");
    let disposed = false,
      frame = 0;
    let renderer: THREE.WebGLRenderer | undefined,
      controls: OrbitControls | undefined,
      observer: ResizeObserver | undefined,
      themeObserver: MutationObserver | undefined;
    let grid: THREE.GridHelper | undefined;
    const scene = new THREE.Scene();
    let drawables: Drawable[] = [];
    try {
      const content = create();
      drawables = content.objects;
      objects.current = drawables;
      const radius = content.radius;
      if (!Number.isFinite(radius) || radius <= 0)
        throw new Error("Invalid geometry bounds");
      renderer = new THREE.WebGLRenderer({ antialias: true });
      renderer.domElement.setAttribute("data-testid", "3d-canvas");
      renderer.setPixelRatio(Math.min(window.devicePixelRatio || 1, 2));
      const camera = new THREE.PerspectiveCamera(45, 1, 0.001, radius * 80);
      const { distance } = fitCameraToRadius(camera, radius);
      controls = new OrbitControls(camera, renderer.domElement);
      controls.enableDamping = true;
      controls.minDistance = Math.max(0.001, radius * 0.02);
      controls.maxDistance = distance * 12;
      const ambient = new THREE.AmbientLight(0xffffff, 0.75);
      scene.add(ambient);
      const light = new THREE.DirectionalLight(0xffffff, 1.2);
      light.position.set(1, 2, 3);
      scene.add(light);
      drawables.forEach((item) => scene.add(item.object));
      grid = new THREE.GridHelper(radius * 3, 16);
      grid.position.y = content.lowY - radius * 0.01;
      scene.add(grid);
      element.replaceChildren(renderer.domElement);
      const theme = () => {
        const style = getComputedStyle(element);
        scene.background = new THREE.Color(
          style.getPropertyValue("--color-surface-subtle").trim() || "#0d1220",
        );
        for (const item of drawables) {
          const color =
            style
              .getPropertyValue(
                item.kind === "support"
                  ? "--color-warning"
                  : item.kind === "unclassified"
                    ? "--color-text-muted"
                    : "--color-secondary",
              )
              .trim() || "#38bdf8";
          const material = item.object.material as
            THREE.MeshPhongMaterial | THREE.LineBasicMaterial;
          material.color.setStyle(color);
        }
      };
      theme();
      themeObserver = new MutationObserver(theme);
      for (
        let ancestor: Element | null = element;
        ancestor;
        ancestor = ancestor.parentElement
      )
        themeObserver.observe(ancestor, {
          attributes: true,
          attributeFilter: ["data-theme", "style", "class"],
        });
      const resize = () => {
        const width = Math.max(1, element.clientWidth),
          height = Math.max(1, element.clientHeight);
        camera.aspect = width / height;
        camera.updateProjectionMatrix();
        renderer?.setSize(width, height);
      };
      resize();
      observer = new ResizeObserver(resize);
      observer.observe(element);
      let previousDisplay: typeof visibility;
      const draw = () => {
        if (disposed) return;
        if (display.current !== previousDisplay) {
          drawables.forEach((item) => {
            item.object.visible = display.current
              ? display.current(item)
              : true;
          });
          previousDisplay = display.current;
        }
        controls?.update();
        renderer?.render(scene, camera);
        frame = requestAnimationFrame(draw);
      };
      draw();
    } catch {
      setError(
        "The 3D view is unavailable. Open or download the exact representation to inspect it.",
      );
    }
    return () => {
      disposed = true;
      cancelAnimationFrame(frame);
      observer?.disconnect();
      themeObserver?.disconnect();
      controls?.dispose();
      const materials = new Set<THREE.Material>();
      drawables.forEach((item) => {
        item.object.geometry.dispose();
        for (const material of Array.isArray(item.object.material)
          ? item.object.material
          : [item.object.material])
          materials.add(material);
      });
      materials.forEach((material) => material.dispose());
      grid?.geometry.dispose();
      if (grid)
        for (const material of Array.isArray(grid.material)
          ? grid.material
          : [grid.material])
          material.dispose();
      renderer?.dispose();
      element.replaceChildren();
      objects.current = [];
    };
    // Creation closes over one immutable representation revision. Visibility is
    // applied through its ref and never recreates geometry or executes work.
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [dependency]);
  return error;
}

export function ThreeDViewer({
  arrayBuffer,
  fileName,
}: {
  arrayBuffer: ArrayBuffer;
  fileName?: string;
}) {
  const host = useRef<HTMLDivElement>(null);
  const error = useScene(
    host,
    () => {
      if (
        arrayBuffer.byteLength > 32 * 1024 * 1024 ||
        arrayBuffer.byteLength < 15
      )
        throw new Error("STL view bound");
      const geometry = new STLLoader().parse(arrayBuffer);
      const position = geometry.getAttribute("position");
      if (!position || !position.count || position.count > 3_000_000) {
        geometry.dispose();
        throw new Error("STL vertex bound");
      }
      for (const coordinate of position.array)
        if (!Number.isFinite(coordinate) || Math.abs(coordinate) > 1_000_000) {
          geometry.dispose();
          throw new Error("STL finite bounds");
        }
      // STL display uses Z-up coordinates, as does the toolpath projection. This
      // rotates only the view geometry; the exact stored/manufactured file is intact.
      geometry.rotateX(-Math.PI / 2);
      geometry.center();
      geometry.computeBoundingSphere();
      geometry.computeBoundingBox();
      const radius = geometry.boundingSphere?.radius ?? 0;
      return {
        objects: [
          {
            object: new THREE.Mesh(
              geometry,
              new THREE.MeshPhongMaterial({ color: 0x38bdf8, shininess: 40 }),
            ),
          },
        ],
        radius,
        lowY: geometry.boundingBox?.min.y ?? -radius,
      };
    },
    arrayBuffer,
  );
  return (
    <div className="wp-geometry">
      <div
        ref={host}
        className="wp-geometry-canvas"
        role="img"
        aria-label={
          fileName
            ? `Rotatable 3D preview: ${fileName}`
            : "Rotatable 3D geometry preview"
        }
      />
      {fileName && <p className="wp-muted">{fileName}</p>}
      {error ? (
        <p role="alert">{error}</p>
      ) : (
        <p className="wp-muted">
          Drag to rotate · scroll to zoom. A preview does not establish
          engineering compliance.
        </p>
      )}
    </div>
  );
}
export function ToolpathViewer({ document }: { document: ToolpathDocument }) {
  const host = useRef<HTMLDivElement>(null);
  const id = useId();
  const [through, setThrough] = useState(document.layers.length);
  const [model, setModel] = useState(true),
    [support, setSupport] = useState(true),
    [unclassified, setUnclassified] = useState(true);
  useEffect(() => setThrough(document.layers.length), [document]);
  const error = useScene(
    host,
    () => {
      let minX = Infinity,
        minY = Infinity,
        minZ = Infinity,
        maxX = -Infinity,
        maxY = -Infinity,
        maxZ = -Infinity;
      for (const layer of document.layers) {
        minZ = Math.min(minZ, layer.z);
        maxZ = Math.max(maxZ, layer.z);
        for (const kind of ["model", "support", "unclassified"] as const)
          for (const [x1, y1, x2, y2] of layer[kind]) {
            minX = Math.min(minX, x1, x2);
            maxX = Math.max(maxX, x1, x2);
            minY = Math.min(minY, y1, y2);
            maxY = Math.max(maxY, y1, y2);
          }
      }
      const centerX = (minX + maxX) / 2,
        centerY = (minY + maxY) / 2,
        centerZ = (minZ + maxZ) / 2;
      const radius = Math.max(maxX - minX, maxY - minY, maxZ - minZ, 0.001);
      const objects: Drawable[] = [];
      for (const [index, layer] of document.layers.entries())
        for (const kind of ["model", "support", "unclassified"] as const) {
          const paths = layer[kind];
          if (!paths.length) continue;
          const positions = new Float32Array(paths.length * 6);
          paths.forEach(([x1, y1, x2, y2], position) =>
            positions.set(
              [
                x1 - centerX,
                layer.z - centerZ,
                centerY - y1,
                x2 - centerX,
                layer.z - centerZ,
                centerY - y2,
              ],
              position * 6,
            ),
          );
          const geometry = new THREE.BufferGeometry();
          geometry.setAttribute(
            "position",
            new THREE.BufferAttribute(positions, 3),
          );
          objects.push({
            object: new THREE.LineSegments(
              geometry,
              new THREE.LineBasicMaterial({ color: 0x38bdf8 }),
            ),
            layer: index + 1,
            kind,
          });
        }
      return { objects, radius, lowY: minZ - centerZ };
    },
    document,
    (object) =>
      (object.layer ?? 0) <= through &&
      (object.kind === "model"
        ? model
        : object.kind === "support"
          ? support
          : unclassified),
  );
  const selected =
    document.layers[
      Math.max(0, Math.min(through - 1, document.layers.length - 1))
    ];
  return (
    <div className="wp-geometry">
      <div
        ref={host}
        className="wp-geometry-canvas"
        role="img"
        aria-label="Rotatable 3D toolpaths from all supported layers"
      />
      {error && <p role="alert">{error}</p>}
      <label htmlFor={id}>
        Layers 1–{through} of {document.layers.length}
        {selected ? ` · Z ${selected.z.toFixed(2)} mm` : ""}
      </label>
      <input
        id={id}
        type="range"
        min={1}
        max={document.layers.length}
        value={through}
        onChange={(event) => setThrough(Number(event.target.value))}
      />
      <div className="wp-row">
        {document.classificationKnown && (
          <>
            <label>
              <input
                type="checkbox"
                checked={model}
                onChange={(event) => setModel(event.target.checked)}
              />{" "}
              Model paths
            </label>
            <label>
              <input
                type="checkbox"
                checked={support}
                onChange={(event) => setSupport(event.target.checked)}
              />{" "}
              Support paths
            </label>
          </>
        )}
        <label>
          <input
            type="checkbox"
            checked={unclassified}
            onChange={(event) => setUnclassified(event.target.checked)}
          />{" "}
          Unclassified paths
        </label>
      </div>
      {!document.classificationKnown && (
        <p className="wp-muted">
          Support classification is unknown for this representation. Paths are
          shown without inferred support categories.
        </p>
      )}
      <p className="wp-muted">
        Drag to rotate · scroll to zoom · reveal layers with the slider.
        Geometry uses actual toolpaths; it is not a machine approval.
      </p>
    </div>
  );
}
