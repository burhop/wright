# Plan

Reuse `SurfaceWorkspace` and `LiveAppSurface`. Add a default-off Workflows
sidebar selection and a focused adapter component that filters only the Rivet
editor surface for the active workspace. Missing assets show a diagnostic, not
a fallback. Program-wide approval applies; real editor display remains
conditional on slice-058 manifest availability.
