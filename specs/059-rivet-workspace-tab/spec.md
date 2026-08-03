# Rivet Workspace Tab

Add a default-off Workflows entry to Wright workspace navigation. It hosts only
the existing isolated `LiveAppSurface` presentation path, retains the selected
surface across navigation, and shows actionable disabled/missing diagnostics.
It never imports Rivet into the Wright React tree.

Requirements: workspace/session isolation; keyboard-accessible tab entry;
retained surface on 100 switches; safe missing editor state; close/stop controls
through existing Surface controls; no persistence or runtime authority change.
