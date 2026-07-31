# Python graphics in the workspace

Wright can turn a Python value into a durable graph, table, image, or safe HTML
document in the workspace. You do not need to choose a port, run a web server,
write HTML, or know JavaScript.

## Your first graph

Create a Python file in the active workspace and paste this program:

```python
import wright

graph = wright.line(
    x=[0, 1, 2, 3],
    y=[10, 12, 15, 19],
    title="Measured load",
    x_label="Time (s)",
    y_label="Load (N)",
    description="Measured load rises from 10 N to 19 N over three seconds.",
    display_id="measured-load",
)

print(f"Created {graph.surface_id} revision {graph.revision}")
```

Run the file from Wright. A **Measured load** surface appears in the center
panel. It contains the labeled graph and a data-table/text fallback for
accessibility. The output is durable by default, so it remains after Python
exits.

`wright.line`, `wright.bar`, `wright.scatter`, and `wright.histogram` use only
the Python standard library. A new engineer can therefore create a graph from
an installed Wright release without installing a plotting framework.

## Update one graph instead of creating tabs

The `display_id` is the graph's logical name for the current workspace task. For
a Wright-run file, the task identity is stable for that file path, so reuse the
same `display_id` when you revise values and rerun the program:

```python
wright.line(
    x=[0, 1, 2, 3],
    y=[10, 13, 18, 22],
    title="Measured load",
    x_label="Time (s)",
    y_label="Load (N)",
    description="Updated load rises from 10 N to 22 N.",
    display_id="measured-load",
)
```

Wright updates the existing logical surface and records a new immutable
revision. A late or stale revision cannot replace the current one. Choose
**History** on the surface to inspect the labeled revision list.

## Existing plotting and data objects

`wright.display(value, ...)` recognizes common objects lazily:

- Matplotlib figures become PNG data.
- Plotly figures use Wright's bundled offline Plotly renderer.
- pandas data frames become semantic tables.
- Pillow images become PNG data.
- SVG strings and passive HTML are sanitized before rendering.
- Objects with a bounded `_repr_mimebundle_` use supported safe media only.
- Other values receive an inert text fallback.

These packages are optional. Install only the one your program needs, for
example `pip install matplotlib`, `pip install plotly`, `pip install pandas`, or
`pip install pillow`. Wright does not import any of them when `import wright`
runs. See the runnable `matplotlib_graph.py`, `plotly_graph.py`, and
`display_gallery.py` examples in `examples/workspace-surfaces`.

## Accessibility

Always provide a short `description` that communicates the conclusion a person
should learn without seeing the graphic. Include units in axis labels. Wright
uses the description as the graph's accessible name and retains a table or text
fallback when one is available.

Good: `"Load rises from 10 N to 19 N over three seconds."`

Avoid: `"A graph."`

## Offline and security behavior

The Python helper never starts or discovers a server. Wright injects a
short-lived display endpoint and execution token only when it runs the file.
The token is bound to the authenticated user, workspace, session, task, and
execution, and Wright revokes it when execution ends. The helper returns an
identifier and revision, not a reusable credential.

Graph data and renderer code work offline. Plotly is shipped as a lazy local
bundle; it is not downloaded from a CDN. Server-side limits still bound points,
representations, JSON depth/items, encoded bytes, and validation time.

Ordinary HTML is passive and sanitized. `active_html=True` is a deliberate
advanced request for an isolated, unprivileged document; it does not grant
Wright bridge, file, credential, tool, device, or network authority. Prefer a
native graph, table, SVG, image, or passive HTML whenever possible.

## History and deletion

Closing a surface tab does not delete its durable output. Stopping a future live
application is also a different action.

**Delete output** removes the durable surface and its revision history only
after Wright shows that the operation cannot be recovered. Content-addressed
payload cleanup is then scheduled under workspace retention policy. Wright
reports that state explicitly instead of claiming immediate physical erasure.

## Troubleshooting

**“No Wright display execution is configured”**

Run the file from Wright. A normal terminal is not given workspace authority.
For explicit local development, configure `WRIGHT_DISPLAY_ENDPOINT`,
`WRIGHT_DISPLAY_TOKEN`, and `WRIGHT_DISPLAY_WORKSPACE_ID`; Wright never guesses
or starts an endpoint.

**The graph was rejected as stale**

Your process sent a lower or skipped revision. Rerun from the current Wright
execution or create a new `display_id` for a genuinely different logical
output.

**The value is too large or contains a non-finite number**

Remove `NaN`/infinity, reduce the number of points, or split the output. Wright
fails before transport when the SDK can detect the problem and validates again
at the service boundary.

**The interactive Plotly graph could not render**

The accessible fallback remains visible. Open **Diagnostics** for the stable
error and correlation ID. Verify that Plotly data contains finite JSON values.

**An optional example says to install a package**

Install the named package into the Python environment Wright uses, then rerun.
The base `wright.line`/`bar`/`scatter`/`histogram` helpers need no optional
package.
