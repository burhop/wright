export function workspaceContentUrl(path: string, sessionId: string): string {
  const query = new URLSearchParams({
    path,
    session_id: sessionId,
  });
  return `/api/workspace/files/content?${query.toString()}`;
}
