"""Display an existing Plotly figure using the bundled offline renderer."""

try:
    import plotly.graph_objects as go
except ImportError:
    print("Plotly is optional. Install it with: pip install plotly")
else:
    import wright

    figure = go.Figure(
        data=go.Scatter(x=[0, 1, 2, 3], y=[10, 12, 15, 19], mode="lines")
    )
    figure.update_layout(
        title="Measured load",
        xaxis_title="Time (s)",
        yaxis_title="Load (N)",
    )
    handle = wright.display(
        figure,
        title="Measured load",
        description="Measured load rises from 10 N to 19 N.",
        display_id="plotly-load",
    )
    print(f"Created {handle.surface_id} revision {handle.revision}")
