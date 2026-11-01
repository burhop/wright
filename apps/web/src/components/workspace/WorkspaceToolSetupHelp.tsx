import type { WorkspaceToolSetupRequest } from "../../services/workspace-tool-setup";
import { ProviderSetupGuide } from "./ProviderSetupGuide";

/** Reuses the workspace's MCP selector and registry; never installs or enables. */
export function WorkspaceToolSetupHelp({
  request,
  onReturn,
}: {
  request: WorkspaceToolSetupRequest;
  onReturn: () => void;
}) {
  return (
    <section className="workspace-tool-setup-help" aria-label={request.title}>
      <h3>{request.title}</h3>
      <p>{request.purpose}</p>
      <p>
        Use the selector below for installed servers. To inspect installation
        and connection options, open the existing Tool Registry in a separate
        tab. Your job setup stays here. Nothing is installed or enabled by
        opening it.
      </p>
      <a href="/tool-registry" target="_blank" rel="noopener noreferrer">
        Open Tool Registry (new tab)
      </a>
      <ProviderSetupGuide text={request.guideText} />
      <details>
        <summary>Exact job requirements</summary>
        <ul>
          {request.requirements.map((text, index) => (
            <li key={index}>{text}</li>
          ))}
        </ul>
        <p>
          Return to <code>{request.sourcePath}</code>. Availability is checked
          again on return; configuring a server does not prove readiness.
        </p>
      </details>
      <button
        type="button"
        className="recovery-button recovery-button--primary"
        onClick={onReturn}
      >
        Return to job setup
      </button>
    </section>
  );
}
