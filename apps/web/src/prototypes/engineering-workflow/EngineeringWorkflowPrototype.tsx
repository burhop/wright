import { useMemo } from "react";
import { useLocation } from "react-router-dom";

import { EngineeringWorkflowVisualSlice } from "./EngineeringWorkflowVisualSlice";
import { ReactFlowWorkflowCanvas } from "./canvas/react-flow/ReactFlowWorkflowCanvas";
import {
  diagnosticScenario,
  diagnosticWorkflow,
} from "./fixtures/diagnostic-workflow";
import { workflowForPrototypeSearch } from "./fixtures/scale-workflows";
import { prototypeViewStateForSearch } from "./prototype-review-state";
import { wrightDiagnosticMcpCatalogAdapter } from "./services/diagnostic-mcp-catalog-adapter";
import { wrightDiagnosticLlmAdapter } from "./services/diagnostic-llm-adapter";
import { brepDiagnosticMcpRuntimeAdapter } from "./services/brep-diagnostic-mcp-runtime-adapter";

export function EngineeringWorkflowPrototype() {
  const { search } = useLocation();
  const diagnosticMode = useMemo(
    () => new URLSearchParams(search).get("scenario") === "diagnostic",
    [search],
  );
  const workflow = useMemo(
    () =>
      diagnosticMode ? diagnosticWorkflow : workflowForPrototypeSearch(search),
    [diagnosticMode, search],
  );
  const viewState = useMemo(
    () => prototypeViewStateForSearch(search),
    [search],
  );

  return (
    <EngineeringWorkflowVisualSlice
      badge={
        diagnosticMode ? "CP3I · Output delivery" : "CP3C · Knowledge lookup"
      }
      diagnosticScenario={diagnosticMode ? diagnosticScenario : undefined}
      diagnosticLlmAdapter={
        diagnosticMode ? wrightDiagnosticLlmAdapter : undefined
      }
      diagnosticMcpCatalogAdapter={
        diagnosticMode ? wrightDiagnosticMcpCatalogAdapter : undefined
      }
      diagnosticMcpRuntimeAdapter={
        diagnosticMode ? brepDiagnosticMcpRuntimeAdapter : undefined
      }
      workflow={workflow}
      viewState={viewState}
      renderCanvas={(props) => <ReactFlowWorkflowCanvas {...props} />}
    />
  );
}

export default EngineeringWorkflowPrototype;
