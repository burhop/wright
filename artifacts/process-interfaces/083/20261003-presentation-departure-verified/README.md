# Exact presentation cleanup on browser departure

The shared workspace host releases an exact saved or preview presentation using
the existing authenticated owner endpoint and a bounded keepalive request when
the browser document leaves. Closing a presentation does not execute, resume,
cancel or approve its process. Ordinary tab unmount and StrictMode retain their
existing behavior; cached documents keep their mounted view. Pending opens are
released if their reply arrives while the document can still execute cleanup.

The actual saved Heat and Focus-wheel interfaces each survive three reloads,
with prior presentation closure checked independently in the backend. Navigating
away releases the final views. All 57 retained run/output/saved-bundle files and
UI authoring/revision records are unchanged. Twelve browser checks pass with no
browser diagnostics. The walkthrough was entered from existing exact saved links;
normal workspace authoring entry is covered separately in retained prior proofs.

See [walkthrough](workspace-walkthrough/report.html), [scope](checked-scope.json),
[frontend tests](affected-frontend-tests.txt) and [backend tests](authority-tests.txt).
The 63 frontend and 73 backend counts overlap prior checks; do not add them to
older counts. Private traces contain authentication and are deliberately excluded.

The first browser launch was denied before navigation (spawn EPERM), so its
retained stop has no screenshot and does not meet the generic image-interaction
validator. The fresh walkthrough passes the structure validator. The first
typecheck fixture typing error is also retained, followed by the passing check.
Abrupt termination and browser back-forward-cache recovery remain unqualified.
