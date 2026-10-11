import { describe, it, expect, vi } from "vitest";
import { render, screen, fireEvent, waitFor } from "@testing-library/react";
import "@testing-library/jest-dom";
import * as THREE from "three";
import ThreeDViewer, {
  fitCameraToRadius,
} from "../src/components/common/ThreeDViewer";
import { ToolpathViewer, parseToolpaths } from "@wright/ui-kit";

const rendering = vi.hoisted(() => ({ render: vi.fn(), dispose: vi.fn() }));

// Mock ResizeObserver for JSDOM environment
class MockResizeObserver {
  observe = vi.fn();
  unobserve = vi.fn();
  disconnect = vi.fn();
}
globalThis.ResizeObserver = MockResizeObserver;

// Mock WebGLRenderer to bypass jsdom WebGL limitations
vi.mock("three", async () => {
  const original = (await vi.importActual("three")) as typeof import("three");
  class MockWebGLRenderer {
    domElement = document.createElement("canvas");
    setSize() {}
    setPixelRatio() {}
    render(scene: unknown) {
      rendering.render(scene);
    }
    dispose() {
      rendering.dispose();
    }
  }
  return {
    ...original,
    WebGLRenderer: MockWebGLRenderer,
  };
});

// Mock OrbitControls
vi.mock("three/examples/jsm/controls/OrbitControls.js", () => {
  class MockOrbitControls {
    update() {}
    dispose() {}
    enableDamping = false;
    dampingFactor = 0;
    maxDistance = 0;
    minDistance = 0;
  }
  return {
    OrbitControls: MockOrbitControls,
  };
});

// Mock STLLoader
vi.mock("three/examples/jsm/loaders/STLLoader.js", () => {
  class MockSTLLoader {
    parse() {
      const geometry = new THREE.BufferGeometry();
      geometry.setAttribute(
        "position",
        new THREE.Float32BufferAttribute([0, 0, 0, 1, 0, 0, 0, 1, 0], 3),
      );
      geometry.computeVertexNormals();
      return geometry;
    }
  }
  return {
    STLLoader: MockSTLLoader,
  };
});

describe("ThreeDViewer", () => {
  const mockBuffer = new ArrayBuffer(84);

  it("renders the canvas element and displays the file name", () => {
    render(<ThreeDViewer arrayBuffer={mockBuffer} fileName="gearbox.stl" />);

    const canvas = screen.getByTestId("3d-canvas");
    expect(canvas).toBeInTheDocument();
    expect(screen.getByText("gearbox.stl")).toBeInTheDocument();
  });

  it("fits sub-unit STL models without clamping them to radius 1", () => {
    const camera = new THREE.PerspectiveCamera(45, 1, 0.001, 10000);

    const { distance, radius } = fitCameraToRadius(camera, 0.09);

    expect(radius).toBeCloseTo(0.09);
    expect(distance).toBeLessThan(1);
    expect(camera.far).toBeLessThan(20);
  });

  it("discloses an invalid bounded representation rather than claiming a rendered model", () => {
    render(
      <ThreeDViewer arrayBuffer={new ArrayBuffer(8)} fileName="invalid.stl" />,
    );
    expect(screen.getByRole("alert")).toHaveTextContent(
      "3D view is unavailable",
    );
    expect(screen.queryByTestId("3d-canvas")).not.toBeInTheDocument();
  });

  it("shows actual paths through every layer and disposes the renderer on close", async () => {
    const hash = "a".repeat(64);
    const document = parseToolpaths(
      {
        format: "wright.gcode.toolpaths.v1",
        package_sha256: hash,
        classification_source: "gcode_feature_comments",
        layers: [
          { index: 1, z: 0.2, model: [[0, 0, 5, 0]], support: [] },
          { index: 2, z: 0.4, model: [[0, 1, 5, 1]], support: [] },
        ],
      },
      hash,
    );
    const { unmount } = render(<ToolpathViewer document={document} />);
    expect(screen.getByText(/Layers 1–2 of 2/)).toBeInTheDocument();
    expect(screen.getByLabelText("Model paths")).toBeChecked();
    fireEvent.change(screen.getByRole("slider"), { target: { value: 1 } });
    expect(screen.getByText(/Layers 1–1 of 2/)).toBeInTheDocument();
    await waitFor(() => {
      const scene = rendering.render.mock.calls.at(-1)?.[0] as THREE.Scene;
      const lines = scene.children.filter(
        (object) =>
          object instanceof THREE.LineSegments &&
          !(object instanceof THREE.GridHelper),
      );
      expect(lines).toHaveLength(2);
      expect(lines.filter((object) => object.visible)).toHaveLength(1);
    });
    const calls = rendering.dispose.mock.calls.length;
    unmount();
    expect(rendering.dispose).toHaveBeenCalledTimes(calls + 1);
  });
});
