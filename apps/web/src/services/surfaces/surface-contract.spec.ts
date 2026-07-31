import { describe, expect, it } from "vitest";

import {
  parseSurfaceDescriptor,
  type SurfaceDescriptor,
  type SurfaceSource,
} from "./surface-contract";

const base = {
  schemaVersion: 1,
  surfaceId: "surface-1",
  workspaceId: "workspace-1",
  title: "Surface",
  lifecycle: "declared",
  presentations: [],
  capabilities: [],
  revision: 1,
  createdAt: "2026-07-30T12:00:00Z",
  updatedAt: "2026-07-30T12:00:00Z",
};

const sources: SurfaceSource[] = [
  {
    kind: "file",
    sourceId: "file-1",
    sourceVersion: "revision-1",
    path: "models/bracket.step",
    mediaType: "model/step",
  },
  {
    kind: "display",
    sourceId: "execution-1:loads",
    sourceVersion: "3",
    displayId: "loads",
    revision: 3,
  },
  {
    kind: "live_app",
    sourceId: "brep",
    sourceVersion: "manifest-hash",
    manifestId: "brep",
  },
  {
    kind: "mcp_app",
    sourceId: "server-1:ui://brep/main",
    sourceVersion: "content-hash",
    serverId: "server-1",
    resourceUri: "ui://brep/main",
    contentHash: "content-hash",
  },
  {
    kind: "external_url",
    sourceId: "approval-1",
    sourceVersion: "https://docs.example.test",
    displayUrl: "https://docs.example.test/guide",
    viewOnly: true,
  },
];

describe("Workspace Surface contract", () => {
  it.each(sources)("parses the $kind discriminator", (source) => {
    const descriptor = parseSurfaceDescriptor({ ...base, source });
    expect(descriptor.source.kind).toBe(source.kind);
    expect(descriptor.surfaceId).toBe("surface-1");
    expect(descriptor.revision).toBe(1);
  });

  it("rejects unknown source kinds, schema majors, and authority fields", () => {
    expect(() =>
      parseSurfaceDescriptor({
        ...base,
        source: { kind: "unknown", sourceId: "x", sourceVersion: "1" },
      }),
    ).toThrow(/source.kind/);
    expect(() =>
      parseSurfaceDescriptor({ ...base, schemaVersion: 2, source: sources[0] }),
    ).toThrow(/schemaVersion/);
    expect(() =>
      parseSurfaceDescriptor({
        ...base,
        source: sources[0],
        targetUrl: "http://127.0.0.1:22",
      }),
    ).toThrow(/targetUrl/);
  });

  it.each([0, -1, 1.5, Number.NaN])(
    "rejects malformed revision %s",
    (revision) => {
      expect(() =>
        parseSurfaceDescriptor({ ...base, source: sources[0], revision }),
      ).toThrow(/revision/);
    },
  );

  it("returns an immutable descriptor projection", () => {
    const descriptor: SurfaceDescriptor = parseSurfaceDescriptor({
      ...base,
      source: sources[0],
    });
    expect(Object.isFrozen(descriptor)).toBe(true);
    expect(Object.isFrozen(descriptor.source)).toBe(true);
  });

  it("parses strict capability projections", () => {
    const descriptor = parseSurfaceDescriptor({
      ...base,
      source: sources[0],
      capabilities: [
        { name: "tool", state: "consent_required", riskTier: "mutating" },
      ],
    });
    expect(descriptor.capabilities[0]).toEqual({
      name: "tool",
      state: "consent_required",
      riskTier: "mutating",
    });
    expect(Object.isFrozen(descriptor.capabilities[0])).toBe(true);
    expect(() =>
      parseSurfaceDescriptor({
        ...base,
        source: sources[0],
        capabilities: [{ name: "tool", state: "root", riskTier: "low" }],
      }),
    ).toThrow(/state/);
  });

  it("parses instance authority and presentation eligibility explicitly", () => {
    const descriptor = parseSurfaceDescriptor({
      ...base,
      lifecycle: "ready",
      source: sources[2],
      instance: {
        instanceId: "instance-1",
        generation: 2,
        sharing: "shared",
        readyAt: "2026-07-30T12:00:00Z",
      },
      presentations: [
        { kind: "panel", eligible: true },
        { kind: "browser", eligible: false, reason: "Policy denied" },
      ],
    });
    expect(descriptor.instance).toEqual({
      instanceId: "instance-1",
      generation: 2,
      sharing: "shared",
      readyAt: "2026-07-30T12:00:00Z",
    });
    expect(descriptor.presentations[1]).toEqual({
      kind: "browser",
      eligible: false,
      reason: "Policy denied",
    });
    expect(() =>
      parseSurfaceDescriptor({
        ...base,
        source: sources[2],
        instance: {
          instanceId: "instance-1",
          generation: 2,
          sharing: "global",
        },
      }),
    ).toThrow(/sharing/);
    expect(() =>
      parseSurfaceDescriptor({
        ...base,
        source: sources[2],
        presentations: [{ kind: "popup", eligible: true }],
      }),
    ).toThrow(/presentations\[0\].kind/);
  });
});
