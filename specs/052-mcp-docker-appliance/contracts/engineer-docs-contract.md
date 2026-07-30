# Contract: Engineer Documentation

The engineer-facing documentation is for mechanical/design engineers who want to try Wright with bundled engineering MCPs.

## Required Content

- What the MCP appliance is
- When to use it instead of the standard Wright appliance
- Required prerequisites
- How to configure the environment file
- How to run with Docker or compose
- The local URL and port to open
- How to opt into remote/LAN access safely
- Included tools and what each can do
- Where to find third-party license, notice, no-warranty, and source-access materials bundled with the image
- SolidEdgeMCP internal-source build configuration and the fact that Solid Edge itself is not redistributed
- A simple verification prompt for each entry
- How to interpret health/unavailable statuses
- How to stop and clean up containers and MCP-specific volumes

## Style Rules

- Use plain engineering language.
- Keep commands copyable.
- Avoid implementation details in the quickstart.
- Link to maintainer documentation for source pins, licenses, and bundle updates.
- Never imply Solid Edge desktop/vendor assets are installed in the Linux appliance.

## Acceptance

A reviewer who is comfortable with CAD tools but not software development can complete first-run setup, verify one local MCP-backed operation, understand the SolidEdgeMCP source/build requirement, and clean up the trial environment from the guide alone.
