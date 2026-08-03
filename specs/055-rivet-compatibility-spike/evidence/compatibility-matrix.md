# Compatibility matrix

| Surface | Result | Evidence / required follow-up |
|---|---|---|
| Node runner and External Call | Conditional | Exact packages ran a synthetic graph and cancellation probe. Build a Wright-owned bridge in the next slice. |
| Editor IO/dataset/native seams | Conditional | Source exposes IO provider, browser IndexedDB dataset provider, and Tauri native API. Prove per-workspace injection in a real embedded build. |
| Remote debugger | Conditional | Local unauthenticated WebSocket connection was accepted. Never expose Rivet's endpoint directly; add a Wright-authenticated, generation-scoped adapter. |
| Offline source rebuild on Windows | Blocked | Committed Yarn cache lacks required Windows platform archives under `YARN_ENABLE_NETWORK=0`. Vendor/cache the selected platform or use a separately verified build supply chain. |
| Runtime network behavior | Conditional | Fixture has no network and static probe found no authorities; enforce runtime browser/network denial in a later embedded build. |
| Supply chain | Conditional | 259 installed packages had a declared legacy/current license. Complete security/vulnerability review before production selection. |
| Browser, Hermes, native, Docker | Unverified | No production adoption until these target contexts are separately tested. |
