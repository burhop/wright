import { describe, expect, it } from "vitest";

import {
  promptRequestRouteCanRun,
  promptRequestRouteIssues,
} from "./prompt-request-routing";

describe("prompt request typed routing", () => {
  it("allows a complete text and image request into a multimodal request input", () => {
    const issues = promptRequestRouteIssues(
      {
        promptPresent: true,
        imageCount: 2,
        documentCount: 0,
        readableDocumentCount: 0,
      },
      "request",
      ["request", "text"],
    );

    expect(issues).toEqual([]);
    expect(promptRequestRouteCanRun(issues)).toBe(true);
  });

  it("reports attachments that an explicit text-only route leaves unused", () => {
    const issues = promptRequestRouteIssues(
      {
        promptPresent: true,
        imageCount: 2,
        documentCount: 1,
        readableDocumentCount: 1,
      },
      "text",
      ["request", "text"],
    );

    expect(issues).toEqual([
      expect.objectContaining({
        code: "ATTACHMENTS_NOT_ROUTED",
        severity: "warning",
      }),
    ]);
    expect(promptRequestRouteCanRun(issues)).toBe(true);
  });

  it("rejects an image-only route when the connected block has no image port", () => {
    const issues = promptRequestRouteIssues(
      {
        promptPresent: true,
        imageCount: 1,
        documentCount: 0,
        readableDocumentCount: 0,
      },
      "images",
      ["request", "text"],
    );

    expect(issues).toContainEqual(
      expect.objectContaining({ code: "OUTPUT_NOT_ACCEPTED" }),
    );
    expect(promptRequestRouteCanRun(issues)).toBe(false);
  });

  it("requires explicit document parsing before an opaque document is bundled", () => {
    const issues = promptRequestRouteIssues(
      {
        promptPresent: true,
        imageCount: 0,
        documentCount: 2,
        readableDocumentCount: 1,
      },
      "request",
      ["request", "text"],
    );

    expect(issues).toContainEqual(
      expect.objectContaining({ code: "DOCUMENT_TEXT_UNAVAILABLE" }),
    );
    expect(promptRequestRouteCanRun(issues)).toBe(false);
  });
});
