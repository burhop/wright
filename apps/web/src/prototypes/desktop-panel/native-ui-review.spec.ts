import { afterEach, expect, it, vi } from "vitest";
import type { McpUiHostContext } from "@modelcontextprotocol/ext-apps";
import {
  captureUiReview,
  uiReviewFile,
  type ReviewEvent,
} from "./native-ui-review";

afterEach(() => {
  document.body.innerHTML = "";
  vi.restoreAllMocks();
});
const location = {
  active_surface: "home" as const,
  editor_has_unsaved_changes: false,
};
function surface() {
  document.body.innerHTML =
    '<main id="editor"><button data-testid="review-fixture">Private document title</button><input value="secret-form-value"><textarea>private-source-body</textarea></main>';
  vi.spyOn(Element.prototype, "getBoundingClientRect").mockImplementation(
    function (this: Element) {
      return new DOMRect(this.tagName === "BUTTON" ? 900 : 0, 0, 200, 30);
    },
  );
  return document.getElementById("editor")!;
}
it("captures real control clipping and exact target without copying text or form values", () => {
  const root = surface();
  const report = captureUiReview(
    root,
    { theme: "dark", containerDimensions: { width: 1024, height: 768 } },
    location,
    [],
    root.querySelector("button")!,
  );
  expect(report.selected_element).toMatchObject({
    horizontal_clip: true,
    control_index: 0,
    relative_selector: "button:nth-of-type(1)",
  });
  expect(report.host).toMatchObject({
    available: true,
    theme: "dark",
    container_dimensions: { width: 1024, height: 768 },
  });
  const text = JSON.stringify(report);
  for (const secret of [
    "Private document title",
    "secret-form-value",
    "private-source-body",
  ])
    expect(text).not.toContain(secret);
  expect(report.build.resource_uri).toBeNull();
});
it("allowlists host signals and bounds retained observations", () => {
  const root = surface();
  const events = Array.from({ length: 100 }, (_, elapsed_ms): ReviewEvent => ({
    elapsed_ms,
    kind: "resize",
  }));
  const report = captureUiReview(
    root,
    {
      arbitrary_secret: "not-allowed",
      styles: {
        variables: {
          "--font-sans": "url(secret)",
          "--color-text-primary": "#eee",
        },
        css: { fonts: "private-font-url" },
      },
      toolInfo: {
        id: "secret-id",
        tool: { name: "private-tool", inputSchema: { type: "object" } },
      },
    } as unknown as McpUiHostContext, // Exercise partial wire context, including unknown host fields.
    location,
    events,
  );
  expect(report.recent_events).toHaveLength(20);
  expect(report.host.style_variables).toEqual({
    "--color-text-primary": "#eee",
  });
  expect(JSON.stringify(report)).not.toMatch(
    /arbitrary_secret|not-allowed|private-font-url|secret-id|private-tool|url\(secret\)/,
  );
});
it("keeps missing host context explicit and rejects a target outside Wright", () => {
  const report = captureUiReview(
    surface(),
    undefined,
    location,
    [],
    document.body,
  );
  expect(report.host.available).toBe(false);
  expect(report.host.theme).toBeNull();
  expect(report.selected_element).toBeNull();
});
it("bounds control sampling and report bytes", () => {
  const root = surface();
  root.innerHTML = "<button>not captured</button>".repeat(100);
  const report = captureUiReview(root, undefined, location, []);
  expect(report.controls).toHaveLength(80);
  expect(report.controls_truncated).toBe(true);
  const file = uiReviewFile(report, "bounded comment");
  expect(file.size).toBeLessThanOrEqual(65536);
  expect(file.name).toMatch(/^wright-ui-review-[a-f0-9-]+\.json$/);
  expect(() =>
    uiReviewFile({ ...report, limits: ["a".repeat(65536)] }, ""),
  ).toThrow(/bounded/);
});
