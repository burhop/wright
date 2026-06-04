# Feature Specification: Enhanced Tool Registry UI

**Feature Branch**: `009-tool-registry-enhanced-ui`

**Created**: 2026-06-04

**Status**: Draft

**Input**: User description: "We want to update the tool registry to include more MCP servers with a better UI offering more functionality. We want to differentiate between when we need to install the software and MCP server locally and the ones where the MCP server is out on the network and we just need to connect to it. For each tool we need an image (Maybe from the github repo if that is its origin and a description on what it is and what it means to install it. If it is installed already, we need a button to check for updates, and if there is one, allow it to be updated. We also need a way to uninstall it. The URL for most of the UI work is: http://promaxgb10-9666:5173/tool-registry."

---

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Browse the MCP Server Catalog (Priority: P1)

A user opens the Tool Registry page and sees a rich catalog of MCP servers. Each server entry displays a logo/image, a clear name, a short description, and a visual badge that immediately communicates whether the server runs locally (requiring a local install) or lives on the network (requiring only a connection URL). The user can browse, search, and filter this catalog to discover capabilities for their workspaces.

**Why this priority**: Discovery is the entry point to all other actions. If the catalog experience is poor, users cannot take advantage of any of the following stories. This is the foundational user journey.

**Independent Test**: Can be fully tested by loading the Tool Registry page with a seeded list of servers and verifying that images, names, descriptions, and type badges are rendered correctly — no install actions needed.

**Acceptance Scenarios**:

1. **Given** the Tool Registry page is loaded, **When** the server list renders, **Then** every server card displays a logo/image, a name, a description, and a badge indicating "Local" or "Network" type.
2. **Given** the server list is visible, **When** the user types in the search box, **Then** the displayed cards are filtered in real time to match the search query against name and description.
3. **Given** the server list is visible, **When** the user selects a category filter (e.g., "Local" or "Network"), **Then** only servers matching that category type are shown.
4. **Given** a server has a GitHub repository as its source, **When** its card is displayed, **Then** the card shows the repository owner avatar or the project logo fetched from the repository metadata.
5. **Given** a server card is displayed, **When** the user hovers over it, **Then** a smooth visual hover effect indicates the card is interactive.

---

### User Story 2 - Install a Local MCP Server (Priority: P2)

A user sees a server in the catalog that is marked as "Local" (meaning the server software must be installed on the machine). The card clearly explains what the server does and what installing it means (e.g., it will install an npm package or Python package). The user clicks Install, sees a progress state, and upon success the card updates to show "Installed" along with the version that was installed.

**Why this priority**: Installation is the primary action for locally-hosted servers. Without it, users cannot use any local tooling. Clear install-type differentiation prevents user confusion about why some servers need local software.

**Independent Test**: Can be fully tested using a mock server that simulates an install operation returning a success response, verifying that the button state transitions from "Install" → "Installing…" → "Installed [version]".

**Acceptance Scenarios**:

1. **Given** a Local server card shows "Not Installed", **When** the user reads the card, **Then** the card includes a brief description of what the install process will do (e.g., "Installs the uvx package locally").
2. **Given** the user clicks the Install button on a Local server, **When** the install is in progress, **Then** the button displays a loading/spinner state and is disabled to prevent double-clicks.
3. **Given** the install completes successfully, **When** the card re-renders, **Then** it shows "Installed" with the installed version number and the Install button is replaced.
4. **Given** the install fails, **When** the error is returned, **Then** the card displays an inline error message describing why the install failed, and the Install button is available to retry.

---

### User Story 3 - Check for Updates and Update an Installed Local Server (Priority: P3)

A user has a Local MCP server installed and wants to know if there is a newer version available. They click a "Check for Updates" button. If an update is available, a notification appears on the card with the new version number and an "Update" button. The user clicks Update and the server is updated in-place.

**Why this priority**: Keeping tooling current is important for stability and new features. This is a secondary lifecycle action after initial install.

**Independent Test**: Can be fully tested by mocking an "update available" API response, verifying the update banner appears and clicking Update triggers the update endpoint.

**Acceptance Scenarios**:

1. **Given** a Local server card shows "Installed", **When** the user clicks "Check for Updates", **Then** the system queries for the latest version and displays either "Up to date" or "Update available: vX.Y.Z".
2. **Given** an update is available, **When** the user clicks "Update", **Then** the card shows an in-progress state and, upon success, shows the newly installed version.
3. **Given** "Check for Updates" is clicked, **When** the check is in progress, **Then** the button shows a spinner and is disabled.
4. **Given** the version check network call fails, **When** the error occurs, **Then** a non-blocking error message is shown on the card and the user can retry.

---

### User Story 4 - Connect to a Network MCP Server (Priority: P2)

A user sees a server in the catalog marked as "Network" (meaning the server is already running somewhere on the network and only needs a connection URL). The card displays a URL field or connection endpoint. The user fills in the URL if needed and clicks "Connect". Upon success, the server is listed as "Connected" and is available for use in workspaces.

**Why this priority**: Network servers are a distinct installation-free path. Confusing users about whether they need to install software or just connect is a critical UX problem. This story makes the distinction clear and actionable.

**Independent Test**: Can be fully tested by pre-seeding a Network-type server with a known URL, clicking Connect, and verifying the card transitions to "Connected" state with no local install required.

**Acceptance Scenarios**:

1. **Given** a Network server card is displayed, **When** it renders, **Then** the card clearly shows a "Network / Remote" badge and explains that no local software install is required.
2. **Given** a Network server requires a URL, **When** the user views the card, **Then** an editable URL field is visible (pre-populated if a default exists).
3. **Given** the user provides a valid URL and clicks "Connect", **When** the connection succeeds, **Then** the card shows "Connected" and the server becomes available.
4. **Given** the connection URL is invalid or the server is unreachable, **When** the user clicks "Connect", **Then** an inline error message describes the connection failure.

---

### User Story 5 - Uninstall a Local MCP Server (Priority: P3)

A user decides they no longer need a locally installed MCP server. They click "Uninstall" on the server card, see a confirmation prompt, and upon confirming, the server is removed from the local machine. The card reverts to the "Not Installed" state, retaining the entry in the catalog so the user can reinstall later.

**Why this priority**: Lifecycle management is complete only with the ability to remove software. This is a cleanup action less critical than install or update but necessary for good housekeeping.

**Independent Test**: Can be fully tested by mocking an uninstall API response and verifying the card reverts to the "Not Installed" state without removing the entry from the catalog.

**Acceptance Scenarios**:

1. **Given** a Local server shows "Installed", **When** the user clicks "Uninstall", **Then** a confirmation dialog appears asking the user to confirm before proceeding.
2. **Given** the user confirms the uninstall, **When** the operation completes, **Then** the card reverts to "Not Installed" state with an Install button available.
3. **Given** the uninstall fails, **When** the error is returned, **Then** the card shows an error message and remains in the "Installed" state.

---

### Edge Cases

- What happens when the logo/image URL for a server is unavailable or returns an error? The card should display a fallback placeholder icon without breaking the layout.
- What happens when the catalog contains zero servers? An empty state should be displayed with a clear message and a prompt to add a custom server.
- What happens when both search and category filters are applied simultaneously? The results should match both criteria (AND logic).
- What happens when a user attempts to install a server while another install is already in progress on the same card? The Install button should remain disabled until the current operation completes.
- What happens when the network version-check times out? A timeout error should be shown without blocking the rest of the UI.

---

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: The Tool Registry page MUST display each MCP server with a visual image or logo, a name, a short description, and a deployment-type badge ("Local" or "Network").
- **FR-002**: The system MUST differentiate between "Local" servers (requiring local software installation) and "Network" servers (requiring only a connection URL), displaying each type with distinct visual treatment and different action flows.
- **FR-003**: Each server card MUST display a description that explains what the server does and, for Local servers, what installing it means (packages, dependencies).
- **FR-004**: For servers with a GitHub repository as their source, the system MUST attempt to display the repository avatar or project logo as the server image.
- **FR-005**: The system MUST provide a search input that filters visible server cards in real time by name and description.
- **FR-006**: The system MUST provide category/type filter controls that allow the user to filter by deployment type ("Local", "Network") or by functional category (e.g., "simulation", "CAD").
- **FR-007**: For Local servers that are not installed, the system MUST display an "Install" button and a description of what the install process entails.
- **FR-008**: For Local servers that are installed, the system MUST display a "Check for Updates" button that queries the latest available version.
- **FR-009**: When an update is available for an installed Local server, the system MUST display the new version number and an "Update" button that triggers the update process.
- **FR-010**: For Local servers that are installed, the system MUST display an "Uninstall" button that, after confirmation, removes the server software from the local machine.
- **FR-011**: For Network servers, the system MUST display a connection URL field (editable if not yet connected) and a "Connect" button.
- **FR-012**: All install, update, connect, and uninstall operations MUST show an in-progress loading state on the relevant button/card and prevent duplicate submissions.
- **FR-013**: All operation failures (install, update, uninstall, connect, version check) MUST surface an inline error message on the affected card without crashing or navigating away.
- **FR-014**: The catalog MUST retain a server entry even after it is uninstalled, so the server can be reinstalled without re-registering.
- **FR-015**: The system MUST display an empty state when no servers match the active search/filter criteria.

### Key Entities

- **MCP Server Entry**: Represents a single MCP server in the catalog. Key attributes: name, description, image URL, deployment type (local/network), category, install status, installed version, connection URL (network-only), update availability.
- **Deployment Type**: A classification ("Local" vs "Network") that determines the available actions (install/uninstall/update vs connect/disconnect) and the explanatory copy shown to the user.
- **Update Status**: A record of the current installed version and the latest available version for a Local server, used to determine if an update is available.

---

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: Users can determine whether a server requires local installation or only a network connection within 3 seconds of viewing any server card, without reading documentation.
- **SC-002**: The install-to-confirmation feedback loop (clicking Install → seeing "Installed" confirmation) completes in under 30 seconds for standard package installs on the target hardware.
- **SC-003**: Searching or filtering the catalog produces visible, accurate results within 200 milliseconds of user input on the target hardware.
- **SC-004**: A user attempting to check for updates on an installed server receives feedback (up-to-date or update available) within 5 seconds for a locally reachable update source.
- **SC-005**: Zero unrecoverable UI crashes occur when server images fail to load or when any API operation returns an error response.
- **SC-006**: 100% of server cards in the catalog display a meaningful image (real logo or fallback placeholder) — no broken image states are visible to the user.

---

## Assumptions

- The backend API already has endpoints for install, uninstall, and server listing; the version-check endpoint may need to be added or extended.
- Server logo/image URLs are either stored in the server metadata in the database or are derivable from a GitHub repository URL associated with the server.
- The distinction between "Local" and "Network" deployment types is already encoded in the server's `type` field (e.g., `stdio` = Local, `sse`/`webmcp` = Network) or will be added as an explicit field.
- The update-check mechanism compares the installed package version against the latest available version for the relevant package manager (e.g., npm, pip, uvx).
- The target UI URL (http://promaxgb10-9666:5173/tool-registry) runs the frontend in development mode against the local backend API.
- Mobile support is out of scope; the UI is desktop-only.
- Authentication and authorization are out of scope for this feature — all users have access to all registry actions.
- The existing "Register Custom Tool" modal is retained as-is; this feature enhances the catalog view and card interactions only.
