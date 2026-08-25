export type EngineeringWorkflowPrototypeViewState =
  | "ready"
  | "loading"
  | "empty"
  | "error";

export const prototypeViewStateCopy = {
  loading: {
    title: "Preparing workflow preview",
    description:
      "Loading the canonical workflow and its reviewable engineering artifacts.",
  },
  empty: {
    title: "No workflow blocks yet",
    description:
      "Start from an engineering template or describe the work to be planned.",
  },
  error: {
    title: "Workflow preview unavailable",
    description:
      "The saved workflow was not changed. Review the source or try loading it again.",
  },
} as const;

export function prototypeViewStateForSearch(
  search: string,
): EngineeringWorkflowPrototypeViewState {
  const view = new URLSearchParams(search).get("view");
  return view === "loading" || view === "empty" || view === "error"
    ? view
    : "ready";
}
