# Feature Specification: MCP Credential & Secret Setup

**Feature Branch**: `026-mcp-credential-setup`

**Created**: 2026-06-12

**Status**: Draft

**Input**: User description: "We need to be able to set up MCPs of all types. For example some require API keys. Research if there are other ways to support these MCPs and create a UI that can accept the needed values to run the MCP. Make sure all secret information is not put in the repo but exists in the user's config. As part of this exercise, install jarvis-onshape-mcp with our App. They will need a key so we need to update our UI for these situations. Acceptance criteria is that MCPs like the jarvis-onshape-mcp can be set up. Further, test cases should verify the OnShape MCP is working correctly."

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Configure an MCP Server Requiring Credentials (Priority: P1)

An engineer wants to add the Jarvis OnShape MCP to their Wright instance. The OnShape MCP requires two secrets — an API access key and an API secret key — to authenticate against the OnShape REST API. The engineer opens the MCP Tool Registry in the Wright UI, locates the OnShape MCP server entry, and sees that it requires credential configuration before installation. The UI presents labeled input fields for each required environment variable (e.g., `ONSHAPE_API_KEY`, `ONSHAPE_API_SECRET`). The engineer enters their credentials. The secrets are persisted securely in the user's local configuration file outside the repository — never committed to version control. After saving, the MCP server starts successfully using those credentials.

**Why this priority**: Without credential entry, MCPs requiring authentication simply cannot function. This is the core blocker for the entire feature.

**Independent Test**: Can be fully tested by registering the Jarvis OnShape MCP, entering credentials through the UI, and verifying the server starts and can list tools.

**Acceptance Scenarios**:

1. **Given** an MCP server is registered with required environment variables (`ONSHAPE_API_KEY`, `ONSHAPE_API_SECRET`), **When** the user opens the server's credential configuration in the UI, **Then** they see labeled input fields for each required variable with password masking for secret values.
2. **Given** the user has entered valid credentials, **When** they save and install/activate the server, **Then** the MCP server process launches with those credentials as environment variables and reports a healthy status.
3. **Given** credentials have been saved for a server, **When** the user reopens the credential configuration panel, **Then** saved values are shown as masked placeholders (e.g., `••••••••`) and can be updated or cleared.

---

### User Story 2 - Secure Secret Storage Outside Repository (Priority: P1)

An engineer's Wright instance stores all MCP secrets in a local user configuration file (`~/.config/wright/mcp-secrets.json`) that is outside the repository tree. The secrets file has restricted file permissions (owner-read-only). No secrets ever appear in the SQLite database, git-tracked files, or API responses.

**Why this priority**: Leaking secrets into version control or database fields accessible via the API would be a critical security violation. This is a hard requirement, not optional.

**Independent Test**: Can be tested by saving credentials through the UI and then verifying: (a) `~/.config/wright/mcp-secrets.json` exists with correct permissions, (b) the SQLite `mcp_servers.env_vars` column contains only variable *names* (not values), (c) `GET /api/mcp/servers` responses do not include secret values.

**Acceptance Scenarios**:

1. **Given** a user saves credentials for an MCP server, **When** inspecting the secrets storage file, **Then** secrets are stored in `~/.config/wright/mcp-secrets.json` with file permissions `0600` (owner read/write only).
2. **Given** credentials are saved, **When** the `mcp_servers` table `env_vars` column is queried, **Then** it contains only variable names and metadata (descriptions, required flags) — never plaintext secret values.
3. **Given** an MCP server with saved credentials, **When** the REST API `GET /api/mcp/servers` endpoint is called, **Then** the response includes environment variable names and whether they are configured, but never returns the actual secret values.

---

### User Story 3 - Pre-configured OnShape MCP in Wright Catalog (Priority: P2)

A new Wright user opens the Tool Registry and sees the Jarvis OnShape MCP listed in the catalog with a clear description, OnShape logo, and a "Requires Configuration" badge. They click "Configure," enter their OnShape API key pair, and install the server. The MCP tools (create_document, create_sketch, render_part_studio_views, etc.) become available in their workspace for the agent to use.

**Why this priority**: The OnShape MCP is the concrete validation case for the credential system. Having it pre-registered in the catalog makes the feature immediately useful and testable.

**Independent Test**: Can be tested by opening the Tool Registry page, finding the OnShape MCP, configuring credentials, installing, and verifying the agent can call at least one OnShape tool.

**Acceptance Scenarios**:

1. **Given** a fresh Wright deployment, **When** the user opens the Tool Registry, **Then** the Jarvis OnShape MCP is listed with the name "Jarvis OnShape MCP," an OnShape-related icon, the category "cad," and a description.
2. **Given** the OnShape MCP entry exists, **When** the user clicks to configure it, **Then** the UI shows two required fields: "ONSHAPE_API_KEY" (labeled "Access Key") and "ONSHAPE_API_SECRET" (labeled "Secret Key," with password masking).
3. **Given** valid OnShape credentials are configured, **When** the server is installed and started, **Then** the server's tool list includes OnShape CAD tools (e.g., `create_document`, `create_sketch`, `render_part_studio_views`).

---

### User Story 4 - Credential Configuration for Any MCP Type (Priority: P2)

An administrator registers a new custom MCP server that requires three environment variables: a public API URL, an API token, and a webhook secret. During registration through the existing "Add Server" flow, they can specify which environment variables are required and which should be treated as secrets (masked in UI). After registration, any user configuring this server sees the appropriate input fields in the credential panel.

**Why this priority**: The system must be generic, not hardcoded to OnShape. Any MCP should be able to declare its credential requirements.

**Independent Test**: Can be tested by registering a new MCP server with custom env_vars metadata, then verifying the credential UI renders the correct fields.

**Acceptance Scenarios**:

1. **Given** an administrator is adding a new MCP server, **When** they include environment variable definitions in the registration payload (with name, description, required flag, and secret flag), **Then** the server is registered and the variable definitions are stored.
2. **Given** an MCP server with declared environment variables, **When** a user opens its credential configuration, **Then** the UI renders a labeled input field for each variable, with secret variables using password-type inputs.
3. **Given** all required environment variables for an MCP server are configured, **When** the server is activated, **Then** the runtime passes all configured variables to the server process as environment variables.

---

### Edge Cases

- What happens when a user tries to install an MCP server that has required credentials but hasn't configured them yet? → The system prevents installation and shows a clear message: "This server requires credential configuration before it can be installed."
- What happens when saved credentials are invalid (e.g., expired API key)? → The MCP server fails to start and reports an error status with the error message visible in the UI; credentials can be re-entered.
- What happens when the secrets file (`~/.config/wright/mcp-secrets.json`) is missing or corrupted? → The system recreates the file with correct permissions on next write; previously configured servers show "credentials not configured" and require re-entry.
- How does the system handle concurrent writes to the secrets file? → File-level locking (advisory lock) prevents race conditions.
- What happens when a server is deleted? → Its credentials are also removed from the secrets file.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: System MUST provide a credential configuration UI panel for each MCP server that declares environment variables, with labeled input fields for each variable.
- **FR-002**: System MUST store MCP secret values in a local user configuration file (`~/.config/wright/mcp-secrets.json`) with restricted file permissions (`0600`), never in the repository, database fields, or API responses.
- **FR-003**: System MUST pass configured environment variables to MCP server processes when they are started (as OS-level environment variables injected into the subprocess).
- **FR-004**: System MUST support an environment variable metadata schema that includes: variable name, human-readable label, description, whether it is required, and whether it is a secret (should be masked in UI).
- **FR-005**: System MUST mask secret environment variable values in the UI using password-type input fields and show existing values as masked placeholders.
- **FR-006**: System MUST prevent installation/activation of an MCP server when required environment variables are not yet configured, showing a clear instructional message.
- **FR-007**: System MUST include the Jarvis OnShape MCP as a pre-registered catalog entry with environment variable definitions for `ONSHAPE_API_KEY` and `ONSHAPE_API_SECRET`.
- **FR-008**: System MUST remove stored credentials for an MCP server when that server is deleted from the registry.
- **FR-009**: System MUST NOT return secret values through the REST API — the `GET /api/mcp/servers` and related endpoints MUST only indicate whether each credential is configured (true/false), not its value.
- **FR-010**: System MUST allow users to update or clear previously saved credentials at any time through the UI.

### Key Entities

- **MCP Server**: Represents a registered MCP tool server. Extended with structured environment variable metadata (list of variable definitions with name, label, description, required, secret flags).
- **Environment Variable Definition**: Metadata about an environment variable an MCP server needs — its name, human label, description, whether required, and whether it contains a secret.
- **Credential Store**: A local JSON file (`~/.config/wright/mcp-secrets.json`) that maps server IDs to their environment variable values. File-permission protected, not version-controlled.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: Users can configure, save, and update credentials for any MCP server through the UI in under 60 seconds.
- **SC-002**: The Jarvis OnShape MCP successfully starts, lists tools, and responds to at least one tool call (`create_document` or `list_documents` equivalent) after credentials are configured through the UI.
- **SC-003**: No secret values appear in the SQLite database, API responses, or any file within the repository tree — verified by automated test scanning these locations after credential configuration.
- **SC-004**: The secrets storage file maintains `0600` permissions and is located outside the repository directory — verified by automated test after write operations.
- **SC-005**: When required credentials are missing, the system blocks server activation and shows a user-friendly message — verified by attempting to install a server without configuring required credentials.

## Assumptions

- Users have a home directory (`~`) writable by the Wright API process, and the `~/.config/wright/` directory can be created if it doesn't exist.
- The Jarvis OnShape MCP is installed as an `stdio`-type MCP server, launched via `uv run` with the `onshape-mcp` package.
- The existing `StdioRunner` already supports injecting environment variables via its `env` parameter — only the credential retrieval and injection at startup needs to be added.
- The existing `McpServerCreate` model's `env_vars` field (`dict[str, str]`) will be evolved to carry structured metadata (variable definitions) rather than raw key-value secret pairs.
- The Docker container deployment will mount a user config volume or use environment variables to provide secrets — this is out of scope for the initial implementation (local development focus).
- The OnShape API credentials provided by the user will be stored immediately as the initial seed data for the OnShape MCP credential store.
