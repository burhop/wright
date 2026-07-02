# Offline E2E Smoke Tests

These pytest smoke tests exercise constitution-required end-to-end seams without
live agents, Docker, network calls, credentials, or proprietary host software.

The shared fixture in `conftest.py` uses a temporary SQLite database, runs API
migrations against that database, enables `WRIGHT_TESTING=1`, and seeds fake MCP
state only where a test needs it.

Covered seams:

- API health
- default agent registry behavior
- MCP listing through API routes
- Wright gateway tool listing and mocked call path
