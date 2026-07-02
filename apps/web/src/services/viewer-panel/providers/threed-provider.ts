import * as THREE from "three";
import { OrbitControls } from "three/addons/controls/OrbitControls.js";
import { STLLoader } from "three/addons/loaders/STLLoader.js";
import type {
  FileDescriptor,
  ViewerProvider,
  ViewerDocument,
  PanelHost,
  OpenContext,
  CancellationToken,
  BackupContext,
  BackupHandle,
  ViewerDocumentChangeEvent,
  Event,
} from "../types";
import { workspaceService } from "../../workspace-service";

const VIEWER_BACKGROUND = 0x090d16;
const PART_MATERIAL = 0xd9f3ff;
const PART_SPECULAR = 0x7dd3fc;
const GRID_PRIMARY = 0x1e293b;
const GRID_SECONDARY = 0x0d1220;

export const fitCameraToRadius = (
  camera: THREE.PerspectiveCamera,
  radius: number,
) => {
  const safeRadius = Math.max(radius, 0.001);
  const fov = THREE.MathUtils.degToRad(camera.fov);
  const distance = (safeRadius / Math.sin(fov / 2)) * 1.35;
  const component = distance / Math.sqrt(3);

  camera.position.set(component, component, component);
  camera.lookAt(0, 0, 0);
  camera.near = Math.max(0.00001, safeRadius / 1000);
  camera.far = Math.max(10, distance * 8, safeRadius * 80);
  camera.updateProjectionMatrix();

  return { distance, radius: safeRadius };
};

export interface ThreeDDocument extends ViewerDocument {
  readonly arrayBuffer: ArrayBuffer;
}

class ThreeDDocumentImpl implements ThreeDDocument {
  readonly uri: string;
  readonly type = "threed";
  readonly arrayBuffer: ArrayBuffer;

  constructor(uri: string, arrayBuffer: ArrayBuffer) {
    this.uri = uri;
    this.arrayBuffer = arrayBuffer;
  }

  isDirty() {
    return false;
  }

  markClean() {}

  dispose() {}
}

export class ThreeDProvider implements ViewerProvider<ThreeDDocument> {
  readonly id = "threed-viewer";
  private changeCallbacks = new Set<(e: ViewerDocumentChangeEvent) => void>();

  readonly onDidChangeDocument: Event<ViewerDocumentChangeEvent> = (
    listener,
  ) => {
    this.changeCallbacks.add(listener);
    return {
      dispose: () => {
        this.changeCallbacks.delete(listener);
      },
    };
  };

  async openDocument(
    file: FileDescriptor,
    context: OpenContext,
  ): Promise<ThreeDDocument> {
    const sessionId = context.sessionId;
    if (!sessionId) {
      throw new Error("No active session ID provided");
    }
    const buffer = await workspaceService.getFileContentArrayBuffer(
      sessionId,
      file.uri,
      context.backupId,
    );
    return new ThreeDDocumentImpl(file.uri, buffer);
  }

  disposeDocument(doc: ThreeDDocument) {
    doc.dispose();
  }

  async resolveViewer(
    document: ThreeDDocument,
    panel: PanelHost,
    _mode: string,
    _token: CancellationToken,
  ): Promise<void> {
    const container = panel.container;

    // Clear previous contents of container
    container.innerHTML = "";

    const wrapper = window.document.createElement("div");
    wrapper.style.width = "100%";
    wrapper.style.height = "100%";
    wrapper.style.position = "relative";
    wrapper.style.backgroundColor = "#090d16";

    const canvas = window.document.createElement("canvas");
    canvas.style.display = "block";
    canvas.style.width = "100%";
    canvas.style.height = "100%";
    canvas.setAttribute("data-testid", "3d-canvas");
    wrapper.appendChild(canvas);

    container.appendChild(wrapper);

    const width = container.clientWidth || 300;
    const height = container.clientHeight || 300;

    const scene = new THREE.Scene();
    scene.background = new THREE.Color(VIEWER_BACKGROUND);

    const camera = new THREE.PerspectiveCamera(
      45,
      width / height,
      0.001,
      10000,
    );
    camera.position.set(40, 40, 40);

    const renderer = new THREE.WebGLRenderer({ antialias: true, canvas });
    renderer.setSize(width, height);
    renderer.setPixelRatio(Math.min(window.devicePixelRatio, 2));

    const ambientLight = new THREE.AmbientLight(0xb8d8f0, 0.65);
    scene.add(ambientLight);

    const dirLight1 = new THREE.DirectionalLight(0xffffff, 1.1);
    dirLight1.position.set(1, 1, 1).normalize();
    scene.add(dirLight1);

    const dirLight2 = new THREE.DirectionalLight(0x7dd3fc, 0.45);
    dirLight2.position.set(-1, -1, -1).normalize();
    scene.add(dirLight2);

    const gridHelper = new THREE.GridHelper(
      80,
      40,
      GRID_PRIMARY,
      GRID_SECONDARY,
    );
    gridHelper.position.y = -10;
    scene.add(gridHelper);

    const loader = new STLLoader();
    let mesh: THREE.Mesh | null = null;
    let geometry: THREE.BufferGeometry | null = null;
    let material: THREE.MeshPhongMaterial | null = null;

    try {
      geometry = loader.parse(document.arrayBuffer);
      geometry.center();

      material = new THREE.MeshPhongMaterial({
        color: PART_MATERIAL,
        specular: PART_SPECULAR,
        shininess: 60,
      });

      mesh = new THREE.Mesh(geometry, material);
      scene.add(mesh);

      geometry.computeBoundingSphere();
      const boundingSphere = geometry.boundingSphere;
      if (boundingSphere) {
        const { radius } = fitCameraToRadius(camera, boundingSphere.radius);
        gridHelper.position.y = -radius * 1.1;
        const gridSize = Math.max(0.1, radius * 4);
        gridHelper.scale.setScalar(gridSize / 80);
      }
    } catch (err) {
      console.error(
        "Failed to parse STL geometry buffer in pluggable viewer",
        err,
      );
    }

    const controls = new OrbitControls(camera, renderer.domElement);
    controls.enableDamping = true;
    controls.dampingFactor = 0.05;
    const radius = geometry?.boundingSphere?.radius;
    const fitDistance =
      radius !== undefined ? fitCameraToRadius(camera, radius).distance : 40;
    controls.minDistance =
      radius !== undefined ? Math.max(0.01, radius * 0.02) : 1;
    controls.maxDistance = Math.max(
      1,
      fitDistance * 12,
      (radius || 0.001) * 40,
    );

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

    let animationFrameId: number;
    const animate = () => {
      animationFrameId = requestAnimationFrame(animate);
      controls.update();
      renderer.render(scene, camera);
    };
    animate();

    const cleanUp = () => {
      cancelAnimationFrame(animationFrameId);
      resizeObserver.disconnect();
      controls.dispose();
      if (geometry) geometry.dispose();
      if (material) material.dispose();
      if (mesh) scene.remove(mesh);
      scene.remove(gridHelper);
      renderer.dispose();
    };

    panel.onDidDispose(() => {
      cleanUp();
    });
  }

  async save(
    _document: ThreeDDocument,
    _token: CancellationToken,
  ): Promise<void> {}

  async saveAs(
    _document: ThreeDDocument,
    _destination: FileDescriptor,
    _token: CancellationToken,
  ): Promise<void> {}

  async revert(
    _document: ThreeDDocument,
    _token: CancellationToken,
  ): Promise<void> {}

  async backup(
    document: ThreeDDocument,
    _context: BackupContext,
    _token: CancellationToken,
  ): Promise<BackupHandle> {
    return {
      id: "backup-" + document.uri,
      delete: async () => {},
    };
  }

  getCapabilities(_file: FileDescriptor, _mode: string) {
    return {
      canEdit: false,
      canAnnotate: false,
      supports3DControls: true,
      prefersIsolation: false,
      supportsMultiView: false,
    };
  }
}

export default ThreeDProvider;
