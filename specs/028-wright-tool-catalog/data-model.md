# Data Model: Engineering Tool Catalog

This document specifies the Pydantic schemas in `schemas.py` that represent the catalog structures.

## Schemas

### 1. EnvVarDefinition
Represents required environment variables or credentials. Aligns with the core `tool_registry.models.EnvVarDefinition`.

* `name` (string): Env variable name (e.g. `ONSHAPE_API_KEY`)
* `label` (string): UI field label (e.g. `Access Key`)
* `description` (string, default `""`): Tooltip description
* `required` (boolean, default `True`): If input is required
* `secret` (boolean, default `False`): If masked input is required

### 2. DependencySpec
System and python package dependencies.

* `system` (list[string], default `[]`): System binary dependencies (e.g. `['freecad']`)
* `python` (list[string], default `[]`): Python modules (e.g. `['jarvis-onshape-mcp']`)
* `node` (list[string], default `[]`): Node package dependencies (e.g. `['@modelcontextprotocol/server-postgres']`)

### 3. CatalogEntry
Represents an installable MCP server in the catalog.

* `id` (string): Unique identifier (e.g. `freecad-mcp-sandraschi`)
* `name` (string): Human-readable name
* `vendor` (string): Vendor name/organization
* `description` (string): Detailed description of tools provided
* `domains` (list[string]): List of domain tags from taxonomy
* `tags` (list[string], default `[]`): Generic search tags
* `transport` (string: `stdio`, `sse`, or `webmcp`): Comm channel
* `command` (list[string] or string): Start command
* `source_url` (string, optional): Git source repository link
* `image_url` (string, optional): Icon source URL
* `locality` (string: `local` or `remote`)
* `weight` (string: `light`, `medium`, or `heavy`)
* `env_vars` (list[EnvVarDefinition], default `[]`): Env variables
* `dependencies` (DependencySpec, default empty): Dependencies

---

## Domain Taxonomy
Each catalog entry MUST declare one or more of the following domains:
* `cad`: Computer-Aided Design
* `code-cad`: Programmatic geometry/CAD
* `cloud-cad`: Cloud-based browser CAD
* `fea`: Finite Element Analysis
* `cfd`: Computational Fluid Dynamics
* `cam`: Computer-Aided Manufacturing
* `plm`: Product Lifecycle Management
* `bim`: Building Information Modeling
* `eda`: Electronic Design Automation
* `thermal`: Thermal analysis
* `tolerance`: Tolerance analysis/stackups
* `drafting`: Technical drafting/AutoCAD
* `mesh`: Polygon mesh modeling (Blender, SketchUp)
* `iot`: Internet of Things integration
