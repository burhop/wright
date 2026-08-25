import { describe, expect, it } from "vitest";

import {
  createDesignInputHistory,
  reduceDesignInputHistory,
  type DesignInputDocumentDraft,
} from "./design-input-draft";

const longBrief: DesignInputDocumentDraft = {
  documentId: "long-brief",
  name: "long-brief.md",
  mediaType: "text/markdown",
  sizeBytes: 2048,
  textPreview: "A long reusable design brief.",
  textPreviewTruncated: false,
};

const requirements: DesignInputDocumentDraft = {
  documentId: "requirements",
  name: "requirements.pdf",
  mediaType: "application/pdf",
  sizeBytes: 8192,
  textPreview: null,
  textPreviewTruncated: false,
};

describe("design input draft history", () => {
  it("records a whole prompt edit as one reversible command", () => {
    const initial = createDesignInputHistory();
    const prompted = reduceDesignInputHistory(initial, {
      type: "apply",
      command: {
        type: "replace-prompt",
        prompt: "Design a compact enclosure that can be carried safely.",
      },
    });

    expect(prompted.present.prompt).toContain("compact enclosure");
    expect(prompted.present.revision).toBe(1);
    expect(
      reduceDesignInputHistory(prompted, { type: "undo" }).present.prompt,
    ).toBe("");
  });

  it("adds a document batch atomically and removes documents with history", () => {
    const withDocuments = reduceDesignInputHistory(createDesignInputHistory(), {
      type: "apply",
      command: {
        type: "add-documents",
        documents: [longBrief, requirements],
      },
    });

    expect(withDocuments.present.documents).toHaveLength(2);
    expect(withDocuments.present.revision).toBe(1);

    const removed = reduceDesignInputHistory(withDocuments, {
      type: "apply",
      command: { type: "remove-document", documentId: "requirements" },
    });
    expect(removed.present.documents.map(({ name }) => name)).toEqual([
      "long-brief.md",
    ]);
    expect(
      reduceDesignInputHistory(removed, { type: "undo" }).present.documents,
    ).toHaveLength(2);
  });

  it("ignores duplicate documents and clears redo after a new edit", () => {
    const withDocument = reduceDesignInputHistory(createDesignInputHistory(), {
      type: "apply",
      command: { type: "add-documents", documents: [longBrief] },
    });
    expect(
      reduceDesignInputHistory(withDocument, {
        type: "apply",
        command: { type: "add-documents", documents: [longBrief] },
      }),
    ).toBe(withDocument);

    const undone = reduceDesignInputHistory(withDocument, { type: "undo" });
    const replaced = reduceDesignInputHistory(undone, {
      type: "apply",
      command: { type: "replace-prompt", prompt: "New direction" },
    });
    expect(replaced.future).toEqual([]);
  });
});
