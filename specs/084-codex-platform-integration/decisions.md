# Decisions and deferred qualifications

11 October 2026:

- Use the official pinned Python SDK/app-server pair 0.162.1, with low-level public
  `CodexClient`, explicit denial and a clean worker environment. High-level/default
  approval handling does not supply Wright's required controls. Maintain no runtime fork.
- User accepted **Chat pilot exception; gate authoring/workflows**. The harmless
  `collaboration.list_agents` negative control executed without approval. Zero-tools
  remains FAILED; flags, read-only sandbox and empty environments are partial controls.
- Enable chat only through explicit experimental environment settings. Never substitute
  Hermes, another model, credentials or a provider if Codex is unavailable.
- Authorized existing ChatGPT credentials are copied only to private isolated state;
  original bytes remain unchanged and disposable credential copies are removed. Actual
  gpt-6.1-sol/high access and restart continuation passed. API-key billing remains unqualified.
- Inject a core storage port into the adapter. Application composition supplies DataVault;
  do not relax architectural dependency rules to import storage inside agent_adapters.
- Public experimental `dynamicTools` supports the bounded read gateway callback. The
  pinned SDK typed start model omits it, but its public dict interface accepts it. Keep
  this explicit schema/version dependency. This is not external MCP interoperability.
- Freeze actual inspectable redacted configuration/instruction/tool snapshots as well as
  digests. Recheck identity on continuation and hold unknown/rerouted turns without replay.
- Native empty threads have no materialized history before their first turn. A worker's
  acknowledged fresh thread reports empty history locally. A restart with a never-used
  thread remains an explicit unmaterialized-thread limitation; never replace its identity.
- Preserve existing authoring/job ownership. Model-entry routes must check a Codex session
  before consulting a cached Hermes authoring owner. Status/cancel/read of existing jobs
  and saved/common views retain the durable owner.
- A served reload exposed an existing React StrictMode mounted-ref bug. Reset the mounted
  flag when its effect starts; retain the unmount guard and test actual history restoration.
- Legacy tests that switch the default to exercise MCP preflight now create explicit
  non-Hermes session fixtures. Existing sessions must retain their platform under switching.
- Use the latest reviewed Feature 083 editor cases. Older seven-group image-redesign
  assumptions do not match the current four-group palette/blank workflow creation. Preserve
  stopped attempts, original reviewed cases and their exact authority constraints.
- Preserve the baseline exact-byte manufacturing defect: eleven manifest hashes match
  CRLF reconstructions, while committed Linux blobs are LF. Do not normalize protected
  originals, regenerate their hashes or weaken the guard to obtain a pass.

Deferred decisions: released public tool-ceiling support; API-key route/billing; other
models; native external MCP and broader gateway tool catalogs; cost accounting; uncertain
native tool effect recovery; Windows descendant cleanup/ACLs; Linux x64 and Docker lanes.
None changes the accepted chat exception or enables confined authoring/workflows.
