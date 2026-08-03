# Research

## Decisions

- Use the existing managed surface lifecycle rather than a file URL: it provides loopback routing, health checks, diagnostics, and retained tabs.
- Provision the complete manifest on the server: a browser cannot choose a launch command or artifact path.
- Keep manual import/export: it is a temporary non-authoritative compatibility mode approved by the user; workspace persistence remains in the existing adapter/persistence slices.
- Keep capabilities empty and sharing isolated: no bridge is needed for browser-native import/export.
