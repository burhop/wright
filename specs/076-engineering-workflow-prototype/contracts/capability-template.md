# Contract: Engineering Capability Template

## Purpose

Capability templates make a large engineering catalog understandable without turning CAD, FEA, CAM, CFD, PLM, kinematics, or any other discipline into a Wright runtime service family.

## Shape

```ts
type EngineeringCapabilityTemplate = {
  capabilityId: string;
  categoryId: string;
  title: string;
  description: string;
  keywords: string[];
  expectedInputs: Array<{ label: string; schemaHint?: JsonSchema }>;
  expectedOutputs: Array<{ label: string; schemaHint?: JsonSchema }>;
  compatibilityQuery?: CatalogCompatibilityQuery;
};
```

Categories, keywords, titles, and input/output descriptions are presentation and discovery metadata. Organizations may add or rename them without adding application code.

## Discovery behavior

- The compact palette shows pinned, recent, and context-relevant templates.
- The full library supports search and filterable categories.
- Search covers title, description, keywords, expected inputs, and expected outputs.
- Candidate catalog matches are derived from the generic workspace catalog and are labeled as live or fixture data.
- Choosing a template creates an unbound generic `mcp-action` block.
- A template may narrow compatible catalog results, but it cannot choose a server or tool automatically.

## Binding boundary

An unbound capability is not executable. Before execution, the user must select and review one exact workspace-visible catalog tool, its current input schema/revision, mappings, and approval policy through the generic MCP binding contract.

The following are prohibited:

- dispatch branches based on `categoryId`, `capabilityId`, title, vendor, or file format;
- CAD-, FEA-, CAM-, CFD-, PLM-, or similar service/executor subclasses;
- persisting a catalog match count as binding authority;
- treating a friendly template name as an MCP tool identity;
- silently rebinding when an exact tool or schema changes.

## Reference conformance

The visual slice demonstrates at least CAD, structural FEA, CAM, CFD, PLM/PDM, kinematics, thermal analysis, sheet-metal preparation, metrology, and quality workflows. Focused tests must prove that search can find these templates and that the UI describes them as generic MCP action templates rather than runtime implementations.
