import { useMemo } from "react";

import { EngineeringWorkflowVisualSlice } from "./EngineeringWorkflowVisualSlice";
import { ReactFlowWorkflowCanvas } from "./canvas/react-flow/ReactFlowWorkflowCanvas";
import { workflowForPrototypeSearch } from "./fixtures/scale-workflows";
import { prototypeViewStateForSearch } from "./prototype-review-state";

export function EngineeringWorkflowPrototype() {
  const workflow = useMemo(
    () => workflowForPrototypeSearch(window.location.search),
    [],
  );
  const viewState = useMemo(
    () => prototypeViewStateForSearch(window.location.search),
    [],
  );

  return (
    <EngineeringWorkflowVisualSlice
      badge="CP3B · Design input"
      workflow={workflow}
      viewState={viewState}
      renderCanvas={(props) => <ReactFlowWorkflowCanvas {...props} />}
    />
  );
}

export default EngineeringWorkflowPrototype;
