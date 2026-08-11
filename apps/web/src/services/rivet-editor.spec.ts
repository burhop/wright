import { describe, expect, it } from "vitest";

import {
  directRivetCanvasFrameUrl,
  directRivetEditorUrl,
} from "./rivet-editor";

describe("directRivetEditorUrl", () => {
  it("uses the retained local editor in packaged builds", () => {
    expect(
      directRivetEditorUrl({}, { protocol: "http:", hostname: "127.0.0.1" }),
    ).toBe("http://127.0.0.1:9180/");
  });

  it("honors an explicitly configured editor URL", () => {
    expect(
      directRivetEditorUrl(
        { VITE_RIVET_DIRECT_EDITOR_URL: "http://localhost:9190/" },
        { protocol: "http:", hostname: "127.0.0.1" },
      ),
    ).toBe("http://localhost:9190/");
  });

  it("does not guess a loopback editor for remote deployments", () => {
    expect(
      directRivetEditorUrl({}, { protocol: "https:", hostname: "wright.example" }),
    ).toBeNull();
  });

  it("passes only the exact Wright origin to the isolated canvas", () => {
    expect(
      directRivetCanvasFrameUrl(
        "http://127.0.0.1:9180/?workflow=fixture",
        "http://127.0.0.1:4173/workspaces/ignored",
      ),
    ).toBe(
      "http://127.0.0.1:9180/?workflow=fixture&parentOrigin=http%3A%2F%2F127.0.0.1%3A4173&artifactRevision=db4d86e7",
    );
  });
});
