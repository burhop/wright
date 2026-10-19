# Connection management parity audit

17 October 2026; source `267b0bb9`, installed prototype **0.15.0** unchanged.
This distinguishes actual shared mechanisms from legacy UI/API surface area.
It does not reduce the [submitted goal](integration-completion-goal.md) or declare
the remaining required authentication journey complete.

| Journey | Existing shared implementation | Native prototype status |
|---|---|---|
| Catalog setup | Reviewed install plans, onboarding, protocol validation and workspace enablement owners | Exposed; bounded actual-owner qualification retained |
| Custom public endpoint / literal command | Import preview → exact draft/plan → operator review/apply → protocol check → selected workspace enable | Exposed and locally qualified; no implicit tool grant |
| Provider lifecycle and tools | Shared lifecycle/registry owners | Start, stop, uninstall, per-tool switches and workspace disable qualified; saved status recovers lost replies without replay |
| OAuth | Existing MCP SDK presentation/state/PKCE and credential owner | Scoped private presentation exists; real Windows callback, personal sign-in and saved authentication remain unverified |
| General configuration import | Recognizes Claude/VS Code/plain JSON; intentionally discards source and environment/header values | Not exposed as a full import. Parsing a file does not establish runnable configuration |
| API-key/private credentials | Existing Wright HTTP credential API and ToolCard form; stored values are not returned by the status API | No secret-value tool port. A private operator UI/authentication handoff must be qualified before claiming native parity |
| Provider upgrades | Existing version-check/update endpoints and legacy UI | Recorded installed version can be inspected; automatic upgrade is not exposed or qualified |

## Observed boundaries

The existing [configuration importer](../../packages/tool_registry/src/tool_registry/config_import.py)
keeps requirement names and whether a value was supplied, replacing environment
and header values with redaction markers. A pure existing-owner invocation with
an unused synthetic value confirmed that both a credential value and an ordinary
`RUN_MODE` value are absent from the normalized preview. No provider, network,
plan/application, secret store or workflow was used. Receipt and source hashes:
`/tmp/wright-desktop-completion-qualification-20261017/connection-parity-pure-preview.json`.

The [plan builder](../../packages/tool_registry/src/tool_registry/install_plans.py)
retains command/arguments/endpoint and credential requirement names for an import;
the [registration adapter](../../packages/tool_registry/src/tool_registry/registry_onboarding.py)
creates the server from those fields. This inspection does not establish an
end-to-end mapping for arbitrary environment/header definitions or values.
Adding a JSON textarea to the native panel would not supply that missing proof.
The current typed native endpoint/command requests reject extra fields instead
of silently accepting configuration they do not support.

The [credential service](../../packages/tool_registry/src/tool_registry/services.py)
uses existing local secret storage. Its status response derives field definitions
from `server.env_vars`; imported `credentials_required` names alone are not proof
of the necessary editable definition or runtime header mapping. The legacy
[ToolCard](../../apps/web/src/components/tools/ToolCard.tsx) has the actual direct
Wright HTTP form; the onboarding wizard's credential step reports status and
does not itself implement private credential entry. App-only tool visibility
does not, by itself, prove a private secret-argument channel in the desktop host.

The [legacy version updater](../../packages/tool_registry/src/tool_registry/version_check.py)
contains named-package test shortcuts returning `1.4.0` without an upgrade, and
also substitutes `1.4.0` when a post-upgrade version is not observed. Its normal
commands upgrade a package without an exact target-version plan. These are
source-inspected shared limitations, not provider defects or verified upgrades.
No upgrade command was executed. Do not expose this endpoint as a qualified
native update action or count its success flag as observed version evidence.

## Next actions and constraints

Finish the required real OAuth/operator journey using the existing account and
SDK owner when Windows access and the user are available. The existing SSH alias
is known; the mapped B: drive and stale synthetic callback are not routing proof.
Keep private URLs in the operator UI. Actual callback state/PKCE validation,
saved authenticated state and protocol validation must provide the evidence.

For private credential parity, reuse an authenticated Wright operator form and
the existing secret owner; keep raw values out of conversation/tool arguments and
results. A scoped handoff should bind the exact server/configuration and return
only readiness. Qualify the real host/session/origin boundary before enabling it.
Do not invent a new credential database, general proxy or authentication route.

If full JSON import is included in the next prototype increment, qualify actual
nonsecret environment/header preservation and typed credential references through
the same plan/registration/runtime owners. Unsupported fields require explicit
diagnostics. Continue excluding credentials, grants and runs from portable assets.

If upgrades are included, require an observed target version, current exact
configuration, active-run/call handling and explicit uncertain-outcome recovery.
Reuse reviewed setup/lifecycle mechanisms. Copying the legacy button or changing
the reported version is insufficient. Keep this work separate from independent
provider/catalog testing; no vendor code or provider bug report was added here.

The current prototype's qualified public-command/endpoint and OAuth presentation
remain useful. Full JSON/private/update parity remains explicitly unqualified;
it is not silently inferred from the old Hermes UI. Required Windows delivery,
authentication, repository gates/CI and exact dev deployment remain open.
