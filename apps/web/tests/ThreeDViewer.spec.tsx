import { describe, it, expect, vi } from "vitest";
import { render, screen } from "@testing-library/react";
import "@testing-library/jest-dom";
import * as THREE from "three";
import ThreeDViewer, {
  fitCameraToRadius,
} from "../src/components/common/ThreeDViewer";

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
    render() {}
    dispose() {}
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
      return new THREE.BufferGeometry();
    }
  }
  return {
    STLLoader: MockSTLLoader,
  };
});

describe("ThreeDViewer", () => {
  const mockBuffer = new ArrayBuffer(8);

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
});
