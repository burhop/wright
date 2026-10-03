# Saved interface theme and reconnect verification

Both actual model-created saved engineering interfaces now inherit Wright's
selected light/dark colors and browser-control color scheme. Each embedded page
reconnects after frame reload with the same saved UI, run and exact outputs.
Eight served checks pass; the Heat interface has 18 results and the wheel has 19.
The 57 retained output/run/bundle files and authoring records are unchanged.
No generation, process start, engineering decision or saved preference change occurred.

See [walkthrough](workspace-walkthrough/report.html) and [scope](checked-scope.json).
The original theme mismatch remains in retained-product-stop. The separate
global-response assertion stop remains in retained-harness-stop; that assertion
accidentally selected a retained hidden Heat tab's response. The final check
inspects the actual visible frame's own backend context.

The existing bounded token bridge now includes only light/dark color-scheme
values. Origin, source window, nonce, exact presentation and generation guards
remain intact. Unsupported values and generic tool authority stay unavailable.
An older runtime ignores the extra token, preserving handshake compatibility
but lacking the new control styling until upgraded.

Current frontend checks pass 47 cases, scoped client checks 94, backend host and
authority checks 71, and packaging 3. Counts overlap earlier evidence. App
TypeScript passes. The initial temporary-directory permission failure is retained
as JUnit; a fresh workspace-scoped test root passes. Current packaging compares
the shipped fixed runtime and manifest bytes to source. Older installed browser
evidence is not relabelled as current; full editor/accessibility, engineering,
provider/migration and final acceptance remain open. Private traces are excluded.
