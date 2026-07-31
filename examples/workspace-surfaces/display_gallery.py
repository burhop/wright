"""Safe table, passive HTML, pandas, and Pillow display examples."""

import wright


wright.display(
    [
        {"Time (s)": 0, "Load (N)": 10},
        {"Time (s)": 1, "Load (N)": 12},
        {"Time (s)": 2, "Load (N)": 15},
    ],
    title="Load data",
    description="Three load measurements by time.",
    display_id="load-table",
)

wright.display(
    "<section><h2>Result</h2><p>The maximum measured load is 15 N.</p></section>",
    title="Result summary",
    description="A passive HTML summary of the measured load.",
    display_id="safe-html-summary",
)

try:
    import pandas as pd
except ImportError:
    print("pandas gallery item skipped. Install it with: pip install pandas")
else:
    wright.display(
        pd.DataFrame({"Time (s)": [0, 1, 2], "Load (N)": [10, 12, 15]}),
        title="Pandas load data",
        description="Three load measurements in a pandas table.",
        display_id="pandas-load-table",
    )

try:
    from PIL import Image
except ImportError:
    print("Pillow gallery item skipped. Install it with: pip install pillow")
else:
    image = Image.new("RGB", (64, 64), color=(45, 125, 210))
    wright.display(
        image,
        title="Blue sample",
        description="A solid blue 64 by 64 pixel sample image.",
        display_id="pillow-sample",
    )
