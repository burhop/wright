import { useEffect, useRef } from "react";
import * as THREE from "three";
import { OrbitControls } from "three/addons/controls/OrbitControls.js";
import { STLLoader } from "three/addons/loaders/STLLoader.js";

interface ThreeDViewerProps {
  arrayBuffer: ArrayBuffer;
  fileName?: string;
}

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
    scene.background = new THREE.Color(0x151515); // Calm dark console surface color

    // 2. Create Camera
    const camera = new THREE.PerspectiveCamera(45, width / height, 0.1, 1000);
    camera.position.set(40, 40, 40);

    // 3. Create Renderer
    const renderer = new THREE.WebGLRenderer({ antialias: true, canvas });
    renderer.setSize(width, height);
    renderer.setPixelRatio(Math.min(window.devicePixelRatio, 2));

    // 4. Add Lights
    const ambientLight = new THREE.AmbientLight(0x444444);
    scene.add(ambientLight);

    const dirLight1 = new THREE.DirectionalLight(0xffffff, 0.8);
    dirLight1.position.set(1, 1, 1).normalize();
    scene.add(dirLight1);

    const dirLight2 = new THREE.DirectionalLight(0x555555, 0.4);
    dirLight2.position.set(-1, -1, -1).normalize();
    scene.add(dirLight2);

    // 5. Add Grid & Axis Helpers
    const gridHelper = new THREE.GridHelper(80, 40, 0x333333, 0x222222);
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
        color: 0x4f46e5, // Wright console accent indigo
        specular: 0x222222,
        shininess: 60,
      });

      mesh = new THREE.Mesh(geometry, material);
      scene.add(mesh);

      // Adjust camera distance to fit geometry bounding box
      geometry.computeBoundingSphere();
      const boundingSphere = geometry.boundingSphere;
      if (boundingSphere) {
        const radius = boundingSphere.radius;
        // Position camera based on radius
        camera.position.set(radius * 2.2, radius * 2.2, radius * 2.2);
        camera.lookAt(0, 0, 0);
        // Adjust grid position to fit base
        gridHelper.position.y = -radius * 1.1;

        // Dynamically adjust camera near/far clipping planes based on model size
        camera.near = Math.max(0.001, radius * 0.01);
        camera.far = Math.max(1000, radius * 100);
        camera.updateProjectionMatrix();
      }
    } catch (err) {
      console.error("Failed to parse STL geometry buffer", err);
    }

    // 7. Add Orbit Controls
    const controls = new OrbitControls(camera, renderer.domElement);
    controls.enableDamping = true;
    controls.dampingFactor = 0.05;
    controls.maxDistance = 400;
    
    // Set dynamic minDistance based on bounding sphere radius if available
    const radius = geometry?.boundingSphere?.radius;
    controls.minDistance = radius !== undefined ? Math.max(0.01, radius * 0.1) : 5;

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
        backgroundColor: "#151515",
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
            backgroundColor: "rgba(21, 21, 21, 0.8)",
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
