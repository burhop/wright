"""Display an existing Matplotlib figure through the same Wright API."""

try:
    import matplotlib.pyplot as plt
except ImportError:
    print("Matplotlib is optional. Install it with: pip install matplotlib")
else:
    import wright

    figure, axes = plt.subplots()
    axes.plot([0, 1, 2, 3], [10, 12, 15, 19])
    axes.set_title("Measured load")
    axes.set_xlabel("Time (s)")
    axes.set_ylabel("Load (N)")
    handle = wright.display(
        figure,
        title="Measured load",
        description="Measured load rises from 10 N to 19 N.",
        display_id="matplotlib-load",
    )
    print(f"Created {handle.surface_id} revision {handle.revision}")
