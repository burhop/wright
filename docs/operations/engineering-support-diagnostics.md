# Engineering Support Diagnostics

Wright can create a small local JSON support file for a workspace or one Rivet
scenario. Nothing is uploaded automatically. The preview is the authority: an
export is unavailable until the current user reviews that exact preview and
checks the confirmation box.

## Create a support file

1. Open the Rivet engineering report that needs diagnosis.
2. Under **Local support diagnostics**, choose **Preview support file**.
3. Review every included, omitted, redacted, or truncated category and any
   inspect-before-retry recovery.
4. Check the confirmation for this current preview.
5. Choose **Export reviewed support file**. The JSON file is downloaded
   locally once. A second export requires a fresh preview.

A preview expires after five minutes, is bound to the current principal,
workspace, optional session/scenario scope, state identities, and snapshot
digest, and is held only by the running Wright process. Restart, expiry,
replay, cross-workspace use, or changed catalog/model/workflow/scenario identity
invalidates it.

## What the file contains

The allowlist contains product/data-schema identity, active public catalog
identity, bounded state counts, content/evidence digests, logical storage
availability, provider kind/status/identity digest, stable failure and recovery
codes, cleanup truth, generation/expiry times, and redaction facts. Material
identity digests are separate from timing and resource observations.

The preview always names excluded categories. Raw engineering payloads,
artifact bodies, proprietary model features, prompts, request/response bodies,
database rows, environment values, credentials, tokens, cookies, commands,
arguments, private filenames/paths, local endpoints, process configuration,
tool results, and raw logs are omitted or redacted. Logs, traces, HTTP errors,
the on-screen preview, and the attachment use the same safe identity boundary.

Limits are 2 MiB per export, 2,000 records, 4,096 characters per safe string,
100 values per collection, 64 provider summaries, 64 failure summaries, and 32
category records. Serialization and policy errors fail closed.

## Interpreting recovery

- `INSPECT_BEFORE_RETRY` means cleanup is not proven clean. Inspect the named
  local provider boundary before running anything again.
- `REVIEW_PROVIDER_STATUS` means the operation ended cleanly but its provider
  result still needs review.
- `DIAGNOSTIC_PREVIEW_STALE` means durable engineering identities changed;
  create and review a fresh preview.
- `DIAGNOSTIC_PREVIEW_EXPIRED` means the five-minute grant ended.
- `DIAGNOSTIC_EXPORT_DENIED` covers replay, wrong principal/workspace/digest,
  invalid token, restart, or an otherwise unusable preview without disclosing
  which private comparison failed.

The attachment is inert evidence. It contains no reusable Wright authority and
cannot start an MCP, model, application, printer, spindle, robot, heater, PLC,
or other physical equipment. Review it again before sharing it outside the
organization; Wright does not select a recipient or support destination.
