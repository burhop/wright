# Bracket Design CAD Example

This example demonstrates using Wright's agent endpoints to trigger a parametric 3D CAD design task, stream the decision/code process from the active LLM agent, and write the final OpenSCAD CAD source file and metadata details.

## How to Run

1. Make sure the Wright backend API is running at `http://localhost:8000`.
2. Install package dependencies:
   ```bash
   pip install httpx
   ```
3. Run the script:
   ```bash
   python main.py
   ```

## Output Artifacts

Running the script creates an `output/` directory with:
- `bracket.scad`: The generated OpenSCAD design script.
- `metadata.json`: JSON file detailing design dimensions and validation metadata.
