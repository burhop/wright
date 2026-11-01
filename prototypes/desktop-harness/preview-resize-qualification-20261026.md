# File preview resize correction

The Windows tester observed uploaded preview text below the viewport after
narrowing the panel. The previous browser journey checked control presence and
horizontal overflow, so it passed despite the invisible text.

The strengthened existing file journey reproduces a viewport ratio of zero on
Linux using the real MCP/backend/file owners and a disposable workspace. The
initial preview and exact PNG transfer still pass; only the resize visibility
assertion fails. The failed report and screenshot remain retained.

The preview now keeps itself visible on resize while focus remains inside it.
After the user focuses file search, resize respects that navigation instead of
scrolling back to the preview. No file read, download, upload or authorization
contract changes; the original text/identity validation remains in place.

The same file journey passes after the correction: the complete uploaded text
enters the viewport, focus is retained, returning to search remains visible,
and downloaded PNG bytes retain their exact SHA-256. Nineteen focused preview/Home
tests, TypeScript, scoped ESLint and resource packaging pass.

Evidence: `.local-run/native-document-tabs-20261026/preview-resize/`.
`before/report.json` retains the failure; `after/report.json` and
`after/files-narrow.png` record the corrected Linux simulated-host journey.
The fixtures are synthetic UI text and an explicitly copied retained reference
image, not new engineering outputs. No engineering process or accepted source
was changed. Actual Windows requalification is pending; native Windows host
rendering and download/open remain separate, unverified boundaries.

This correction is local only. Installed prototype 0.24 remains frozen for the
user-approved native document-tab test. The wider file-list and navigation
usability concerns remain open and follow the user's native-tab direction.
