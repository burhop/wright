# Viewer Capability Record

Recorded 2026-09-16 against `dev` commit `6c0602a4`.

| Format | In-app capability                                                                                                                  | Offline capability                                                                             | Required Trace behavior                                                                                                                            |
| ------ | ---------------------------------------------------------------------------------------------------------------------------------- | ---------------------------------------------------------------------------------------------- | -------------------------------------------------------------------------------------------------------------------------------------------------- |
| STL    | Interactive Three.js viewer registered through `STLLoader`; the retained campaign `source_mesh.stl` opened in the production UI with nonblank canvas pixels | The current viewer depends on the built application and is not a standalone file-origin bundle | Use the Wright viewer in-app. Export a recorded preview and original unless a self-contained viewer asset set is deliberately bundled and tested.  |
| STEP   | A real `mounting-bracket.step` fixture exists. No geometry loader is registered; generic text reading is covered by provider tests | No bundled STEP viewer                                                                         | Present a linked display representation when recorded, retain the original, and explicitly state that interactive geometry viewing is unavailable. |
| 3MF    | No loader, registry contribution, or real fixture was found                                                                        | No bundled 3MF viewer                                                                          | Present a recorded preview and original-file fallback with an explicit viewer-unavailable state.                                                   |

These are capability observations, not engineering validation. Trace must not
infer geometry correctness from a successful viewer load or from file presence.
