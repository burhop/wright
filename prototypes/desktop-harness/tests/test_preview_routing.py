"""Exercise desktop JSON routes with a production-style frontend fallback."""
import importlib.util
from pathlib import Path
import unittest

from fastapi import APIRouter, FastAPI
from fastapi.responses import HTMLResponse
from fastapi.testclient import TestClient


class PreviewRoutingTests(unittest.TestCase):
    def test_desktop_reads_and_writes_precede_frontend_without_losing_routes(self):
        spec = importlib.util.spec_from_file_location(
            "preview_server", Path(__file__).resolve().parents[1] / "preview_server.py"
        )
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        app = FastAPI()

        @app.get("/api/health")
        def health():
            return {"healthy": True}

        @app.get("/{path:path}", response_class=HTMLResponse)
        def frontend(path: str):
            return "<html>Workspace frontend</html>"

        desktop = APIRouter(prefix="/api/desktop")

        @desktop.get("/workspaces")
        def workspaces():
            return {"workspaces": []}

        @desktop.post("/connect")
        def connect():
            return {"connected": True}

        module.include_desktop_router(app, desktop)
        with TestClient(app) as client:
            response = client.get("/api/desktop/workspaces")
            self.assertEqual(response.status_code, 200)
            self.assertEqual(response.headers["content-type"], "application/json")
            self.assertEqual(response.json(), {"workspaces": []})
            self.assertEqual(client.post("/api/desktop/connect").json(), {"connected": True})
            self.assertEqual(client.get("/api/health").json(), {"healthy": True})
            self.assertIn("Workspace frontend", client.get("/workspace/example").text)


if __name__ == "__main__":
    unittest.main()
