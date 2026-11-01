import { afterEach, expect, it, vi } from "vitest";
import {
  act,
  cleanup,
  fireEvent,
  render,
  screen,
  waitFor,
} from "@testing-library/react";
import { NativeFileUpload } from "./NativeFileUpload";

const workspace = {
  workspace_id: "a",
  session_id: "chat-a",
  workspace_name: "A",
  available: true,
  reason: null,
};
const data = new Uint8Array([0, 255, 60, 62, 13, 10]);
const digest =
  "9c17195371edce04de3f349ccc57d389a1ca5c687a1c6a0d00153227fe52987e";
const path = `uploads/${digest}/part.step`;
const encoded = btoa(String.fromCharCode(...data));
const doc = {
  workspace_id: "a",
  session_id: "chat-a",
  filename: "part.step",
  path,
  sha256: digest,
  bytes: data.length,
};
const reply = (document = doc) => ({
  content: [],
  structuredContent: { ok: true, document },
});
const read = (extra = {}) => ({
  content: [],
  structuredContent: {
    ...doc,
    supported: true,
    content_base64: encoded,
    ...extra,
  },
});
afterEach(() => {
  cleanup();
  vi.restoreAllMocks();
});

function show(call = vi.fn().mockResolvedValue(reply()), onUploaded = vi.fn()) {
  const view = render(
    <NativeFileUpload
      call={call}
      workspace={workspace}
      onUploaded={onUploaded}
    />,
  );
  fireEvent.change(screen.getByLabelText(/Choose input file/), {
    target: { files: [new File([data], "part.step")] },
  });
  return { call, onUploaded, ...view };
}

it("saves an explicitly prepared report through the same scoped upload and receipt checks", async () => {
  const call = vi.fn().mockResolvedValue(reply());
  const onUploaded = vi.fn();
  const prepare = vi.fn(() => new File([data], "part.step"));
  render(
    <NativeFileUpload
      call={call}
      workspace={workspace}
      onUploaded={onUploaded}
      preparedFile={prepare}
      actionLabel="Save UI report"
      help="Only the prepared report is saved."
    />,
  );
  expect(screen.queryByLabelText(/Choose input file/)).toBeNull();
  expect(call).not.toHaveBeenCalled();
  expect(prepare).not.toHaveBeenCalled();
  const save = screen.getByRole("button", { name: "Save UI report" });
  fireEvent.click(save);
  fireEvent.click(save);
  await screen.findByText(/Saved part.step in uploads/);
  expect(call).toHaveBeenCalledExactlyOnceWith("wright_workspace_file_upload", {
    request: {
      workspace_id: "a",
      session_id: "chat-a",
      filename: "part.step",
      sha256: digest,
      content_base64: encoded,
    },
  });
  expect(onUploaded).toHaveBeenCalledExactlyOnceWith(path);
  expect(prepare).toHaveBeenCalledTimes(1);
});

it("stages exact binary bytes once despite a duplicate click and refreshes saved files", async () => {
  const { call, onUploaded } = show();
  const button = screen.getByRole("button", { name: "Upload file" });
  fireEvent.click(button);
  fireEvent.click(button);
  await screen.findByText(/Saved part.step in uploads/);
  expect(call).toHaveBeenCalledExactlyOnceWith("wright_workspace_file_upload", {
    request: {
      workspace_id: "a",
      session_id: "chat-a",
      filename: "part.step",
      sha256: digest,
      content_base64: encoded,
    },
  });
  expect(onUploaded).toHaveBeenCalledExactlyOnceWith(path);
});

it.each(["lost", "scope", "hash"])(
  "reconciles an unconfirmed %s reply using a read without replaying upload",
  async (failure) => {
    const call = vi
      .fn()
      .mockImplementationOnce(() =>
        failure === "lost"
          ? Promise.reject(Error("lost acknowledgement"))
          : Promise.resolve(
              reply({
                ...doc,
                ...(failure === "scope"
                  ? { workspace_id: "other" }
                  : { sha256: "a".repeat(64) }),
              }),
            ),
      )
      .mockResolvedValue(read());
    const { onUploaded } = show(call);
    fireEvent.click(screen.getByRole("button", { name: "Upload file" }));
    await screen.findByText(/Upload outcome is unconfirmed/);
    expect(screen.getByRole("button", { name: "Upload file" })).toBeDisabled();
    fireEvent.click(screen.getByRole("button", { name: "Check saved upload" }));
    await screen.findByText(/Saved part.step in uploads/);
    expect(
      call.mock.calls.filter(
        ([name]) => name === "wright_workspace_file_upload",
      ),
    ).toHaveLength(1);
    expect(call).toHaveBeenLastCalledWith("wright_workspace_file_download", {
      workspace_id: "a",
      session_id: "chat-a",
      path,
    });
    expect(onUploaded).toHaveBeenCalledExactlyOnceWith(path);
  },
);

it("keeps reconciliation pending when saved bytes or scope differ", async () => {
  const call = vi
    .fn()
    .mockRejectedValueOnce(Error("lost"))
    .mockResolvedValue(read({ content_base64: "b3RoZXI=" }));
  const { onUploaded } = show(call);
  fireEvent.click(screen.getByRole("button", { name: "Upload file" }));
  await screen.findByText(/Upload outcome is unconfirmed/);
  fireEvent.click(screen.getByRole("button", { name: "Check saved upload" }));
  await screen.findByText(/The saved upload is not confirmed/);
  expect(onUploaded).not.toHaveBeenCalled();
  expect(screen.getByRole("button", { name: "Upload file" })).toBeDisabled();
  expect(
    call.mock.calls.filter(([name]) => name === "wright_workspace_file_upload"),
  ).toHaveLength(1);
});

it("shows an authoritative rejection without claiming a saved file or retrying", async () => {
  const call = vi.fn().mockResolvedValue({
    content: [],
    structuredContent: { ok: false, error: { outcome_known: true } },
  });
  const { onUploaded } = show(call);
  fireEvent.click(screen.getByRole("button", { name: "Upload file" }));
  await screen.findByText(/Upload was rejected/);
  expect(
    screen.queryByRole("button", { name: "Check saved upload" }),
  ).toBeNull();
  expect(onUploaded).not.toHaveBeenCalled();
  expect(call).toHaveBeenCalledOnce();
});

it.each([0, 16 * 1024 * 1024 + 1])(
  "rejects size %s before sending bytes",
  async (size) => {
    const { call } = show();
    const file = new File(["x"], "input.txt");
    Object.defineProperty(file, "size", { value: size });
    fireEvent.change(screen.getByLabelText(/Choose input file/), {
      target: { files: [file] },
    });
    fireEvent.click(screen.getByRole("button", { name: "Upload file" }));
    await screen.findByText(/Choose a nonempty file up to 16 MiB/);
    expect(call).not.toHaveBeenCalled();
  },
);

it("ignores a late owner receipt after the workspace panel unmounts", async () => {
  let finish!: (value: ReturnType<typeof reply>) => void;
  const call = vi.fn().mockReturnValue(
    new Promise<ReturnType<typeof reply>>((resolve) => {
      finish = resolve;
    }),
  );
  const { onUploaded, unmount } = show(call);
  fireEvent.click(screen.getByRole("button", { name: "Upload file" }));
  await waitFor(() => expect(call).toHaveBeenCalledOnce());
  unmount();
  await act(async () => {
    finish(reply());
  });
  expect(onUploaded).not.toHaveBeenCalled();
});
