import { afterEach, expect, it, vi } from "vitest";
import {
  cleanup,
  fireEvent,
  render,
  screen,
  waitFor,
} from "@testing-library/react";
import { RepresentationViewer } from "@wright/ui-kit";

afterEach(() => {
  cleanup();
  vi.restoreAllMocks();
});
const sha = "a".repeat(64);
const original = new Blob(["%PDF-1.7\n".padEnd(250000)], {
  type: "application/pdf",
});
const png =
  "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAQAAAC1HAwCAAAAC0lEQVR42mP8/x8AAwMCAO+a1V8AAAAASUVORK5CYII=";
function pageBlob(page: number, changes = {}) {
  return new Blob(
    [
      JSON.stringify({
        format: "wright.pdf.page.v1",
        source_sha256: sha,
        page,
        page_count: 2,
        width: 1,
        height: 1,
        png_base64: png,
        ...changes,
      }),
    ],
    { type: "application/vnd.wright.pdf-page+json" },
  );
}

it("renders an engineering-sized PDF through exact passive reads and paginates", async () => {
  vi.spyOn(URL, "createObjectURL").mockReturnValue("blob:page");
  vi.spyOn(URL, "revokeObjectURL").mockImplementation(() => undefined);
  const read = vi.fn(async (page: number) => pageBlob(page));
  const ready = vi.fn();
  render(
    <RepresentationViewer
      blob={original}
      title="drawing.pdf"
      sourceSha256={sha}
      readPdfPage={read}
      onReady={ready}
    />,
  );
  const image = await screen.findByAltText("drawing.pdf · page 1");
  expect(
    screen.queryByText(/exceeds the supported preview size/),
  ).not.toBeInTheDocument();
  expect(read).toHaveBeenCalledWith(1, expect.any(AbortSignal));
  fireEvent.load(image);
  expect(ready).toHaveBeenCalledTimes(1);
  fireEvent.click(screen.getByRole("button", { name: "Enlarge drawing" }));
  expect(screen.getByRole("region", { name: "PDF page" })).toHaveClass(
    "is-full-size",
  );
  fireEvent.click(screen.getByRole("button", { name: "Fit drawing" }));
  expect(screen.getByRole("region", { name: "PDF page" })).not.toHaveClass(
    "is-full-size",
  );
  fireEvent.click(screen.getByRole("button", { name: "Next page" }));
  await screen.findByAltText("drawing.pdf · page 2");
  expect(read).toHaveBeenCalledWith(2, expect.any(AbortSignal));
  expect(screen.getByRole("button", { name: "Next page" })).toBeDisabled();
  expect(screen.queryByAltText("drawing.pdf · page 1")).not.toBeInTheDocument();
});

it.each([
  { source_sha256: "b".repeat(64) },
  { page: 2 },
  { width: 1801 },
  { png_base64: "bad" },
])("refuses mismatched PDF evidence %s", async (changes) => {
  render(
    <RepresentationViewer
      blob={original}
      title="drawing.pdf"
      sourceSha256={sha}
      readPdfPage={async (page) => pageBlob(page, changes)}
    />,
  );
  await screen.findByText(/could not be previewed/);
  expect(screen.queryByRole("img")).not.toBeInTheDocument();
});

it("discards a late page from the previous PDF", async () => {
  vi.spyOn(URL, "createObjectURL").mockReturnValue("blob:page");
  vi.spyOn(URL, "revokeObjectURL").mockImplementation(() => undefined);
  let finish!: (blob: Blob) => void;
  const oldRead = vi.fn(
    () =>
      new Promise<Blob>((resolve) => {
        finish = resolve;
      }),
  );
  const view = render(
    <RepresentationViewer
      blob={original}
      title="old.pdf"
      sourceSha256={sha}
      readPdfPage={oldRead}
    />,
  );
  await waitFor(() => expect(oldRead).toHaveBeenCalled());
  const current = new Blob(["%PDF-new"], { type: "application/pdf" });
  view.rerender(
    <RepresentationViewer
      blob={current}
      title="new.pdf"
      sourceSha256={sha}
      readPdfPage={async (page) => pageBlob(page)}
    />,
  );
  await screen.findByAltText("new.pdf · page 1");
  finish(pageBlob(1));
  expect(screen.queryByAltText("old.pdf · page 1")).not.toBeInTheDocument();
});
