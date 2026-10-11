import {
  cleanup,
  fireEvent,
  render,
  screen,
  waitFor,
} from "@testing-library/react";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";
import {
  workspaceService,
  type WorkflowApprovalCheckpoint,
} from "../../services/workspace-service";
import { EngineeringReviewFiles } from "./EngineeringReviewFiles";

const digest = "ab".repeat(32);
const checkpoint = (): WorkflowApprovalCheckpoint => ({
  checkpoint_id: "review",
  workspace_id: "workspace",
  workflow_id: "workflow",
  run_id: "run",
  step_id: "review",
  action_kind: "local_review",
  state: "pending",
  subject: { artifact_digests: [digest] },
  subject_digest: "c".repeat(64),
  continuation: {
    artifact_files: [
      { path: "analysis/plot.svg", sha256: digest },
      { path: "diagnosis.md", sha256: digest },
      { path: "analysis/plot-guide.md", sha256: digest },
      { path: "analysis/metrics.json", sha256: digest },
      { path: "unbound.svg", sha256: "d".repeat(64) },
    ],
  },
  actor: null,
  reason: null,
  created_at: 1,
  updated_at: 1,
  expires_at: null,
  external_action: null,
});

beforeEach(() => {
  vi.spyOn(workspaceService, "getFileContentArrayBuffer").mockResolvedValue(
    new Uint8Array([1, 2]).buffer,
  );
  vi.stubGlobal("crypto", {
    subtle: {
      digest: vi.fn().mockResolvedValue(new Uint8Array(32).fill(0xab).buffer),
    },
  });
  vi.stubGlobal("URL", {
    createObjectURL: vi.fn().mockReturnValue("blob:verified"),
    revokeObjectURL: vi.fn(),
  });
});
afterEach(() => {
  cleanup();
  vi.restoreAllMocks();
  vi.unstubAllGlobals();
});

describe("engineering review evidence", () => {
  it("previews only bound images and keeps reports visible and raw records collapsed", async () => {
    const open = vi.fn();
    const { unmount } = render(
      <EngineeringReviewFiles
        checkpoint={checkpoint()}
        sessionId="session"
        onOpenFile={open}
      />,
    );
    expect(await screen.findByAltText("Preview of plot.svg")).toHaveAttribute(
      "src",
      "blob:verified",
    );
    expect(
      workspaceService.getFileContentArrayBuffer,
    ).toHaveBeenCalledExactlyOnceWith("session", "analysis/plot.svg");
    expect(
      screen.getByRole("button", { name: "Open diagnosis.md" }),
    ).toBeVisible();
    expect(
      screen.getByRole("button", { name: "Open plot-guide.md" }),
    ).toBeVisible();
    expect(
      screen.getByText(/Supporting data/).closest("details"),
    ).not.toHaveAttribute("open");
    expect(screen.queryByText("unbound.svg")).toBeNull();
    fireEvent.click(screen.getByRole("button", { name: "Open plot.svg" }));
    expect(open).toHaveBeenCalledWith("analysis/plot.svg");
    unmount();
    expect(URL.revokeObjectURL).toHaveBeenCalledWith("blob:verified");
  });
  it("does not display changed evidence under a pending review", async () => {
    vi.mocked(crypto.subtle.digest).mockResolvedValue(
      new Uint8Array(32).fill(0x01).buffer,
    );
    render(
      <EngineeringReviewFiles checkpoint={checkpoint()} sessionId="session" />,
    );
    expect(await screen.findByRole("alert")).toHaveTextContent(
      "changed since the review was prepared",
    );
    expect(screen.queryByRole("img")).toBeNull();
    expect(URL.createObjectURL).not.toHaveBeenCalled();
  });
  it("shows unavailable previews without pretending the image was reviewed", async () => {
    vi.mocked(workspaceService.getFileContentArrayBuffer).mockRejectedValue(
      new Error("File unavailable"),
    );
    render(
      <EngineeringReviewFiles checkpoint={checkpoint()} sessionId="session" />,
    );
    expect(await screen.findByRole("alert")).toHaveTextContent(
      "Preview unavailable. Open the file to inspect it.",
    );
    expect(screen.queryByRole("img")).toBeNull();
  });
  it("ignores a delayed image response after closing the review", async () => {
    let resolve!: (value: ArrayBuffer) => void;
    vi.mocked(workspaceService.getFileContentArrayBuffer).mockReturnValue(
      new Promise((r) => {
        resolve = r;
      }),
    );
    const { unmount } = render(
      <EngineeringReviewFiles checkpoint={checkpoint()} sessionId="session" />,
    );
    unmount();
    resolve(new Uint8Array([1]).buffer);
    await waitFor(() => expect(URL.createObjectURL).not.toHaveBeenCalled());
  });
  it("does not request images when no evidence was recorded", () => {
    render(
      <EngineeringReviewFiles
        checkpoint={{ ...checkpoint(), continuation: {} }}
        sessionId="session"
      />,
    );
    expect(screen.getByRole("status")).toHaveTextContent(
      "No file links are recorded",
    );
    expect(workspaceService.getFileContentArrayBuffer).not.toHaveBeenCalled();
  });
});
