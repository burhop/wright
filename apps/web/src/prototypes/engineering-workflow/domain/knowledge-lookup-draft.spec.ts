import { describe, expect, it } from "vitest";

import {
  createKnowledgeLookupHistory,
  reduceKnowledgeLookupHistory,
} from "./knowledge-lookup-draft";

const allowedSourceIds = ["workspace", "connections", "approved-web"];

describe("knowledge lookup draft history", () => {
  it("records a lookup prompt as one reversible command", () => {
    const queried = reduceKnowledgeLookupHistory(
      createKnowledgeLookupHistory(),
      {
        type: "apply",
        command: {
          type: "replace-query",
          query: "Find applicable company standards and preferred fasteners.",
        },
      },
      allowedSourceIds,
    );

    expect(queried.present.query).toContain("company standards");
    expect(queried.present.revision).toBe(1);
    expect(
      reduceKnowledgeLookupHistory(queried, { type: "undo" }, allowedSourceIds)
        .present.query,
    ).toBe("");
  });

  it("selects generic source scopes with undo and redo", () => {
    const withWorkspace = reduceKnowledgeLookupHistory(
      createKnowledgeLookupHistory(),
      {
        type: "apply",
        command: { type: "toggle-source", sourceId: "workspace" },
      },
      allowedSourceIds,
    );
    const withConnections = reduceKnowledgeLookupHistory(
      withWorkspace,
      {
        type: "apply",
        command: { type: "toggle-source", sourceId: "connections" },
      },
      allowedSourceIds,
    );

    expect(withConnections.present.sourceIds).toEqual([
      "workspace",
      "connections",
    ]);
    const undone = reduceKnowledgeLookupHistory(
      withConnections,
      { type: "undo" },
      allowedSourceIds,
    );
    expect(undone.present.sourceIds).toEqual(["workspace"]);
    expect(
      reduceKnowledgeLookupHistory(undone, { type: "redo" }, allowedSourceIds)
        .present.sourceIds,
    ).toEqual(["workspace", "connections"]);
  });

  it("rejects unknown source identities and clears redo on a new edit", () => {
    const initial = createKnowledgeLookupHistory();
    expect(
      reduceKnowledgeLookupHistory(
        initial,
        {
          type: "apply",
          command: { type: "toggle-source", sourceId: "bolt-database" },
        },
        allowedSourceIds,
      ),
    ).toBe(initial);

    const selected = reduceKnowledgeLookupHistory(
      initial,
      {
        type: "apply",
        command: { type: "toggle-source", sourceId: "workspace" },
      },
      allowedSourceIds,
    );
    const undone = reduceKnowledgeLookupHistory(
      selected,
      { type: "undo" },
      allowedSourceIds,
    );
    const queried = reduceKnowledgeLookupHistory(
      undone,
      {
        type: "apply",
        command: { type: "replace-query", query: "Find relevant guidance." },
      },
      allowedSourceIds,
    );
    expect(queried.future).toEqual([]);
  });
});
