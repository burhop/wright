import { describe, expect, it, vi } from "vitest";

import type {
  FileDescriptor,
  ViewerContribution,
  ViewerProvider,
} from "../viewer-panel/types";
import {
  FileSurfaceAdapter,
  FileSurfaceUnsupportedError,
} from "./file-surface-adapter";

const file: FileDescriptor = {
  id: "/models/bracket.step",
  uri: "/models/bracket.step",
  name: "bracket.step",
  extension: "step",
  mimeType: "model/step",
  metadata: { last_modified: 42 },
};

const provider = () => {
  const document = {
    uri: file.uri,
    type: "three-d",
    isDirty: vi.fn(() => false),
    markClean: vi.fn(),
    dispose: vi.fn(),
  };
  const value: ViewerProvider = {
    id: "three-d-viewer",
    openDocument: vi.fn(async () => document),
    disposeDocument: vi.fn((item) => item.dispose()),
    resolveViewer: vi.fn(async () => undefined),
    save: vi.fn(async () => undefined),
    saveAs: vi.fn(async () => undefined),
    revert: vi.fn(async () => undefined),
    backup: vi.fn(async () => ({
      id: "backup",
      delete: async () => undefined,
    })),
    onDidChangeDocument: vi.fn(() => ({ dispose: vi.fn() })),
    getCapabilities: vi.fn(() => ({
      canEdit: false,
      canAnnotate: false,
      supports3DControls: true,
      prefersIsolation: false,
      supportsMultiView: false,
    })),
  };
  return { value, document };
};

describe("FileSurfaceAdapter", () => {
  it("uses the existing viewer selection and creates a stable file descriptor", async () => {
    const fake = provider();
    const contribution: ViewerContribution = {
      id: "three-d-viewer",
      label: "3D Viewer",
      selector: [{ extension: "step" }],
      priority: "default",
      providerFactory: () => fake.value,
    };
    const registry = { getDefaultViewer: vi.fn(() => contribution) };
    const adapter = new FileSurfaceAdapter(registry);

    const first = await adapter.open(file, {
      mode: "preview",
      sessionId: "session-1",
      workspaceId: "workspace-1",
    });
    const second = await adapter.open(
      { ...file, id: "models\\bracket.step", uri: "models\\bracket.step" },
      {
        mode: "preview",
        sessionId: "session-1",
        workspaceId: "workspace-1",
      },
    );

    expect(registry.getDefaultViewer).toHaveBeenCalledWith(
      expect.objectContaining({ uri: "/models/bracket.step" }),
      "preview",
    );
    expect(first.descriptor.surfaceId).toBe(second.descriptor.surfaceId);
    expect(first.descriptor.source).toMatchObject({
      kind: "file",
      path: "models/bracket.step",
      mediaType: "model/step",
    });
    expect(first.provider).toBe(fake.value);
    expect(first.document).toBe(fake.document);
  });

  it("delegates save and revert and disposes subscription/document exactly once", async () => {
    const fake = provider();
    const subscription = { dispose: vi.fn() };
    vi.mocked(fake.value.onDidChangeDocument).mockReturnValue(subscription);
    const contribution: ViewerContribution = {
      id: "three-d-viewer",
      label: "3D Viewer",
      selector: [{ extension: "step" }],
      priority: "default",
      providerFactory: () => fake.value,
    };
    const adapter = new FileSurfaceAdapter({
      getDefaultViewer: () => contribution,
    });
    const host = await adapter.open(file, {
      mode: "preview",
      sessionId: "session-1",
      workspaceId: "workspace-1",
    });

    await host.save();
    await host.revert();
    host.dispose();
    host.dispose();

    expect(fake.value.save).toHaveBeenCalledTimes(1);
    expect(fake.value.revert).toHaveBeenCalledTimes(1);
    expect(subscription.dispose).toHaveBeenCalledTimes(1);
    expect(fake.value.disposeDocument).toHaveBeenCalledTimes(1);
  });

  it("reports unsupported files without changing the viewer registry", async () => {
    const registry = { getDefaultViewer: vi.fn(() => undefined) };
    const adapter = new FileSurfaceAdapter(registry);
    await expect(
      adapter.open(file, {
        mode: "preview",
        sessionId: "session-1",
        workspaceId: "workspace-1",
      }),
    ).rejects.toBeInstanceOf(FileSurfaceUnsupportedError);
    expect(registry.getDefaultViewer).toHaveBeenCalledTimes(1);
  });
});
