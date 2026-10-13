import { useState } from "react";
import WorkflowRecoveryConcept from "../workflow-recovery/WorkflowRecoveryConcept";
import type { WorkspaceWorkflowSourceDocument } from "../../services/workspace-service";
import { NativeSourceClient } from "./native-source-client";
import "../../styles/presentation-controls.css";
import "./native-panel.css";

/** Shared editor inside one real host work surface, without another chat or executor. */
export function NativeWorkflowPanel({ initial, client, workspaceName, onDirty }: {
  readonly initial: WorkspaceWorkflowSourceDocument;
  readonly client: NativeSourceClient;
  readonly workspaceName: string;
  readonly onDirty?: (dirty: boolean) => void;
}) {
  const [document, setDocument] = useState(initial);
  const [unsaved, setUnsaved] = useState(false);
  const [reopen, setReopen] = useState(0);
  return (
    <main className="native-workflow-panel" data-control-style="neutral" data-presentation="native-panel">
      <header className="native-workflow-panel__context">
        <b>{workspaceName}</b>
        <span>{unsaved ? "Unsaved changes — save before closing." : "Workflow"}</span>
        <small>Use this desktop conversation for reasoning. Run controls are not connected in this editor prototype.</small>
      </header>
      <div className="native-workflow-panel__editor">
        <WorkflowRecoveryConcept
          workflowSource={document.source}
          workflowLayout={document.layout ?? undefined}
          workflowFilePath={document.path}
          definitionRevision={document.definition_revision}
          storageDigest={document.storage_digest}
          reopenRequest={reopen}
          simulationPreview={false}
          onUnsavedChange={dirty => { setUnsaved(dirty); onDirty?.(dirty); }}
          onSave={(source, layout) => client.save(source, layout)}
          onReadStoredSource={() => client.read()}
          onReloadStoredSource={async (canReplace) => {
            const observed = await client.read();
            if (canReplace && !canReplace(observed)) return;
            client.accept(observed);
            setDocument(observed);
            setReopen(value => value + 1);
          }}
        />
      </div>
    </main>
  );
}
