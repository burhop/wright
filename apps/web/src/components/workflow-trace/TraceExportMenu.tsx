interface TraceExportMenuProps {
  onExportEvidence?: () => void;
  onExportTrace?: (mode: "report_only" | "full_data") => void;
}

export function TraceExportMenu({
  onExportEvidence,
  onExportTrace,
}: TraceExportMenuProps) {
  if (!onExportEvidence && !onExportTrace) return null;
  return (
    <details className="workflow-trace__export">
      <summary>Export review</summary>
      <div className="workflow-trace__actions">
        {onExportTrace && (
          <>
            <button type="button" onClick={() => onExportTrace("report_only")}>
              Report ZIP
            </button>
            <button type="button" onClick={() => onExportTrace("full_data")}>
              Report and data ZIP
            </button>
          </>
        )}
        {onExportEvidence && (
          <button type="button" onClick={onExportEvidence}>
            Technical evidence JSON
          </button>
        )}
      </div>
    </details>
  );
}
