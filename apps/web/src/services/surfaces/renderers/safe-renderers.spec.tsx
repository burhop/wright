import { render, screen, within } from "@testing-library/react";
import { describe, expect, it } from "vitest";

import { SafeRepresentationRenderer } from "./safe-renderers";

describe("safe Workspace Surface renderers", () => {
  it("renders text as inert preformatted content", () => {
    render(
      <SafeRepresentationRenderer
        description="Raw solver output"
        representation={{
          mediaType: "text/plain",
          encoding: "utf-8",
          data: "<script>not markup</script>",
        }}
      />,
    );
    expect(screen.getByRole("region", { name: "Raw solver output" })).toHaveTextContent(
      "<script>not markup</script>",
    );
    expect(document.querySelector("script")).toBeNull();
  });

  it("renders table JSON with semantic headers and an accessible caption", () => {
    render(
      <SafeRepresentationRenderer
        description="Load by time table"
        representation={{
          mediaType: "application/vnd.wright.table+json",
          encoding: "json",
          data: { columns: ["Time", "Load"], data: [[0, 10], [1, 12]] },
        }}
      />,
    );
    const table = screen.getByRole("table", { name: "Load by time table" });
    expect(within(table).getByRole("columnheader", { name: "Time" })).toBeVisible();
    expect(within(table).getByRole("cell", { name: "12" })).toBeVisible();
  });

  it("renders raster images from data only and carries required alt text", () => {
    render(
      <SafeRepresentationRenderer
        description="Stress contour"
        representation={{
          mediaType: "image/png",
          encoding: "base64",
          data: "iVBORw0KGgo=",
        }}
      />,
    );
    const image = screen.getByRole("img", { name: "Stress contour" });
    expect(image).toHaveAttribute("src", "data:image/png;base64,iVBORw0KGgo=");
    expect(image).toHaveAttribute("draggable", "false");
  });

  it("sanitizes SVG and passive HTML into locked documents", () => {
    const { rerender } = render(
      <SafeRepresentationRenderer
        description="Safe vector"
        representation={{
          mediaType: "image/svg+xml",
          encoding: "utf-8",
          data: '<svg onload="bad()"><script>bad()</script><circle r="2"/></svg>',
        }}
      />,
    );
    let region = screen.getByRole("img", { name: "Safe vector" });
    expect(region.innerHTML).toContain("circle");
    expect(region.innerHTML).not.toMatch(/script|onload/i);

    rerender(
      <SafeRepresentationRenderer
        description="Safe explanation"
        representation={{
          mediaType: "text/html",
          encoding: "utf-8",
          data: '<p>Result</p><a href="javascript:bad()">bad</a><script>bad()</script>',
          activeHtml: false,
        }}
      />,
    );
    region = screen.getByRole("document", { name: "Safe explanation" });
    expect(region).toHaveAttribute("data-wright-document-locked", "true");
    expect(region.innerHTML).toContain("Result");
    expect(region.innerHTML).not.toMatch(/javascript:|script/i);
  });

  it("fails closed for unsupported media or active HTML", () => {
    expect(() =>
      render(
        <SafeRepresentationRenderer
          description="Unsafe"
          representation={{
            mediaType: "text/html",
            encoding: "utf-8",
            data: "<button>active</button>",
            activeHtml: true,
          }}
        />,
      ),
    ).toThrow(/isolated/);
  });
});
