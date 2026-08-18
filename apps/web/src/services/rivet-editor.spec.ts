import { describe, expect, it } from "vitest";

import {
  directRivetCanvasFrameUrl,
  directRivetEditorUrl,
  workspaceRivetWorkflowSlug,
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
      "http://127.0.0.1:9180/?workflow=fixture&parentOrigin=http%3A%2F%2F127.0.0.1%3A4173&artifactRevision=6b12fce1",
    );
  });

  it("recognizes only canonical saved workflow files", () => {
    expect(
      workspaceRivetWorkflowSlug("/workflows/rivet/workflow.rivet-project"),
    ).toBe("rivet");
    expect(
      workspaceRivetWorkflowSlug(
        "workflows\\chatter-review\\workflow.rivet-project",
      ),
    ).toBe("chatter-review");
    expect(
      workspaceRivetWorkflowSlug("/notes/workflow.rivet-project"),
    ).toBeNull();
    expect(
      workspaceRivetWorkflowSlug("/workflows/rivet/copy.rivet-project"),
    ).toBeNull();
    expect(
      workspaceRivetWorkflowSlug("/workflows/../workflow.rivet-project"),
    ).toBeNull();
  });
});
