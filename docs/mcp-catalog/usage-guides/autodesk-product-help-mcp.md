# Autodesk Product Help MCP usage guide

Recorded 26 October 2026. Status: historical protocol and read-only product-list
qualification plus bounded ARM64 first-contact observations; no customer-route provider-call acceptance.

## Identity and sources

Official service: [Autodesk Product Help MCP documentation](https://help.autodesk.com/view/ADSKMCP/ENU/?guid=ADSKMCP_KnowledgeMcp_autodesk_product_help_mcp_server_html).
Catalog ID `autodesk-product-help-mcp`; public Streamable HTTP endpoint
`https://developer.api.autodesk.com/knowledge/public/v1/mcp`.
See the [setup recipe](../mcp-server-setup-recipes.md#september-curation-qualification-recipes)
and [native Windows qualification](../evidence/windows-qualification-2026-08-13/autodesk-product-help-mcp-windows-qualification.json).
The historical server identified itself as
`autodesk-knowledge-public-v1-mcp-server` version3.0.2, MCP2025-11-25.
Rediscover current tool schemas rather than assuming a hosted version is frozen.

## Installation and readiness

Register/select the existing remote catalog entry in Wright, review its actual
installation/readiness plan, and enable it for the intended workspace. It needs
no Autodesk desktop application, local MCP package or catalog-listed credential.
Network access and the existing HTTP MCP transport are required. Publisher terms
remain an independent gate; do not infer acceptance from anonymous connectivity
or bypass a blocked Wright action. The catalog's ARM64 support is documented,
not independently tested by the historical Windows/x64 receipts.

## Verified workflows and successful calls

The linked historical qualification initialized the exact endpoint, listed tools
and called `get_available_products` with `{}`. September's setup recipe also
records the call through Wright's prefixed gateway tool and checking that Fusion
is present. Inspect the actual structured response and retain its observed server,
tool contract, arguments and response identity. This is read-only documentation
access, not a CAD artifact, model measurement or engineering validation.
`search_help_content` was listed; this guide does not newly qualify that tool.

## Pitfalls and recovery

A connection or tool listing alone does not establish a successful product-list
call. Record network/authentication/terms diagnostics distinctly. On a read-only
request timeout, preserve the first attempt and follow the gateway's existing
bounded recovery; do not alter endpoint URLs to evade readiness. No provider
bug is established or submitted by this guide.

## Validation, authority and limitations

Check the returned product names rather than treating transport success as the
expected answer. No dimensions, units, printability, physical acceptance or CAD
creation claim follows from documentation discovery. User-visible setup and the
agent gateway must both be observed; a direct host probe is not customer success.
New synthetic-beta observations will be linked from the campaign when completed;
this entry does not assert their outcome.

## Maintenance

Retain historical platform/version scopes when adding new evidence. Never put
credentials, browser cookies or private account data in this guide.

## Private ARM64 first-contact evidence — 26 October 2026

The clean disposable ARM64 technical probe initialized the hosted service as
`autodesk-knowledge-public-v1-mcp-server` version 1.0.12 and called
`get_available_products({})`, returning a non-error product list including Fusion.
This is an observed service identity, not a claim about its latest release.
[Exact provider contract and returned data](../../../artifacts/first-contact/synthetic-beta-002/receipts/hosted-readiness-001.json)
remain separate from customer outcomes.

The original private native wheel `3593ac77443b…` also listed and called the provider
through its configured stdio bridge after observation. Actual Hermes 0.19.0 tool
discovery initially returned no tools because its optional MCP SDK was absent;
installing the same-version `hermes-agent[mcp]` extra supplied MCP 1.26.0. Its stdio
subprocess also needed the existing nonsecret WRIGHT_HOME binding. With that
binding, actual Hermes discovered 14 tools and invoked the read-only product-list
handler. [Technical setup and source receipts](../../../artifacts/first-contact/synthetic-beta-002/receipts/hermes-mcp-call-001.json)
record the actual tool, arguments, response hash and scope. These post-observation
operations are not customer success, CAD validation or human publisher acceptance.

The first synthetic customer registered the provider but obtained no product list.
Later investigation found Wright's old installer submitted publisher-completion
`true` automatically. That record does not establish human completion. The
corrected private candidate defaults to false and requires an explicit factual
assertion followed by a new plan. A synthetic customer cannot invent it. Preserve
that publisher gate even though the catalog correctly says no MCP login is needed.
No provider bug was established or submitted. Browser chat requires a separately
running Hermes HTTP gateway; terminal MCP readiness does not establish it.

## Human-prerequisite-supplied customer follow-up

The human independently confirmed publisher completion for Autodesk Product Help
for this testing. A fresh customer truthfully recorded that fact, obtained
Validation passed, and reopened the workspace with the provider active. It also
inspected displayed product excerpts including Fusion/FSN. Its
[original report](../../../artifacts/first-contact/synthetic-beta-002/session-records/gh2-authorized-beginner-web/report.json)
and [independent assessment](../../../artifacts/first-contact/synthetic-beta-002/session-records/gh2-authorized-beginner-web/verification.json)
are retained. The overall audit is REJECTED because no identifiable invocation /
result trace independently proves the claimed provider call. Displayed excerpts
alone do not establish provider provenance; not_reached is an evidence gap, not
proof that no call occurred. No customer first-result success is credited.

Saving the raw response and brief encountered workspace_write_approval; neither
file was retained. The checklist persisted via Workspace Settings. This supports
unclear permission recovery in the observed path, not a claim that no permission
mechanism exists elsewhere. Preserve this distinction before expanding coverage.
The human fact grants no SteveCAD access, new terms, engineering review or
physical authority. No provider defect was established or submitted.

## Native first-contact workflow retrieval — 28 October 2026

Customer080 on private native candidate079 installed the existing hosted entry
and ran its saved Fusion preparation workflow. The exact native run records one
successful `get_available_products` call and four successful `search_help_content`
calls with explicitly selected `en_US`, `product_code=FSN` and five results per
query. No desktop CAD application was installed. The declared workflow retrieved
export and additive-preparation documentation; this is documentation evidence,
not geometry, printer qualification or engineering acceptance.

The workflow then failed `TASK_BLOCKED`: its authored prompt demanded an in-task
saved-file receipt, although Wright publishes the configured final response after
accepting a completed envelope. No reference note was saved. Do not install an
imaginary Autodesk writer or infer a provider defect. The prospective1.2.9
instruction clarification keeps old accepted instructions and the original
failure unchanged; its installed behavior remains unobserved.

[Exact native-run/call/timing reconciliation](../../../artifacts/first-contact/synthetic-beta-003/receipts/gh3-docs-newcomer-080-run-reconciliation.json)
and [readable customer outcome](../../../artifacts/first-contact/synthetic-beta-003/run-details/gh3-docs-newcomer-080/result.md)
retain the full-visit scope and limitations. Five successful tool intervals total
10.417 seconds inside a297.614-second failed run; the remainder includes model,
recording and orchestration, not isolated provider latency. The original beta
feedback remains unreviewed and no completed customer first result is credited.

## Prepared native publication — 28 October 2026,03:12 EDT

Fresh maker082 authored a new profile1.2.9 workflow, executed three successful
`search_help_content` calls and received an indexed Markdown reference. Native
run `140ab9ca3efe488bb88422e7190eb8f8` completed in162.282seconds. The publication
event, result record, API-read note and filesystem copy match at10,074bytes and
SHA256 `11b3396ce8f14ed62d5936643eff255df23e0cadd8c3b246d832817c945ffccc`.
The customer opened the readable note and found it and the workflow after
workspace reopening. All eight Markdown citation URLs occur in the retained
provider response text; this does not independently verify every procedural
claim or upstream publication/revision date.

[Exact source/run/publication reconciliation](../../../artifacts/first-contact/synthetic-beta-003/receipts/gh3-docs-prepared-082-run-reconciliation.json)
and the [actual published reference](../../../artifacts/first-contact/synthetic-beta-003/run-details/gh3-docs-prepared-082/fusion-print-preparation-reference.md)
preserve this narrow scope. The599.354-second prepared visit excludes install
preparation, remains unreviewed and is not a causal timing comparison, full
first-contact journey or CAD/engineering acceptance. Chat-to-Run navigation and
missing retrieval dating remain. The old080 failed record and1.2.8 source remain
unchanged; do not overwrite them with this success.
