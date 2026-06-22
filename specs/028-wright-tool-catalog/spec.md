# Feature Specification: Engineering Tool Catalog

**Feature Branch**: `028-wright-tool-catalog`

**Created**: 2026-06-22

**Status**: Draft

**Input**: User description: "Create the catalog system for hermes-plugin-wright that provides a browseable registry of ~30 engineering MCP servers. The catalog is a YAML file (hermes-plugin-wright/catalog.yaml) with entries for engineering tools across domains: CAD (FreeCAD, Fusion 360, OpenSCAD, Zoo.dev), cloud-CAD (OnShape/Jarvis, APS), FEA (CalculiX), CFD (OpenFOAM), CAM (PrusaSlicer), PLM, BIM, EDA, mesh/surface (Blender, Rhino, SketchUp), and drafting (AutoCAD). Each entry has: id, name, vendor, description, domains (list of tags like "cad", "fea"), tags, transport (stdio|sse|webmcp), command (list of strings), source_url, image_url, locality (local|remote), weight (light|medium|heavy), env_vars (list of {name, label, description, required, secret}), and dependencies ({system, python, node} lists). Create a Pydantic schema in schemas.py (CatalogEntry, EnvVarDefinition, DependencySpec) that matches the existing tool_registry.models.EnvVarDefinition exactly so entries are directly insertable into the Wright DB. Create catalog.py with a CatalogLoader class that loads/parses the YAML, filters by domain, and supports free-text search across name/description/tags. Include a domain taxonomy: cad, code-cad, cloud-cad, fea, cfd, cam, plm, bim, eda, thermal, tolerance, drafting, mesh, iot. Write unit tests for the loader and schema validation. Reference: docs/wright-hermes-plugin-plan.md sections 6 (Catalog System) and 6.4 (Domain Taxonomy). Be sure to integrate with existing code as we already started building UI for this."

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Browse Engineering Tools by Domain (Priority: P1)

An engineer using the Hermes Agent wants to see what CAD tools are available for installation. They request a list of tools under the "cad" domain. The system parses the catalog data, filters it using the standard domain taxonomy, and returns a structured list of available CAD servers (e.g. FreeCAD Engineering, Jarvis OnShape MCP, Zoo.dev Cloud CAD) including vendor, description, weight, and credential requirements.

**Why this priority**: Discoverability of domain-specific tools is the main user-facing capability of the catalog.

**Independent Test**: Can be tested by invoking the catalog filtering API/method for "cad" and verifying it returns only entries tagged with the "cad" domain.

**Acceptance Scenarios**:

1. **Given** the catalog database has entries spanning multiple domains, **When** the user filters for the "cad" domain, **Then** only CAD-related tools are returned.
2. **Given** the taxonomy list, **When** a user filters by an empty or non-existent taxonomy term, **Then** an empty list is returned without failing.

---

### User Story 2 - Keyword Search Across Catalog (Priority: P1)

A user wants to find tools related to finite element analysis, but they don't know the domain tag. They enter a search query like "CalculiX" or "simulation". The system performs a case-insensitive search across the name, description, and tags of all catalog entries, returning matching servers like the FreeCAD Engineering server.

**Why this priority**: A search bar is critical for catalog navigation when users don't know the exact domain tags.

**Independent Test**: Can be tested by executing search queries for specific keywords (e.g., "CalculiX", "open-source") and verifying the correct tools are returned.

**Acceptance Scenarios**:

1. **Given** the catalog, **When** searching for a partial name or tag (case-insensitive), **Then** all matching entries are returned.
2. **Given** the catalog, **When** searching for a term that does not exist in any fields, **Then** an empty list is returned.

---

### User Story 3 - Database Insertion Validation (Priority: P1)

An installer component reads a catalog entry to register it with the main Wright Tool Registry database. The system validates the entry using a Pydantic schema. Because the schema's environment variable fields match the core database models exactly, the system can insert the tool definition directly into the SQLite database without field transformations.

**Why this priority**: The catalog registry metadata must align perfectly with the core database models to prevent runtime schema errors during tool installation.

**Independent Test**: Can be tested by instantiating Pydantic schemas with catalog YAML data and asserting that they serialize/validate correctly and align with the existing database interface definitions.

**Acceptance Scenarios**:

1. **Given** a raw catalog dictionary, **When** validated against the `CatalogEntry` schema, **Then** environment variables validate against the exact structure defined in `tool_registry.models.EnvVarDefinition`.
2. **Given** a catalog entry with missing required fields (e.g. invalid transport type or missing required env_vars info), **When** validating, **Then** a clear Pydantic validation error is raised.

---

### Edge Cases

- **Malformed YAML File**: What happens if the catalog YAML has syntax errors? -> The loader raises a parse error with file coordinates and falls back to a safe empty registry state.
- **Duplicate IDs**: What happens if two catalog entries have the same `id`? -> The loader rejects the catalog as invalid and reports a duplication error.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: The system MUST store catalog entries in a YAML file at `hermes-plugin-wright/catalog.yaml`.
- **FR-002**: The catalog MUST contain entries for ~30 engineering tools spanning: CAD, cloud-CAD, FEA, CFD, CAM, PLM, BIM, EDA, mesh/surface, and drafting.
- **FR-003**: Each catalog entry MUST declare the fields: `id`, `name`, `vendor`, `description`, `domains`, `tags`, `transport`, `command`, `source_url`, `image_url`, `locality`, `weight`, `env_vars`, and `dependencies`.
- **FR-004**: The transport field MUST only accept values: `stdio`, `sse`, or `webmcp`.
- **FR-005**: The locality field MUST only accept values: `local` or `remote`.
- **FR-006**: The weight field MUST only accept values: `light`, `medium`, or `heavy`.
- **FR-007**: The system MUST define Pydantic schemas in `hermes-plugin-wright/schemas.py`: `CatalogEntry`, `EnvVarDefinition`, and `DependencySpec`.
- **FR-008**: The `EnvVarDefinition` schema MUST match `tool_registry.models.EnvVarDefinition` fields (`name`, `label`, `description`, `required`, `secret`) exactly.
- **FR-009**: The system MUST define `CatalogLoader` in `hermes-plugin-wright/catalog.py` with methods to load, filter by domain, and perform case-insensitive keyword search.
- **FR-010**: The domain filtering MUST align with the specified domain taxonomy: `cad`, `code-cad`, `cloud-cad`, `fea`, `cfd`, `cam`, `plm`, `bim`, `eda`, `thermal`, `tolerance`, `drafting`, `mesh`, `iot`.
- **FR-011**: The package MUST include unit tests verifying the loader behavior, search logic, and schema validation.

### Key Entities

- **Catalog Entry**: The data representation of a single installable MCP server (defined in `catalog.yaml` and validated by `CatalogEntry`).
- **EnvVar Definition**: The Pydantic model (`EnvVarDefinition`) representing a credential or environment variable option required by the tool.
- **Dependency Spec**: The system, python, and node dependencies required by the tool (`DependencySpec`).
- **Catalog Loader**: The python class (`CatalogLoader`) responsible for reading, caching, parsing, and searching catalog entries.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: Loading and validating the entire catalog file of 30+ entries completes in under 20 milliseconds.
- **SC-002**: Free-text keyword search matches entries across name, description, and tags case-insensitively, with zero false positives.
- **SC-003**: 100% test coverage for the schemas and loader logic (asserted via local unit tests).

## Assumptions

- The schema matches the backend database models in `tool_registry.models` exactly, so no mapping conversions are needed.
- Catalog data is static and loaded from the local filesystem (`catalog.yaml` bundled with the plugin).
