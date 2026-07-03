# Wright Demo Video Recording Script

**Target Duration**: 2 minutes 30 seconds

This script outlines the video storyboard, on-screen visuals, actions, and spoken narration for the official Wright demonstration video.

---

## Scene 1: Introduction & Docker Quickstart
*   **Duration**: 0:00 - 0:20 (20s)
*   **Visuals**: Screen capture of a clean terminal. The user types `docker compose -f docker-compose.minimal.yml up -d --build` to launch the container. As it loads, overlay the Wright logo and title: *"Wright: Local-First Agent Orchestration for Engineering"*.
*   **Action**: Zoom into the terminal showing uvicorn server process starting up, and browser navigating to `http://localhost:8080`.
*   **Spoken Narration**:
    > "Welcome to Wright, the open-source, local-first agent orchestrator designed for physical engineering. Getting started with the public alpha means launching the Docker appliance, then pointing Wright at your own model endpoint and selected engineering tools."

---

## Scene 2: Navigating the Web UI
*   **Duration**: 0:20 - 0:45 (25s)
*   **Visuals**: High-definition capture of the Wright web application. Hover over the primary alpha views: the **Agent Chat**, the **Tool Registry**, and the active **Workspace** with generated files and viewer panels.
*   **Action**: Click the "Tool Registry" tab, showing catalog and validation metadata for selected MCP servers.
*   **Spoken Narration**:
    > "The Wright console centers on agent chat, the tool registry, and local workspaces. Agent Chat lets you direct AI assistants using natural language. The Tool Registry shows selected MCP integrations and validation metadata. Workspace files and generated artifacts stay in local storage you control."

---

## Scene 3: Designing a Bracket with AI
*   **Duration**: 0:45 - 1:45 (60s)
*   **Visuals**: User in the Agent Chat typing: *"Design a parametric bracket with width 50, height 30, and a 5mm mounting hole."*
*   **Action**: Press enter. Show the chat streaming the agent's reasoning. The agent selects the OpenSCAD tool, writes the code, compiles it, runs a headless validation check, and displays the success checkmark.
*   **Spoken Narration**:
    > "Let's ask our agent to design a custom mechanical bracket. Instead of hoping the AI writes perfect CAD code from scratch, Wright steers a deterministic OpenSCAD kernel. The agent writes programmatic CAD parameters, triggers local validation tests, and confirms the design compiles without errors."

---

## Scene 4: OpenSCAD Render and Workspace Artifacts
*   **Duration**: 1:45 - 2:10 (25s)
*   **Visuals**: The 3D render of the bracket pops up directly in the chat panel. The user opens the workspace file view to see `bracket.scad` and `bracket.stl` listed.
*   **Action**: Click to download the CAD files and open them in a standard solid viewer.
*   **Spoken Narration**:
    > "Once compiled, the 3D render appears in the browser console. Generated files are saved in your local workspace in standard formats like STEP and STL, ready to inspect, export to a solid modeler, or slice for manufacturing."

---

## Scene 5: Outro & Call to Action
*   **Duration**: 2:10 - 2:30 (20s)
*   **Visuals**: Transition slide displaying links: GitHub Repository, Discord invite, and Docs site.
*   **Action**: Show the GitHub stars growth and contributor rocks images.
*   **Spoken Narration**:
    > "Wright is fully open-source, local-first, and built on open standards like the Model Context Protocol. Join the community, star the repo on GitHub, and help us build the future of AI-assisted physical design. Thanks for watching!"
