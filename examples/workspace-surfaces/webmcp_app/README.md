# Scoped WebMCP reference app

This dependency-free managed app exposes `set_graph` only through its current Wright workspace/session/surface/generation/origin/server binding. Identically named tools in another page do not collide. Navigation, **Unregister tool**, surface disposal, runtime replacement, or disconnect removes the registration and cancels pending calls.

Start it through `webmcp.surface.json` and choose **Open in workspace**, **Open in browser**, or both. Wright's bridge is the stable route. The page may also register with a feature-detected native `document.modelContext`, but never creates that namespace and remains functional when native support is absent or rejects registration.

The manifest requests only `wright.webmcp.register`. Wright policy and the user's grant remain authoritative. The page has no Wright token, cannot select its binding, and connects to the reserved same-origin `/__wright/webmcp` endpoint using the presentation's host-only cookie.

For a standalone visual smoke check (without tool authority):

```powershell
python server.py --port 8765
```

Open `http://127.0.0.1:8765`. Registration will remain pending because only an authorized Wright presentation provides the scoped WebMCP endpoint. Stop with Ctrl+C.
