import * as THREE from "three";
import { OrbitControls } from "three/addons/controls/OrbitControls.js";
import { STLLoader } from "three/addons/loaders/STLLoader.js";

const decode = (encoded) => {
  const raw = atob(encoded);
  const bytes = new Uint8Array(raw.length);
  for (let index = 0; index < raw.length; index += 1)
    bytes[index] = raw.charCodeAt(index);
  return bytes.buffer;
};

const mount = (container, encoded, label) => {
  if (!container || container.dataset.viewerMounted === "true") return;
  container.dataset.viewerMounted = "true";
  const canvas = document.createElement("canvas");
  canvas.setAttribute("role", "img");
  canvas.setAttribute("aria-label", `Interactive 3D view of ${label}`);
  container.append(canvas);

  const renderer = new THREE.WebGLRenderer({
    canvas,
    antialias: true,
    alpha: false,
  });
  renderer.setPixelRatio(Math.min(window.devicePixelRatio || 1, 2));
  renderer.setClearColor(0x131c2b, 1);
  renderer.outputColorSpace = THREE.SRGBColorSpace;

  const scene = new THREE.Scene();
  const camera = new THREE.PerspectiveCamera(34, 1, 0.01, 100000);
  camera.up.set(0, 0, 1);
  scene.add(new THREE.HemisphereLight(0xffffff, 0x31494a, 2.1));
  const key = new THREE.DirectionalLight(0xffffff, 2.8);
  key.position.set(4, 6, 5);
  scene.add(key);
  const fill = new THREE.DirectionalLight(0x80bfae, 1.2);
  fill.position.set(-4, 2, -3);
  scene.add(fill);

  const geometry = new STLLoader().parse(decode(encoded));
  geometry.computeVertexNormals();
  geometry.center();
  const material = new THREE.MeshStandardMaterial({
    color: 0xa9b4b1,
    metalness: 0.2,
    roughness: 0.58,
  });
  const mesh = new THREE.Mesh(geometry, material);
  scene.add(mesh);

  const box = new THREE.Box3().setFromObject(mesh);
  const size = box.getSize(new THREE.Vector3());
  const radius = Math.max(size.x, size.y, size.z, 0.001);
  camera.near = Math.max(radius / 1000, 0.001);
  camera.far = radius * 100;
  const controls = new OrbitControls(camera, canvas);
  controls.enableDamping = true;
  controls.dampingFactor = 0.08;
  controls.minDistance = radius * 0.45;
  controls.maxDistance = radius * 12;
  controls.target.set(0, 0, 0);
  controls.update();

  let width = 0;
  let height = 0;
  const fit = () => {
    const vertical = THREE.MathUtils.degToRad(camera.fov) / 2;
    const horizontal = Math.atan(Math.tan(vertical) * camera.aspect);
    const distance =
      (size.length() / 2 / Math.sin(Math.min(vertical, horizontal))) * 1.12;
    camera.position.copy(
      new THREE.Vector3(1.35, -1.1, 1.45).normalize().multiplyScalar(distance),
    );
    controls.target.set(0, 0, 0);
    camera.lookAt(controls.target);
    camera.updateProjectionMatrix();
    controls.update();
  };
  const reset = document.createElement("button");
  reset.className = "model-reset";
  reset.setAttribute("aria-label", "Fit model to view");
  reset.title = "Fit model to view";
  reset.textContent = "\u21bb";
  reset.addEventListener("click", fit);
  container.append(reset);
  const resize = () => {
    const bounds = container.getBoundingClientRect();
    const nextWidth = Math.max(1, Math.round(bounds.width));
    const nextHeight = Math.max(1, Math.round(bounds.height));
    if (nextWidth === width && nextHeight === height) return;
    width = nextWidth;
    height = nextHeight;
    renderer.setSize(width, height, false);
    camera.aspect = width / height;
    fit();
  };
  const observer = new ResizeObserver(resize);
  observer.observe(container);

  let frame;
  const render = () => {
    resize();
    controls.update();
    renderer.render(scene, camera);
    frame = requestAnimationFrame(render);
  };
  render();
  container.dataset.viewerState = "ready";

  container.viewerDispose = () => {
    cancelAnimationFrame(frame);
    observer.disconnect();
    controls.dispose();
    geometry.dispose();
    material.dispose();
    renderer.dispose();
    renderer.forceContextLoss();
  };
};

window.WrightSTLViewer = { mount };
