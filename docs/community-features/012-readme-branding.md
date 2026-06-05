# Feature Brief: README Overhaul & Branding

Transform the Wright README from an internal developer reference into a high-impact landing page that converts visitors into users and contributors within 30 seconds, modeled after top agentic framework repos like OpenHands (64k+ stars), CrewAI, and OpenClaw.

## What to build

### Visual Identity

1. **Project logo** — Design or generate a professional SVG logo for Wright that combines engineering/mechanical and AI themes. The logo should work at small sizes (32px favicon) and large sizes (README hero). Store in `docs/images/wright-logo.svg` and `docs/images/wright-logo.png` (high-res export).

2. **Social preview image** — Create a 1280×640px image for GitHub's social preview (shown when the repo link is shared on Slack, Twitter, etc.). Include the Wright logo, tagline ("Local-first AI mechanical engineer"), and 3-4 key feature icons. Store in `docs/images/social-preview.png`. Document how the repo owner should upload it via GitHub Settings → Social Preview.

### README Structure Redesign

Restructure `README.md` to follow the proven layout used by popular repos:

3. **Hero section** — At the very top:
   - Centered Wright logo
   - One-line tagline: "A digital engineer, designer, and mechanical analyst — powered by local-first multi-agent AI."
   - Badge row: Build status (GitHub Actions), License (MIT), Docker Pulls, Python version, Node.js version, GitHub stars
   - Use shields.io badge URLs

4. **"Why Wright?" section** — Before the architecture section, add a narrative that explains:
   - The problem: Mechanical engineers need AI assistance but can't send proprietary designs to cloud APIs
   - The solution: Wright runs entirely on your local machine (Dell DGX Spark), orchestrating multiple AI agents for CAD, FEA, and manufacturing
   - Who it's for: Mechanical engineers, manufacturing teams, and engineering shops that need AI but can't use cloud services
   - Key differentiators: offline-first, multi-agent, full-stack appliance, Docker-deployable

5. **Feature highlights** — A visually scannable section with emoji-prefixed cards:
   - 🔧 Parametric CAD Generation (OpenSCAD via MCP)
   - 🧮 Finite Element Analysis
   - 🏭 Manufacturing Pipeline Automation
   - 🤖 Multi-Agent Orchestration (Hermes + adapters)
   - 🔒 100% Local — No Cloud Required
   - 🐳 One-Command Docker Deployment

6. **Demo screenshots** — Embed the existing UI screenshots (currently loose in repo root as `screenshot_*.png`). Move them to `docs/images/` and embed with captions showing: the agent chat interface, the tool registry, and the file vault.

7. **Simplified Quick Start** — Reduce to the absolute minimum:
   ```
   # Docker (recommended)
   git clone ... && cd wright
   cp docker/.env.example docker/.env  # edit with your LLM API key
   make docker-build && docker compose up
   # Open http://localhost:8080
   ```

8. **Architecture section** — Keep the existing content but add a Mermaid diagram showing the high-level component flow (API → Agent Adapters → Tool Registry → MCP Tools).

9. **Contributing callout** — A brief section encouraging contributions with a link to CONTRIBUTING.md and a mention of "Good First Issues".

10. **Footer** — License info, star history badge (using star-history.com), and contributor avatars.

### Cleanup

11. **Move screenshots** — Relocate `screenshot_agent_chat.png`, `screenshot_file_vault.png`, `screenshot_initial.png`, and `screenshot_tool_registry.png` from the repo root to `docs/images/`. Update any existing references.

## Constraints

- The README must remain a single file (no splitting into multiple docs — that's the docs site feature)
- The Docker Quick Start and architecture sections can be condensed but their information must not be lost (detailed Docker docs will live in the docs site)
- Do not modify any source code, Docker files, or CI/CD workflows
- All badge URLs should use shields.io for consistency
- The README should render correctly on both GitHub and npm/package registries
