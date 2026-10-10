import {
  act,
  cleanup,
  render,
  screen,
  waitFor,
  within,
} from "@testing-library/react";
import { afterEach, expect, it, vi } from "vitest";
import { RepresentationViewer } from "@wright/ui-kit";

afterEach(() => {
  cleanup();
  vi.restoreAllMocks();
});
function blob(text: string, type = "text/markdown") {
  const result = new Blob([text], { type });
  Object.defineProperty(result, "text", { value: async () => text });
  return result;
}
const raw = JSON.stringify({
  schema_version: "wright.process-validation/1",
  id: "assessment-one",
  attempt_id: "attempt-one",
  profile: {},
  request: {},
  summary: {},
  checks: [],
});
const original = blob(raw, "application/json");

it("reads a verified report, shows the exact source on demand, and signals readiness only after presentation", async () => {
  let finish!: (blob: Blob) => void;
  const read = vi.fn(
    (_signal: AbortSignal) =>
      new Promise<Blob>((resolve) => {
        finish = resolve;
      }),
  );
  const ready = vi.fn();
  render(
    <RepresentationViewer
      blob={original}
      title="assessment.json"
      readValidationReport={read}
      onReady={ready}
    />,
  );
  await waitFor(() =>
    expect(read).toHaveBeenCalledWith(expect.any(AbortSignal)),
  );
  expect(ready).not.toHaveBeenCalled();
  await act(async () =>
    finish(
      blob("# Engineering assessment\n\n**HOLD**\n\nHuman review required."),
    ),
  );
  expect(
    screen.getByRole("heading", { name: "Engineering assessment" }),
  ).toBeVisible();
  expect(screen.getByText("Human review required.")).toBeVisible();
  expect(
    screen.getByText("Exact assessment record").closest("details"),
  ).not.toHaveAttribute("open");
  expect(screen.getByText(raw)).not.toBeVisible();
  expect(ready).toHaveBeenCalledTimes(1);
});

it.each([
  undefined,
  async () => {
    throw new Error("Unavailable");
  },
  async () => blob("<script>bad</script>", "text/html"),
  async () => blob("x".repeat(2 * 1024 * 1024 + 1)),
])(
  "keeps the original when the scoped report cannot be shown",
  async (read) => {
    const ready = vi.fn();
    render(
      <RepresentationViewer
        blob={original}
        title="assessment.json"
        readValidationReport={read}
        onReady={ready}
      />,
    );
    await screen.findByText(/readable assessment is unavailable/);
    expect(screen.getByText(raw)).toBeInTheDocument();
    expect(ready).toHaveBeenCalledTimes(1);
  },
);

it("aborts and ignores a report from the previous file", async () => {
  let finish!: (blob: Blob) => void;
  const read = vi.fn(
    (_signal: AbortSignal) =>
      new Promise<Blob>((resolve) => {
        finish = resolve;
      }),
  );
  const view = render(
    <RepresentationViewer
      blob={original}
      title="old.json"
      readValidationReport={read}
    />,
  );
  await waitFor(() => expect(read).toHaveBeenCalled());
  const signal = read.mock.calls[0][0] as AbortSignal;
  view.rerender(
    <RepresentationViewer
      blob={blob("New evidence", "text/plain")}
      title="new.txt"
    />,
  );
  await screen.findByText("New evidence");
  expect(signal.aborted).toBe(true);
  await act(async () => finish(blob("# Old report")));
  expect(
    screen.queryByRole("heading", { name: "Old report" }),
  ).not.toBeInTheDocument();
});

it("does not request reports for ordinary JSON or run instructions from Markdown", async () => {
  const read = vi.fn();
  const view = render(
    <RepresentationViewer
      blob={blob('{"value":3}', "application/json")}
      title="data.json"
      readValidationReport={read}
    />,
  );
  await screen.findByText('{"value":3}');
  expect(read).not.toHaveBeenCalled();
  view.rerender(
    <RepresentationViewer
      blob={original}
      title="assessment.json"
      readValidationReport={async () =>
        blob("# Record\n[Open](https://invalid)\n<script>execute()</script>")
      }
    />,
  );
  await screen.findByRole("heading", { name: "Record" });
  expect(screen.queryByRole("link", { name: "Open" })).not.toBeInTheDocument();
  expect(view.container.querySelector("script")).toBeNull();
});

it("renders escaped finding text exactly without turning it into active content", async () => {
  // Matches the backend report-escaping contract, including literal entity text.
  const report =
    "# Engineering assessment\n\nRequired reader &#x27;probe&#x27; is unavailable.\n\n" +
    "&quot;P2&quot; &amp; &lt;raw&gt; \\[link\\](https://invalid) \\#tag\\_1\n\n" +
    "Literal &amp;\\#x27; and &amp;lt;\n\n&lt;script&gt;alert(1)&lt;/script&gt;";
  const view = render(
    <RepresentationViewer
      blob={original}
      title="assessment.json"
      readValidationReport={async () => blob(report)}
    />,
  );
  await screen.findByRole("heading", { name: "Engineering assessment" });
  const contents = within(
    screen.getByRole("article", { name: "Document contents" }),
  );
  expect(
    contents.getByText("Required reader 'probe' is unavailable."),
  ).toBeVisible();
  expect(
    contents.getByText(
      (_, element) =>
        element?.tagName === "P" &&
        element.textContent === '"P2" & <raw> [link](https://invalid) #tag_1',
    ),
  ).toBeVisible();
  expect(contents.getByText("Literal &#x27; and &lt;")).toBeVisible();
  expect(contents.getByText("<script>alert(1)</script>")).toBeVisible();
  expect(view.container.querySelector("script,a,img,iframe,raw")).toBeNull();
});
