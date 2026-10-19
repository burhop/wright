# Wright desktop walkthrough

Use after the named **0.16.0** update is confirmed installed. No workflow needs to run for these checks.

1. Start a fresh conversation on the existing GB10 host. Say: **“Open Wright Home.”**
2. Choose **SteveCAD desktop demo**. Open **Workflows**, open a saved workflow, switch **Diagram / Source**, then return Home.
3. Open **Connections**. Find SteveCAD and open its saved setup, or review its catalog setup. Your existing publisher account setup is already confirmed; installation is still a separate reviewed action.
4. Click **Connect SteveCAD → Open provider sign-in**. Sign in yourself and confirm the displayed code. Wright polls for completion—no SSH or callback setup. Then check connection readiness. Enable only the workspace tools you need; this does not approve workflow actions.
5. Open **Files**, download a nonsecret file, and confirm it reaches Windows.

Other useful checks:

- **“Create a Wright test workspace called Desktop UI check.”** Verify it appears in Home.
- **“Show my saved Wright workflows.”** Open one without starting a run.
- Custom MCP: **Connections → Add a custom MCP → Import MCP configuration (JSON)**. Preview and review its setup before applying. Commands run on GB10, not Windows.
- Enter private values only under **API keys and configuration values** after setup. Header imports retain names only; imported values are discarded. Never paste credentials into chat.
- To change a pinned version or credentials, open **Provider controls → Set up a replacement**, choose a new name, review the source, and configure/validate it separately. Existing connections and workflow bindings remain intact. Sources that cannot safely prefill must use reviewed catalog setup or a sanitized import.

Still experimental: generated process-UI authoring, automatic background reasoning/restart, native desktop tabs and Computer controls are not enabled. Personal login/consent and real engineering reviews remain yours. GB10 browser tests do not establish Windows panel/download acceptance.
