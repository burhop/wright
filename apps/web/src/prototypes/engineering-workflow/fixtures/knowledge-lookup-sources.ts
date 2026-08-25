export interface KnowledgeLookupSourceOption {
  sourceId: string;
  label: string;
  description: string;
}

/**
 * Generic source scopes describe where governed retrieval may look. They do
 * not select a RAG implementation, search vendor, engineering domain, or MCP
 * tool.
 */
export const knowledgeLookupSources: readonly KnowledgeLookupSourceOption[] = [
  {
    sourceId: "workspace",
    label: "Workspace documents",
    description:
      "Project files, standards, templates, and approved references.",
  },
  {
    sourceId: "connections",
    label: "Connected knowledge",
    description: "Approved document systems, catalogs, and knowledge bases.",
  },
  {
    sourceId: "approved-web",
    label: "Approved web sources",
    description: "External reference sites allowed by workspace policy.",
  },
] as const;

export const knowledgeLookupSourceIds = knowledgeLookupSources.map(
  ({ sourceId }) => sourceId,
);
