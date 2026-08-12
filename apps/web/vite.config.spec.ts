import { describe, expect, it } from "vitest";

import { rewriteSurfaceText } from "./vite.config";

describe("surface development proxy rewriting", () => {
  it("keeps Rivet AI configuration and completion requests inside the preview", () => {
    const authority = encodeURIComponent("s-editor.localhost:8000");
    const rewritten = rewriteSurfaceText(
      'fetch("/wright-ai/config");{"baseUrl":"/wright-ai/v1"}',
      authority,
    );

    expect(rewritten).toContain(
      `fetch("/__wright-surface/${authority}/wright-ai/config")`,
    );
    expect(rewritten).toContain(
      `"baseUrl":"/__wright-surface/${authority}/wright-ai/v1"`,
    );
  });
});
