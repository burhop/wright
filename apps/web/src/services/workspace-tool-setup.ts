/** Navigation/help only. No capability, readiness or execution authority. */
export interface WorkspaceToolSetupRequest {
  workspaceId: string;
  sessionId: string;
  sourcePath: string;
  sourceDigest: string;
  title: string;
  purpose: string;
  requirements: string[];
  guideText: string;
}

/** Resolves when the user returns to the requesting setup; rejects if unavailable. */
export type OpenWorkspaceToolSetup = (
  request: WorkspaceToolSetupRequest,
) => Promise<void>;
