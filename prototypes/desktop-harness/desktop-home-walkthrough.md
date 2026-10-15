# Wright 0.6.0 — quick desktop check

Open a **fresh conversation on the existing GB10 host**. Paste:

> Use the Wright plugin to open Wright home with `wright_home`. This is a read-only UI check: do not run workflows, apply setup, sign in or enable tools.

Then:

1. Choose **SteveCAD desktop demo**.
2. Under **Workflows**, open `stevecad-native.workflow.wflow`.
3. Inspect Diagram and Source. Click **Workspaces**; your workspace should remain selected.
4. Open **Connections**, search **SteveCAD**, then click **Saved setup**.
5. Open the saved plan. It should say **reviewable**. Do not approve/apply it for this check.
6. Narrow the panel and switch back to Workflows. Note any awkward controls, missing content or connection errors.

Tell this implementation chat whether those steps worked and what felt awkward.
A screenshot with UI annotations is useful. Do not include sign-in links or codes.

This uses fresh isolated test state. Original workspaces/runs remain on their
preserved connection. SteveCAD is **not authenticated yet**. Login needs a verified
Windows-to-GB10 callback route; the B: mapping alone does not supply that route.
No engineering result is claimed by this walkthrough.
