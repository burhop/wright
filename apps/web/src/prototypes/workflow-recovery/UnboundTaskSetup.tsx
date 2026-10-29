import { useEffect, useState } from "react";
import type { RecoveryBlock } from "./model";
import type { RecoveryCommand } from "./command-system";
import {
  useWorkflowToolDiscovery,
  useWorkflowToolManagement,
  useWorkflowToolSession,
} from "./workflow-tool-discovery";
import {
  configureUnboundMcpTask,
  mcpServerChoices,
  type McpServerChoice,
} from "./mcp-server-blocks";

export function UnboundTaskSetup({
  block,
  sessionId: hostSessionId,
  readOnly,
  onApply,
}: {
  block: RecoveryBlock;
  sessionId?: string;
  readOnly: boolean;
  onApply: (commands: RecoveryCommand[]) => boolean;
}) {
  const sessionId = useWorkflowToolSession(hostSessionId);
  const read = useWorkflowToolDiscovery();
  const openConnections = useWorkflowToolManagement();
  const [refresh, setRefresh] = useState(0);
  const [servers, setServers] = useState<McpServerChoice[]>([]);
  const [selected, setSelected] = useState("");
  const [message, setMessage] = useState("Loading workspace servers…");
  useEffect(() => {
    let active = true;
    setServers([]);
    setSelected("");
    if (!sessionId) {
      setMessage("Open this workflow in its workspace to choose a server.");
      return;
    }
    setMessage("Loading workspace servers…");
    void read(sessionId)
      .then((tools) => {
        if (active) {
          const choices = mcpServerChoices(tools);
          setServers(choices);
          setMessage(
            choices.length
              ? ""
              : "No workspace servers are available. Check Connections.",
          );
        }
      })
      .catch(() => {
        if (active)
          setMessage(
            "Workspace servers could not be read. Check Connections, then refresh servers.",
          );
      });
    return () => {
      active = false;
    };
  }, [sessionId, read, refresh]);
  return (
    <section
      aria-label="Configure this step"
      className="recovery-authoring-settings"
    >
      <h3>Choose how this step works</h3>
      <p>
        Let AI use one server to follow this step’s instructions. Inputs,
        outputs and connections stay in place. Save and check the workflow
        before running.
      </p>
      {message && <p role="status">{message}</p>}
      <div>
        {openConnections ? (
          <button type="button" onClick={openConnections}>
            Open Connections
          </button>
        ) : (
          <a href="/tool-registry" target="_blank" rel="noreferrer">
            Open Tool Registry
          </a>
        )}
        <button type="button" onClick={() => setRefresh((value) => value + 1)}>
          Refresh servers
        </button>
      </div>
      <label>
        Engineering server
        <select
          value={selected}
          disabled={readOnly || !servers.length}
          onChange={(e) => setSelected(e.target.value)}
        >
          <option value="">Choose a server</option>
          {servers.map((server) => (
            <option key={server.id} value={server.id}>
              {server.name}
            </option>
          ))}
        </select>
      </label>
      <button
        type="button"
        disabled={readOnly || !selected}
        onClick={() => {
          const server = servers.find((item) => item.id === selected);
          if (server) onApply(configureUnboundMcpTask(block, server));
        }}
      >
        Use AI with this server
      </button>
    </section>
  );
}
