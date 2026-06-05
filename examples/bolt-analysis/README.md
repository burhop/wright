# Bolt Stress Analysis Example

This example demonstrates using Wright's agent API to trigger mechanical engineering calculations for a standard bolt subject to shear load, streaming the solver steps, and saving the calculation results.

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
- `bolt_stress.txt`: Structured report detailing dimensions, formulas, calculations, and safety factor validation.
- `validation.json`: Machine-readable validation results.
