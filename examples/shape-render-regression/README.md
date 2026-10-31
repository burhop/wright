# Shape-to-image regression examples

Two text inputs, one reusable four-block workflow: shape description → SteveCAD geometry and capture; rendering description plus that actual capture → generated image.

| Case | Shape | Appearance | Observed execution time |
|---|---|---|---:|
| Cube | Create a cube | Render it as titanium on a table | 2m04s |
| Cylinder | Create a cylinder | Render it as ice floating in space | 2m05s |
| Repeat cube | Create a cube | Render it as titanium on a table | 1m34s |

The beta tester ran and inspected all three through Wright's normal browser UI without intervening developer changes. Each image-generation request contained its corresponding actual CAD capture. These are prepared use/reuse observations; they do not qualify installation, fresh authoring or physical engineering correctness. Detailed laboratory records remain local.

For regression execution, use [the exact saved workflow](saved-workflow.wflow) and [the case definitions](regression-cases.json). Connect authorized SteveCAD and a supported image-generation model, then run cube → cylinder → cube through the same saved workflow, changing only the two inputs. Open the actual captures and final images. Inspect normal run evidence for the capture handoff. No customer code or configuration repair, and no pixel-identical generative-image comparison.

![Titanium-like cube on a table](run-1-render.png)

![Ice-like cylinder in space](run-2-render.png)
