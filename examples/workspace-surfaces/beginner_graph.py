"""The smallest complete Wright graph: one import and no plotting package."""

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
