import { afterEach, expect, it, vi } from "vitest";
import robotTelemetry from "../../../../../tests/datasets/engineering-workflows/scenarios/robot-tracking-diagnosis/01-aisle-floor-seam/telemetry.csv?raw";
import {
  render,
  screen,
  fireEvent,
  cleanup,
  act,
} from "@testing-library/react";
import { FileDownloadProvider, RepresentationDownload } from "@wright/ui-kit";
import { downloadNativeFile } from "./native-download";

afterEach(() => {
  cleanup();
  vi.restoreAllMocks();
});
const host = () => ({
  getHostCapabilities: () => ({ downloadFile: {} }),
  downloadFile: vi.fn().mockResolvedValue({}),
});

it("hands exact binary bytes and basename to the public host API without a URL fetch", async () => {
  const app = host();
  const bytes = new Uint8Array([0, 255, 128, 60, 62]);
  const blob = new Blob([bytes], { type: "image/png" });
  expect(await downloadNativeFile(app, blob, "part image.png")).toBe(
    "requested",
  );
  expect(app.downloadFile).toHaveBeenCalledExactlyOnceWith(
    {
      contents: [
        {
          type: "resource",
          resource: {
            uri: "file:///part%20image.png",
            mimeType: "image/png",
            blob: btoa(String.fromCharCode(...bytes)),
          },
        },
      ],
    },
    { timeout: 60_000 },
  );
});
it("does not read bytes or silently fall back when host downloads are unavailable", async () => {
  const app = { getHostCapabilities: () => ({}), downloadFile: vi.fn() };
  const blob = new Blob(["data"]);
  const read = vi.spyOn(blob, "arrayBuffer");
  expect(await downloadNativeFile(app, blob, "part.step")).toBe("unavailable");
  expect(read).not.toHaveBeenCalled();
  expect(app.downloadFile).not.toHaveBeenCalled();
});
it.each([
  "",
  "../part.step",
  "folder/file",
  "folder\\file",
  ".secret",
  "line\nbreak",
])("rejects an invalid download name %j", async (name) => {
  const app = host();
  await expect(
    downloadNativeFile(app, new Blob(["x"]), name),
  ).rejects.toThrow();
  expect(app.downloadFile).not.toHaveBeenCalled();
});
it("rejects oversize bytes and preserves denial and uncertain transport outcomes", async () => {
  const app = host();
  await expect(
    downloadNativeFile(
      app,
      new Blob([new Uint8Array(32 * 1024 * 1024 + 1)]),
      "large.png",
    ),
  ).rejects.toThrow();
  expect(app.downloadFile).not.toHaveBeenCalled();
  app.downloadFile.mockResolvedValueOnce({ isError: true });
  expect(await downloadNativeFile(app, new Blob(["x"]), "part.step")).toBe(
    "declined",
  );
  app.downloadFile.mockRejectedValueOnce(new Error("timeout"));
  await expect(
    downloadNativeFile(app, new Blob(["x"]), "part.step"),
  ).rejects.toThrow("timeout");
  expect(app.downloadFile).toHaveBeenCalledTimes(2); // no automatic retry
});
it("shows progress, suppresses duplicate clicks, and never claims file delivery", async () => {
  let finish!: (value: "requested") => void;
  const request = vi.fn(
    () =>
      new Promise<"requested">((resolve) => {
        finish = resolve;
      }),
  );
  const blob = new Blob(["retained bytes"]);
  render(
    <FileDownloadProvider request={request}>
      <RepresentationDownload blob={blob} name="results/run/image.png" />
    </FileDownloadProvider>,
  );
  fireEvent.click(screen.getByRole("button", { name: "Download exact file" }));
  fireEvent.click(screen.getByRole("button", { name: "Preparing download…" }));
  expect(request).toHaveBeenCalledExactlyOnceWith(blob, "image.png");
  await act(async () => finish("requested"));
  expect(screen.getByRole("status")).toHaveTextContent("Download requested");
  expect(screen.queryByRole("link")).not.toBeInTheDocument();
});
it.each(["declined", "unavailable", "failure"])(
  "shows %s instead of a silent no-op or retry",
  async (result) => {
    const request = vi.fn(
      result === "failure"
        ? async () => {
            throw new Error("private host error");
          }
        : async () => result as "declined" | "unavailable",
    );
    render(
      <FileDownloadProvider request={request}>
        <RepresentationDownload blob={new Blob(["x"])} name="part.step" />
      </FileDownloadProvider>,
    );
    fireEvent.click(
      screen.getByRole("button", { name: "Download exact file" }),
    );
    const message = await screen.findByRole("status");
    expect(message).toHaveTextContent(
      result === "failure"
        ? "not confirmed"
        : result === "declined"
          ? "cancelled or declined"
          : "does not support",
    );
    expect(message).not.toHaveTextContent("private");
    expect(request).toHaveBeenCalledOnce();
  },
);
it("does not apply an older download receipt to a replacement file", async () => {
  let finish!: (value: "requested") => void;
  const request = vi.fn(
    () =>
      new Promise<"requested">((resolve) => {
        finish = resolve;
      }),
  );
  const view = render(
    <FileDownloadProvider request={request}>
      <RepresentationDownload blob={new Blob(["old"])} name="part.step" />
    </FileDownloadProvider>,
  );
  fireEvent.click(screen.getByRole("button", { name: "Download exact file" }));
  view.rerender(
    <FileDownloadProvider request={request}>
      <RepresentationDownload blob={new Blob(["new"])} name="part.step" />
    </FileDownloadProvider>,
  );
  await act(async () => finish("requested"));
  expect(screen.queryByRole("status")).not.toBeInTheDocument();
  expect(
    screen.getByRole("button", { name: "Download exact file" }),
  ).toBeEnabled();
});

it("preserves a different workflow's retained Robot Tracking telemetry through the same delivery port", async () => {
  const bytes = new TextEncoder().encode(robotTelemetry);
  const app = host();
  const blob = new Blob([new Uint8Array(bytes)], { type: "text/csv" });
  render(
    <FileDownloadProvider
      request={(file, name) => downloadNativeFile(app, file, name)}
    >
      <RepresentationDownload blob={blob} name="telemetry.csv" />
    </FileDownloadProvider>,
  );
  fireEvent.click(screen.getByRole("button", { name: "Download exact file" }));
  await screen.findByRole("status");
  expect(app.downloadFile).toHaveBeenCalledExactlyOnceWith(
    {
      contents: [
        {
          type: "resource",
          resource: {
            uri: "file:///telemetry.csv",
            mimeType: "text/csv",
            blob: btoa(String.fromCharCode(...bytes)),
          },
        },
      ],
    },
    { timeout: 60_000 },
  );
});
