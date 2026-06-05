# Quickstart Example

This is a minimal "hello world" example demonstrating how to connect to the Wright local API, query the system health status, and fetch the active agent name.

## How to Run

1. Make sure the Wright backend API is running at `http://localhost:8000`.
2. Make sure you have python installed and package dependencies:
   ```bash
   pip install httpx
   ```
3. Run the script:
   ```bash
   python main.py
   ```

## Expected Output

```text
Connecting to Wright API at http://127.0.0.1:8000...
API Health: State=connected, Latency=1.5ms
Active Agent: hermes
Success: Quickstart check completed successfully!
```
