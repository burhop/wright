"""Rerun or update a stable display ID without creating duplicate tabs."""

import wright


first = wright.line(
    x=[0, 1, 2],
    y=[10, 12, 15],
    title="Measured load",
    x_label="Time (s)",
    y_label="Load (N)",
    description="Initial measurements reach 15 N.",
    display_id="measured-load",
)

updated = wright.line(
    x=[0, 1, 2],
    y=[10, 13, 18],
    title="Measured load",
    x_label="Time (s)",
    y_label="Load (N)",
    description="Updated measurements reach 18 N.",
    display_id="measured-load",
)

print(f"Updated {first.surface_id} from revision {first.revision} to {updated.revision}")
