import { fireEvent, render, screen, waitFor } from "@testing-library/react";
import { beforeEach, describe, expect, it, vi } from "vitest";
import { WorkspaceGitPanel } from "./WorkspaceGitPanel";
import { workspaceService } from "../../services/workspace-service";

vi.mock("../../services/workspace-service", () => ({
  workspaceService: {
    getGitStatus: vi.fn(),
    getGitHistory: vi.fn(),
    getWorkspaceConfig: vi.fn(),
    initializeGit: vi.fn(),
    commitChanges: vi.fn(),
    checkoutBranch: vi.fn(),
    getGitDiff: vi.fn(),
    pullCommits: vi.fn(),
    pushCommits: vi.fn(),
  },
}));

describe("Workspace Git controls", () => {
  beforeEach(() => {
    vi.resetAllMocks();
    vi.mocked(workspaceService.getGitStatus).mockResolvedValue({
      branch_name: "main",
      is_clean: false,
      changes: [
        { path: "/part.txt", git_status: "M", staged: false, file_size: 2 },
      ],
      is_repository: true,
    });
    vi.mocked(workspaceService.getGitHistory).mockResolvedValue({
      commits: [],
    });
    vi.mocked(workspaceService.getWorkspaceConfig).mockResolvedValue({
      workspace_id: "ws",
      git_remote_url: null,
      git_username: null,
      has_token: false,
      workspace_path: "/workspace",
      workspace_prompt: null,
      git_large_file_threshold: null,
    });
  });
  const open = () =>
    render(
      <WorkspaceGitPanel
        sessionId="workspace-session"
        refreshVersion={0}
        onDiff={vi.fn()}
      />,
    );
  it("shows real changes and commits only after an explicit action", async () => {
    open();
    await screen.findByText("M /part.txt");
    expect(workspaceService.commitChanges).not.toHaveBeenCalled();
    const commit = screen.getByRole("button", {
      name: "Commit all workspace changes",
    });
    expect(commit).toBeDisabled();
    fireEvent.change(screen.getByLabelText("Commit message"), {
      target: { value: "Save part" },
    });
    fireEvent.click(commit);
    await waitFor(() =>
      expect(workspaceService.commitChanges).toHaveBeenCalledWith(
        "workspace-session",
        "Save part",
      ),
    );
    expect(workspaceService.pushCommits).not.toHaveBeenCalled();
  });
  it("switches branches through the shared workspace service", async () => {
    open();
    await screen.findByText("M /part.txt");
    fireEvent.change(screen.getByLabelText("Branch name"), {
      target: { value: "feature/part" },
    });
    fireEvent.click(screen.getByRole("button", { name: "Switch branch" }));
    await waitFor(() =>
      expect(workspaceService.checkoutBranch).toHaveBeenCalledWith(
        "workspace-session",
        "feature/part",
      ),
    );
  });
  it("does not represent a failed status request as a clean repository", async () => {
    vi.mocked(workspaceService.getGitStatus).mockRejectedValue(
      new Error("Git unavailable"),
    );
    open();
    expect(await screen.findByRole("alert")).toHaveTextContent(
      "Git unavailable",
    );
    expect(screen.queryByText("No changes to commit.")).not.toBeInTheDocument();
  });
  it("offers repository creation only when the backend reports no repository", async () => {
    vi.mocked(workspaceService.getGitStatus).mockResolvedValue({
      branch_name: "",
      is_clean: false,
      changes: [],
      is_repository: false,
    });
    open();
    expect(
      await screen.findByRole("button", { name: "Create repository" }),
    ).toBeEnabled();
    expect(workspaceService.initializeGit).not.toHaveBeenCalled();
    expect(workspaceService.getGitHistory).not.toHaveBeenCalled();
  });
  it("warns on files exceeding the configured byte threshold without submitting Git actions", async () => {
    vi.mocked(workspaceService.getWorkspaceConfig).mockResolvedValue({
      workspace_id: "ws",
      git_remote_url: null,
      git_username: null,
      has_token: false,
      workspace_path: "/workspace",
      workspace_prompt: null,
      git_large_file_threshold: 1024 * 1024,
    });
    vi.mocked(workspaceService.getGitStatus).mockResolvedValue({
      branch_name: "main",
      is_clean: false,
      is_repository: true,
      changes: [
        {
          path: "/model.step",
          git_status: "U",
          staged: false,
          file_size: 2 * 1024 * 1024,
        },
      ],
    });
    open();
    expect(
      await screen.findByText(
        "1 changed file exceeds the 1 MiB warning threshold in Workspace Settings.",
      ),
    ).toBeInTheDocument();
    expect(
      screen.getByRole("button", { name: /U \/model.step.*Large file.*2 MiB/ }),
    ).toBeEnabled();
    fireEvent.change(screen.getByLabelText("Commit message"), {
      target: { value: "Review model" },
    });
    expect(
      screen.getByRole("button", { name: "Commit all workspace changes" }),
    ).toBeEnabled();
    expect(workspaceService.commitChanges).not.toHaveBeenCalled();
    expect(workspaceService.pushCommits).not.toHaveBeenCalled();
  });
  it("uses the same 10 MiB default as Workspace Settings", async () => {
    vi.mocked(workspaceService.getGitStatus).mockResolvedValue({
      branch_name: "main",
      is_clean: false,
      is_repository: true,
      changes: [
        {
          path: "/large.step",
          git_status: "M",
          staged: false,
          file_size: 11 * 1024 * 1024,
        },
      ],
    });
    open();
    expect(
      await screen.findByText(
        "1 changed file exceeds the 10 MiB warning threshold in Workspace Settings.",
      ),
    ).toBeInTheDocument();
  });
  it("does not warn for equal, smaller, unknown or deleted sizes", async () => {
    vi.mocked(workspaceService.getGitStatus).mockResolvedValue({
      branch_name: "main",
      is_clean: false,
      is_repository: true,
      changes: [
        {
          path: "/equal.step",
          git_status: "M",
          staged: false,
          file_size: 10 * 1024 * 1024,
        },
        { path: "/small.txt", git_status: "U", staged: false, file_size: 1 },
        { path: "/unknown.step", git_status: "M", staged: false },
        {
          path: "/removed.step",
          git_status: "D",
          staged: false,
          file_size: null,
        },
      ],
    });
    open();
    await screen.findByText("D /removed.step");
    expect(
      screen.queryByText(/warning threshold in Workspace Settings/),
    ).not.toBeInTheDocument();
    expect(screen.queryByText(/Large file/)).not.toBeInTheDocument();
  });
  it("preserves a one-byte threshold instead of rounding it to zero MiB", async () => {
    vi.mocked(workspaceService.getWorkspaceConfig).mockResolvedValue({
      workspace_id: "ws",
      git_remote_url: null,
      git_username: null,
      has_token: false,
      workspace_path: "/workspace",
      workspace_prompt: null,
      git_large_file_threshold: 1,
    });
    open();
    expect(
      await screen.findByText(
        "1 changed file exceeds the 1 B warning threshold in Workspace Settings.",
      ),
    ).toBeInTheDocument();
    expect(screen.getByText("Large file · 2 B")).toBeInTheDocument();
  });
  it("refreshes warnings when the threshold changes", async () => {
    vi.mocked(workspaceService.getGitStatus).mockResolvedValue({
      branch_name: "main",
      is_clean: false,
      is_repository: true,
      changes: [
        {
          path: "/large.step",
          git_status: "M",
          staged: false,
          file_size: 11 * 1024 * 1024,
        },
      ],
    });
    open();
    await screen.findByText(/exceeds the 10 MiB warning threshold/);
    vi.mocked(workspaceService.getWorkspaceConfig).mockResolvedValue({
      workspace_id: "ws",
      git_remote_url: null,
      git_username: null,
      has_token: false,
      workspace_path: "/workspace",
      workspace_prompt: null,
      git_large_file_threshold: 12 * 1024 * 1024,
    });
    fireEvent.click(screen.getByRole("button", { name: "Refresh Git" }));
    await waitFor(() =>
      expect(
        screen.queryByText(/warning threshold in Workspace Settings/),
      ).not.toBeInTheDocument(),
    );
    expect(screen.queryByText(/Large file/)).not.toBeInTheDocument();
  });
  it("clears the preceding workspace's warnings when switching sessions", async () => {
    vi.mocked(workspaceService.getWorkspaceConfig).mockResolvedValue({
      workspace_id: "ws",
      git_remote_url: null,
      git_username: null,
      has_token: false,
      workspace_path: "/workspace",
      workspace_prompt: null,
      git_large_file_threshold: 1,
    });
    const view = open();
    await screen.findByText(/exceeds the 1 B warning threshold/);
    vi.mocked(workspaceService.getWorkspaceConfig).mockResolvedValue({
      workspace_id: "other",
      git_remote_url: null,
      git_username: null,
      has_token: false,
      workspace_path: "/other",
      workspace_prompt: null,
      git_large_file_threshold: null,
    });
    view.rerender(
      <WorkspaceGitPanel
        sessionId="other-session"
        refreshVersion={0}
        onDiff={vi.fn()}
      />,
    );
    await screen.findByText("M /part.txt");
    expect(
      screen.queryByText(/warning threshold in Workspace Settings/),
    ).not.toBeInTheDocument();
  });
});
