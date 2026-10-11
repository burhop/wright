# Initial resource preflight — 2026-09-30

T003 records availability; full qualification belongs to T043/live proof tasks.

| Resource | Observed evidence | Consequence |
|---|---|---|
| Python | Existing .venv imports core and pytest | Foundation tests can run without installation |
| Frontend compiler | node v25.2.0, npm 11.6.2, apps/web/node_modules present | Existing fixed toolchain available; builder qualification still required |
| Git Bash | Installed D: path successfully runs prerequisite script | No Spec Kit setup blocker |
| Docker | Approved read-only daemon query returned 28.5.1 | Clean-container checks possible; sandbox needs approved Docker calls |
| Hermes | /health HTTP200; authenticated /v1/models HTTP200 advertises hermes-agent | Existing configured API usable; actual generation/effective scoped role still unverified |
| Hermes config | Existing host .env has configured API credential; read through authorized escalation without displaying/copying it | Local process environment needs explicit config location; no repository secret |
| Blender | Port9876 not accepting a connection | Need an owned independent provider/host start and safe qualification later |
| External slicer | Retained upstream source exists under feature-081-live/sources/bambu-p1s-mcp | Reuse/qualify separately; historical configuration is not new proof |
| AgentCAD | Three retained pinned bootstrap source directories exist | Need exact selected binding/live qualification |
| OASiS | Existing wright-oasis-campaign Docker container running | Protected unrelated runtime; create an isolated proof runtime rather than mutate it |
| API/UI | Listed local demo/editor ports have no accepting listener | Start owned feature services later; no served-build assertion now |

Initial unauthenticated models query returned401; supplying the existing configured
credential returned200. Credential values were never printed or saved. Health
does not prove model generation or authoring-scope enforcement.

Read-only Docker inventory also shows other existing campaign/data-vault services.
None is Feature 083 owned; no service was killed/restarted or campaign call dispatched.
