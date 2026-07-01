import { useEffect, useRef } from "react";
import * as THREE from "three";
import { OrbitControls } from "three/addons/controls/OrbitControls.js";
import { STLLoader } from "three/addons/loaders/STLLoader.js";

interface ThreeDViewerProps {
  arrayBuffer: ArrayBuffer;
  fileName?: string;
}

const VIEWER_BACKGROUND = 0x090d16;
const PART_MATERIAL = 0xd9f3ff;
const PART_SPECULAR = 0x7dd3fc;
const GRID_PRIMARY = 0x1e293b;
const GRID_SECONDARY = 0x0d1220;

const fitCameraToRadius = (
  camera: THREE.PerspectiveCamera,
  radius: number,
) => {
  const safeRadius = Math.max(radius, 1);
  const fov = THREE.MathUtils.degToRad(camera.fov);
  const distance = (safeRadius / Math.sin(fov / 2)) * 1.35;
  const component = distance / Math.sqrt(3);

  camera.position.set(component, component, component);
  camera.lookAt(0, 0, 0);
  camera.near = Math.max(0.001, safeRadius / 1000);
  camera.far = Math.max(1000, distance * 8, safeRadius * 80);
  camera.updateProjectionMatrix();

  return { distance, radius: safeRadius };
};

export function ThreeDViewer({ arrayBuffer, fileName }: ThreeDViewerProps) {
  const containerRef = useRef<HTMLDivElement>(null);
  const canvasRef = useRef<HTMLCanvasElement>(null);

  useEffect(() => {
    const container = containerRef.current;
    const canvas = canvasRef.current;
    if (!container || !canvas) return;

    // Get current dimensions
    const width = container.clientWidth || 300;
    const height = container.clientHeight || 300;

    // 1. Create Scene
    const scene = new THREE.Scene();
    scene.background = new THREE.Color(VIEWER_BACKGROUND);

    // 2. Create Camera
    const camera = new THREE.PerspectiveCamera(45, width / height, 0.001, 10000);
    camera.position.set(40, 40, 40);

    // 3. Create Renderer
    const renderer = new THREE.WebGLRenderer({ antialias: true, canvas });
    renderer.setSize(width, height);
    renderer.setPixelRatio(Math.min(window.devicePixelRatio, 2));

    // 4. Add Lights
    const ambientLight = new THREE.AmbientLight(0xb8d8f0, 0.65);
    scene.add(ambientLight);

    const dirLight1 = new THREE.DirectionalLight(0xffffff, 1.1);
    dirLight1.position.set(1, 1, 1).normalize();
    scene.add(dirLight1);

    const dirLight2 = new THREE.DirectionalLight(0x7dd3fc, 0.45);
    dirLight2.position.set(-1, -1, -1).normalize();
    scene.add(dirLight2);

    // 5. Add Grid & Axis Helpers
    const gridHelper = new THREE.GridHelper(80, 40, GRID_PRIMARY, GRID_SECONDARY);
    gridHelper.position.y = -10;
    scene.add(gridHelper);

    // 6. Parse and Load STL Geometry
    const loader = new STLLoader();
    let mesh: THREE.Mesh | null = null;
    let geometry: THREE.BufferGeometry | null = null;
    let material: THREE.MeshPhongMaterial | null = null;

    try {
      geometry = loader.parse(arrayBuffer);
      geometry.center();

      material = new THREE.MeshPhongMaterial({
        color: PART_MATERIAL,
        specular: PART_SPECULAR,
        shininess: 60,
      });

      mesh = new THREE.Mesh(geometry, material);
      scene.add(mesh);

      // Adjust camera distance to fit geometry bounding box
      geometry.computeBoundingSphere();
      const boundingSphere = geometry.boundingSphere;
      if (boundingSphere) {
        const { radius } = fitCameraToRadius(camera, boundingSphere.radius);
        // Adjust grid position to fit base
        gridHelper.position.y = -radius * 1.1;
        const gridSize = Math.max(80, radius * 4);
        gridHelper.scale.setScalar(gridSize / 80);
      }
    } catch (err) {
      console.error("Failed to parse STL geometry buffer", err);
    }

    // 7. Add Orbit Controls
    const controls = new OrbitControls(camera, renderer.domElement);
    controls.enableDamping = true;
    controls.dampingFactor = 0.05;
    const radius = geometry?.boundingSphere?.radius;
    const fitDistance =
      radius !== undefined ? fitCameraToRadius(camera, radius).distance : 40;
    controls.minDistance = radius !== undefined ? Math.max(0.01, radius * 0.02) : 1;
    controls.maxDistance = Math.max(1000, fitDistance * 12, (radius || 1) * 40);

    // 8. Handle Resizing
    const resizeObserver = new ResizeObserver((entries) => {
      if (!entries || entries.length === 0) return;
      const { width: newWidth, height: newHeight } = entries[0].contentRect;
      if (newWidth > 0 && newHeight > 0) {
        camera.aspect = newWidth / newHeight;
        camera.updateProjectionMatrix();
        renderer.setSize(newWidth, newHeight);
      }
    });
    resizeObserver.observe(container);

    // 9. Animation Loop
    let animationFrameId: number;
    const animate = () => {
      animationFrameId = requestAnimationFrame(animate);
      controls.update();
      renderer.render(scene, camera);
    };
    animate();

    // 10. Cleanup
    return () => {
      cancelAnimationFrame(animationFrameId);
      resizeObserver.disconnect();
      controls.dispose();
      if (geometry) geometry.dispose();
      if (material) material.dispose();
      if (mesh) scene.remove(mesh);
      scene.remove(gridHelper);
      renderer.dispose();
    };
  }, [arrayBuffer]);

  return (
    <div
      ref={containerRef}
      style={{
        width: "100%",
        height: "100%",
        position: "relative",
        display: "flex",
        flexDirection: "column",
        backgroundColor: "#090d16",
      }}
    >
      <canvas
        ref={canvasRef}
        data-testid="3d-canvas"
        style={{ display: "block", flex: 1 }}
      />
      {fileName && (
        <div
          style={{
            position: "absolute",
            bottom: "var(--space-sm)",
            left: "var(--space-sm)",
            backgroundColor: "rgba(9, 13, 22, 0.84)",
            padding: "2px 8px",
            borderRadius: "var(--radius-sm)",
            color: "var(--color-secondary)",
            fontFamily: "var(--font-ui)",
            fontSize: "0.75rem",
            border: "1px solid var(--color-border)",
            pointerEvents: "none",
          }}
        >
          {fileName}
        </div>
      )}
    </div>
  );
}

export default ThreeDViewer;
