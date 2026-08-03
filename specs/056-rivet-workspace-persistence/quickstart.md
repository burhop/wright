# Independent verification journey

1. Enable `rivet_workflows_enabled` in a test configuration; do not install Rivet or Node.
2. Create a workflow with a synthetic `.rivet-project` and dataset sidecar.
3. Read it, save revision 2, and confirm workspace files contain the canonical content.
4. Retry the revision-1 save and confirm a conflict with no overwrite.
5. Delete and recover it; confirm content and sidecars return.
6. Rebuild the index and confirm it matches files.
7. Disable the feature and confirm existing Wright workspace APIs and startup continue normally while files remain intact.
