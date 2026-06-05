# Feature Brief: Community Engagement Infrastructure

Set up the communication channels, example projects, and marketing assets needed to attract users and contributors to Wright. This is the outward-facing "community building" work — the channels where people discover, learn about, and engage with the project beyond GitHub Issues and PRs.

## What to build

### Communication Channels

1. **Discord server** — Create and configure a Wright community Discord server with channels:
   - `#announcements` (read-only for members) — Release notes, breaking changes, project milestones
   - `#general` — Open discussion about Wright, AI, mechanical engineering
   - `#support` — Help with installation, configuration, and usage
   - `#contributing` — Discussion for contributors (PRs, feature ideas, architecture questions)
   - `#showcase` — Community members sharing what they've built with Wright
   - `#off-topic` — Non-Wright conversation
   - Create a server invite link and add it to: README.md, CONTRIBUTING.md, SUPPORT.md, and the docs site
   - Set up basic moderation (rules channel, verification level, auto-mod for spam)
   - Document the Discord setup and admin instructions so the project owner can manage it

2. **GitHub Discussions integration** — Ensure GitHub Discussions (set up in feature 013) is cross-linked from:
   - The Discord #support channel (pin a message directing complex questions to Discussions for better searchability)
   - The README.md
   - The docs site

### Example Projects

3. **Examples directory** (`examples/`) — Create 3-5 self-contained example projects that demonstrate Wright's capabilities:
   - `examples/quickstart/` — Minimal "hello world" that connects to the API and runs a simple agent task
   - `examples/bracket-design/` — A mechanical bracket parametric design using the CAD tools
   - `examples/bolt-analysis/` — Bolt stress analysis using engineering calculation tools
   - Each example should include:
     - A `README.md` explaining what it demonstrates and how to run it
     - Any necessary input files (CAD templates, material specifications)
     - Expected output or screenshots showing the result
   - Examples should work with the Docker deployment (no local dev setup required)

### Launch Content

4. **Launch blog post** — Write a markdown blog post (stored in `docs/blog/` or as a draft for Dev.to/Medium):
   - Title: "Introducing Wright: Your Local-First AI Mechanical Engineer"
   - Sections:
     - The problem: Why mechanical engineers need local AI (IP protection, air-gapped networks, latency)
     - What Wright does: Multi-agent orchestration for CAD, FEA, and manufacturing
     - How it works: Architecture overview with diagrams
     - Getting started: Docker quickstart
     - What's next: Roadmap highlights
     - How to contribute: Link to GitHub and Discord
   - Include screenshots or demo GIF
   - Target length: 1500-2000 words

5. **Demo recording script** — Write a script/outline for a 2-3 minute demo video:
   - Scene 1: Show the Docker quickstart (15 seconds)
   - Scene 2: Navigate the Wright web UI (15 seconds)
   - Scene 3: Chat with the AI agent to design a bracket (60 seconds)
   - Scene 4: Show the tool registry with MCP tools (15 seconds)
   - Scene 5: Show the generated CAD output (15 seconds)
   - Scene 6: Call to action — GitHub link, Discord invite
   - Store the script in `docs/demo-script.md`

### Contributor Onramps

6. **"Good First Issue" curation** — Create 5-10 GitHub Issues labeled `good first issue` that are:
   - Self-contained (don't require understanding the full architecture)
   - Well-described (include context, expected outcome, relevant files)
   - Appropriately scoped (completable in 2-4 hours for a new contributor)
   - Covering different skill sets: Python backend, TypeScript frontend, documentation, Docker, testing
   - Store issue templates/drafts in `docs/good-first-issues.md` so the project owner can create them

7. **Contributor recognition** — Set up contributor acknowledgment:
   - Add an "all-contributors" configuration (`.all-contributorsrc`) or document how to use GitHub's built-in contributor graph
   - Create a Contributors section in the README (can be auto-generated)
   - Document the recognition policy in CONTRIBUTING.md

### Discoverability

8. **Awesome list submissions** — Prepare submissions to relevant curated lists:
   - Draft a submission PR description for `awesome-ai-agents` (or equivalent 2026 list)
   - Draft a submission for engineering-focused awesome lists
   - Draft a submission for Docker/self-hosted project lists
   - Store drafts in `docs/awesome-list-submissions.md` with links to the target lists and their submission requirements
   - Note: These should only be submitted AFTER the docs site and README overhaul are complete

### Project Metadata

9. **Star history badge** — Add a star-history.com embed or badge to the README showing GitHub star growth over time. Store the embed code in the README branding feature (012) coordination doc.

## Constraints

- Do not modify any application source code, Docker files, or CI/CD workflows
- Discord setup must be documented as instructions (you can't create a Discord server via code)
- Example projects should use the existing API — do not create new API endpoints for examples
- The blog post is a draft — the project owner decides when and where to publish
- Good First Issues are drafts — the project owner creates the actual GitHub Issues
- Awesome list submissions should only happen after the repo meets their quality requirements
- All content should be written in a professional, welcoming tone that encourages participation
