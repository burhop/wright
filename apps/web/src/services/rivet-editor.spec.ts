import { describe, expect, it } from "vitest";

import {
  directRivetCanvasFrameUrl,
  directRivetEditorUrl,
} from "./rivet-editor";

describe("directRivetEditorUrl", () => {
  it("does not guess an unmanaged loopback editor", () => {
    expect(directRivetEditorUrl({})).toBeNull();
  });

  it("honors an explicitly configured editor URL", () => {
    expect(
      directRivetEditorUrl({
        VITE_RIVET_DIRECT_EDITOR_URL: "http://localhost:9190/",
      }),
    ).toBe("http://localhost:9190/");
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
