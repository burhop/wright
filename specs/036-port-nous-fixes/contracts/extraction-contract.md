# Extraction Contract

## Inputs

- Current branch: `codex/port-nous-good-fixes`
- Source branch: `nous_hackathon`
- Candidate folder: `scratch/nous_hackathon_candidates/`

## Required Behavior

1. Do not merge `nous_hackathon`.
2. Review candidate files by original repository path.
3. Apply whole files only when the diff is free of excluded prototype behavior.
4. Apply mixed files only by selected hunks or equivalent manual edits.
5. Leave rejected files documented in the task notes or final summary.

## Exclusion Rules

The final applied source diff must omit:

- Stripe or billing API/UI behavior
- Nemoclaw-specific expansion behavior
- Hackathon Docker, scripts, Makefile targets, or stack configuration
- Generated presentation, video, image, or temporary Office lock output
- Paid-demo MCP server code
- Prototype-only model branding or hardcoded demo labels

## Acceptance Evidence

Each accepted change group must provide:

- Candidate path(s) reviewed
- Live path(s) changed
- Reason the change is reusable
- Targeted validation result or blocker
