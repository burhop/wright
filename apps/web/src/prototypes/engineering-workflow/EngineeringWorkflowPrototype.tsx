import { useMemo } from "react";

import { EngineeringWorkflowVisualSlice } from "./EngineeringWorkflowVisualSlice";
import { ReactFlowWorkflowCanvas } from "./canvas/react-flow/ReactFlowWorkflowCanvas";
import { workflowForPrototypeSearch } from "./fixtures/scale-workflows";

export function EngineeringWorkflowPrototype() {
  const workflow = useMemo(
    () => workflowForPrototypeSearch(window.location.search),
    [],
  );

  return (
    <EngineeringWorkflowVisualSlice
      badge="CP2 · React Flow"
      workflow={workflow}
      renderCanvas={(props) => <ReactFlowWorkflowCanvas {...props} />}
    />
  );
}

export default EngineeringWorkflowPrototype;
