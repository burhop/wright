# Workspace Surfaces Examples

These examples are user-facing, runnable demonstrations of supported surface
contracts. Each example must state prerequisites, the expected panel/browser
result, offline behavior, security posture, and a cleanup command. Examples may
use only public Wright APIs and must not depend on a repository checkout once
packaged. Framework-specific examples pin their optional test dependency.

Keep intentionally hostile inputs out of this directory; they belong under the
test fixture root and must never be presented as copyable application code.

## Python graphics

- `beginner_graph.py`: one import, no optional package, one durable line graph.
- `updating_graph.py`: two revisions of one stable logical graph.
- `matplotlib_graph.py`: an optional Matplotlib figure with an accessible label.
- `plotly_graph.py`: an optional Plotly figure rendered from the offline bundle.
- `display_gallery.py`: native tables, passive sanitized HTML, pandas, and Pillow.

Run a script with Wright's **Run file** action. The expected result is a labeled
surface in the center panel. Closing the tab retains durable output; use the
surface's explicit **Delete output** action to remove it. No example opens a
port or downloads renderer code.
