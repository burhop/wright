# Isolated Windows engineering pilot

This is a source-development pilot, separate from the experimental OpenAI
desktop panel. The Windows agent owns installation and actual engineering
qualification. The GB10 integration agent repairs shared code and develops the
desktop UI. Both use the accepted Wright workflow and durable run mechanisms.

The first Windows pass used dev `40b6270ec5e9bc1c1e9c61c20a0bf50269f35b82`.
Its API/UI started, but its shared Hermes profile selected Sol and the browser
walkthrough stopped at the unlock screen. Those observations do not qualify
Astra, workflow execution, or Roadster reconstruction.

## Keep the existing pilot

Fetch the repair revision into the existing Windows-local repository and review
the diff before advancing its dedicated worktree. Preserve dirty files and the
first-pass evidence. Keep the existing state at
`D:\repos\wright\.local-run\windows-engineering-pilot\state`.
Do not use the mapped drive, GB10 services, SSH, a copied database, or another
instance's credentials. Do not restart unrelated services.

Use a compatible isolated Node from the ranges in
[local setup](quickstart-local.md), then run
`uv sync --locked --all-packages --all-groups --extra runtime` and
`npm ci --engine-strict`.
The Node 25.2.0 first-pass installation does not satisfy the locked test runtime.
Do not replace the global Node installation.

## Separate Astra configuration

In a dedicated PowerShell session, dot-source the pilot's existing
`Enter-Pilot.ps1`, then select a fresh private Hermes root under the pilot state:

```powershell
$env:HERMES_HOME = Join-Path $pilotState 'hermes'
$env:HERMES_PROFILE = 'windows-engineering-pilot'
$env:WRIGHT_HERMES_PROFILE = $env:HERMES_PROFILE
hermes profile create windows-engineering-pilot --no-alias --no-skills
```

Run profile creation only once, after checking that this new profile does not
already exist. Do not clone a shared profile or switch the user's active profile.
Inspect the installed Hermes version and `profile create --help` before applying
these flags; an unsupported version is a prerequisite failure, not permission to
use the shared profile. The official profile resolver should place this profile
under `$env:HERMES_HOME\profiles\windows-engineering-pilot`.

Configure only that profile's `config.yaml` with:

```yaml
model:
  provider: openai-codex
  default: gpt-6-astra
  api_mode: codex_responses
agent:
  reasoning_effort: high
fallback_model: null
```

Keep any generated profile configuration needed by the installed Hermes version.
Explicitly select `openai-codex` / `gpt-6-astra` for each enabled auxiliary role
in that version, including compression, vision, web extraction and title
generation. Disable unused background roles. These are requested settings,
not proof that requests used that model. Do not infer helper routing from a
dropdown or successful primary response.

Use the installed Hermes sign-in flow for this profile:

```powershell
hermes -p windows-engineering-pilot auth add openai-codex --no-browser
```

Personal login and consent are the user's actions. Never copy tokens from
Codex, the shared Hermes profile, or GB10. If already-authorized credentials are
available through this installed Hermes version's supported resolver, qualify
that path without copying or logging them.

Start a dedicated local Hermes API on an unused port, for example 28642.
Set `API_SERVER_ENABLED=true`, `API_SERVER_HOST=127.0.0.1`,
`API_SERVER_PORT=28642` and a newly generated private `API_SERVER_KEY` in
that process's environment, then run
`hermes -p windows-engineering-pilot gateway run`.
Read the key from the pilot's private credential file; never put it in a
command argument, checked-in configuration or evidence.

In the Wright API launcher, select the same profile and set:

```powershell
$env:HERMES_API_BASE_URL = 'http://127.0.0.1:28642'
$env:HERMES_API_DISABLE_DEFAULT_CANDIDATES = '1'
$env:WRIGHT_WORKFLOW_MODEL_TRANSPORT = 'hermes-model-sdk'
$env:HERMES_CONFIG_PATH = Join-Path $env:HERMES_HOME 'profiles/windows-engineering-pilot/config.yaml'
```

Set `HERMES_API_KEY` to the dedicated API's key through private environment
loading. Set `HERMES_ROLE_RUNTIME_ROOT` and `HERMES_ROLE_PYTHON` to the **actual
Windows-local installed Hermes runtime and its Python executable**. Do not
install Hermes in Wright's virtual environment or invent paths from GB10.
Clear inherited endpoint/model/key overrides in this dedicated process as in
the first-pass launcher. Remove its hard-coded `HERMES_API_BASE_URL=...8642`;
it must not overwrite the isolated route.

The browser authoring chat uses this dedicated Hermes API. Select and confirm
Astra for its new session through Wright's existing session model control
(`POST /api/agent/model` with the exact `session_id`, provider and model).
Require `session_locked=true` before authoring; inspect the installed gateway's
lock receipt. Do not change a global/shared selection to satisfy this check.

Workflow AI steps use the existing model-only SDK adapter. Its worker resolves
the same named profile, rejects a changed model/configuration, captures actual
SDK requests, and cannot execute engineering tools. Wright's bounded runtime
executes declared tool proposals through its gateway. Keep HTTP and SDK route
evidence distinct. A successful chat does not qualify workflow execution.

## Readiness sequence

1. Start only the dedicated pilot services. Require normal `/api/health`;
   direct source launches intentionally return 503
   `native_lifecycle_unavailable` at `/api/runtime/identity`. Do not forge a
   manager challenge. Keep API authentication enforced.
2. Open the actual browser UI in a fresh context. Unlock with this instance's
   private Wright token using the [local token flow](quickstart-local.md#browser-access-with-enforced-authentication).
   Before unlock, no protected tools/sessions/settings initialization should
   occur. Check the ordinary workspace page after login.
3. Register a fresh workspace through the normal UI and enter via **Workflows**.
   Create, save and reopen a small source/diagram. Record workspace, session,
   source revision/digest and screenshot; component tests alone do not qualify it.
4. Author and refine a small workflow using the locked Astra chat. Retain actual
   Wright-submitted request evidence and gateway lock/runtime receipts.
   Separately run the following from the configured Wright environment to probe
   the execution route and make one bounded model-only request. Use a fresh
   output directory for every attempt. Its success is a route probe, not
   engineering acceptance:

   ```powershell
   .venv\Scripts\python.exe scripts/qualify-pilot-model.py `
     --expected-provider openai-codex --expected-model gpt-6-astra `
     --prompt-file scripts/pilot/model-route-probe.txt `
     --output "$pilotState\readiness\astra-route-01"
   ```
5. Run a small workflow with a declared human checkpoint. Save its frozen
   model/instruction/tool configuration. Reopen and resume the same durable run.
   Changing the model, SDK or profile must hold continuation before inference.
   Model configuration never grants human review or external-action approval.
6. Use the existing Windows pocket-defect fixture and qualified independent
   producer/measurement MCPs. It was **not included** in the handoff: locate and
   hash the original local files, then copy only selected inputs into a fresh
   workspace. Preserve original requirements. Prove artifact transfer/readback,
   a measured defect, a bounded correction, and revalidation of the exact new
   artifact. A nested provider error must hold dependent work despite outer
   transport success. Do not substitute a fake provider or lower tolerances.
7. Inspect all observed authoring, execution, helper, correction and recovery
   requests. Record requested model, frozen route, confirmed transport model and
   reported upstream revision separately. Record any unobservable Hermes-internal
   calls as unverified. No hidden model fallback is acceptable.

Retain each failed attempt and uncertain effect. Reconcile durable receipts
before any retry; never replay completed mutations. Prove shared changes with a
substantially different existing workflow, preserving its inputs and requirements.
Use the ordinary browser view when the desktop panel is awkward; point both at
the same local API/workspace, and verify identities before operating.

**Roadster reconstruction remains blocked until this sequence passes on
Windows.** No previous model, retrospective cleanup, historical approval or
old run is implicitly authorized for reuse.
