import { useState } from 'react';
import type { ArtifactRef, InteractionSnapshot, NavigationTarget, ProcessClient } from '@wright/process-client';
import { ProcessUI, Section, ProgressPanel, ResultCard, ReasonNotice } from '@wright/ui-kit';

export interface AppProps {
  client: ProcessClient;
  snapshot: InteractionSnapshot;
  readOnly: boolean;
}

// An inert composition reference. The host owns attachment and current state.
// UI generation must tailor this to the supplied engineering job and bindings.
export default function App({ client, snapshot, readOnly }: AppProps) {
  const [navigationFailed, setNavigationFailed] = useState(false);
  const navigate = (target: NavigationTarget) => {
    setNavigationFailed(false);
    void client.navigate(target).catch(() => setNavigationFailed(true));
  };
  const openEvidence = (reference: ArtifactRef) => navigate({
    kind: 'evidence', artifact_ref: reference.artifact_ref, result_id: reference.result_id,
  });
  return <ProcessUI>
    <Section title="Process status">
      {readOnly && <p>Preview — review the interface before using the process.</p>}
      <ProgressPanel state={snapshot.state} observations={snapshot.observations ?? []} />
      {(snapshot.diagnostics ?? []).map((reason, index) =>
        <ReasonNotice key={`${reason.code}-${index}`} reason={reason} />)}
      {navigationFailed && <p role="alert">Wright could not open this evidence. Refresh the common working view and inspect the exact result.</p>}
    </Section>
    <Section title="Results and checks">
      {(snapshot.outputs ?? []).length === 0 && <p>Results will appear as the process produces them.</p>}
      {(snapshot.outputs ?? []).map(output => <ResultCard key={output.result_id} output={output} onNavigate={navigate} onOpen={openEvidence} />)}
    </Section>
  </ProcessUI>;
}
