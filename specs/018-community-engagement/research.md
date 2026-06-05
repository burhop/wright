# Research and Decision Log: Community Engagement Infrastructure

This document records the architectural choices, tools, and layout decisions made for the community engagement feature.

## 1. Example Projects Design

### Decision
Implement three example projects under the `examples/` directory using Python 3.11+ and standard HTTP client libraries (e.g., `requests` or `httpx` and `urllib3`) to communicate with the Wright API.

*   `examples/quickstart/`: Demonstrates connecting to the local API endpoint (`http://localhost:8000`), verifying the agent state, and executing a simple status checker script.
*   `examples/bracket-design/`: Executes a parametric CAD script utilizing Wright CAD tool endpoints to generate a 3D bracket CAD file.
*   `examples/bolt-analysis/`: Runs a script that sends bolt dimensions and materials to the analysis endpoint and outputs a calculations report.

### Rationale
*   Python is the standard language for engineering script automation and matches Wright's backend.
*   By keeping examples in standalone subdirectories with simple `main.py` entry points and `README.md` files, new users can run them instantly.
*   These scripts show users how to programmatically integrate Wright into their local engineering workflows.

### Alternatives Considered
*   *Bash scripts with `curl`*: Rejected because parsing JSON CAD specs or analysis results in bash is complex and not user-friendly for mechanical engineers.
*   *Node.js scripts*: Rejected since Python is much more prevalent in mechanical engineering and scientific computing.

---

## 2. Contributor Recognition Tooling

### Decision
Initialize `.all-contributorsrc` configuration in the root directory. Document commands for the `all-contributors-cli` in `CONTRIBUTING.md`.

### Rationale
*   All Contributors is a widely recognized standard for honoring code and non-code contributions (docs, tutorials, moderation, issues).
*   Allows maintainers to keep a clean, visual table of contributors in the `README.md` that is easy to update.

### Alternatives Considered
*   *Manual README list*: Rejected because it is error-prone, hard to keep aligned, and doesn't format contributor avatars automatically.

---

## 3. Communication Strategy

### Decision
Integrate a permanent Discord server invite link and GitHub Discussions link directly into:
1.  Root `README.md` (as visual badges and text links)
2.  `CONTRIBUTING.md` (in the communication section)
3.  `SUPPORT.md` (as the primary support channel)
4.  Documentation site configuration (as standard social icons/links)

### Rationale
*   Multiple entry points ensure high discoverability of community spaces.
*   Clearly separates immediate chat (Discord) from long-term searchable Q&A (GitHub Discussions).
