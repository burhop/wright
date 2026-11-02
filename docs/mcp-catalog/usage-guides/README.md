# MCP usage guides

Agents should read a provider's setup recipe, qualification evidence and usage
guide before installing or using it. Create or update a guide for every server
installed or used, and link it from this index. Start with the
[shared template](_template.md). At installation, record known prerequisites,
observed versions and connection/protocol results; leave engineering capabilities
unverified until actual use proves them. Update the guide after a verified lesson,
so future agents can reuse successful inputs and avoid known mistakes.

The guide is durable repository knowledge. Keep setup recipes, catalog entries
and evidence as their existing owners, and link them rather than duplicating
them. This practice applies to every MCP provider and does not imply that every
catalog entry has been exercised. Do not save credentials, OAuth tokens, one-use
download tickets or private account state in a guide.

## Reusing installation improvements

For first-hour usability work, prefer suitable hosted providers that do not need a
native engineering application. Record account, authorization and access
requirements explicitly; hosted does not mean immediately usable. Use local
applications where the engineering job requires them.

When an observed setup obstacle is corrected, carry the lesson into this
provider's linked setup recipe and guide, and into Wright's shared onboarding or
readiness mechanism when the defect is shared. Record the affected versions and
platform, exact supported setup, prerequisite checks, recovery, observed timing
and evidence. Distinguish source fixes, packaged candidates, observed installed
behavior and release availability. A laboratory-only launcher, cached download or
prepared application does not establish a fast first-time customer installation.
Keep credentials out of reusable instructions and images.

## Available guides

- [Bambu P1S MCP offline slicing](bambu-p1s-mcp.md): pinned provider, explicit profile requirements and ARM64 qualification limits; no printer access.

- [Playwright MCP](playwright-mcp.md): pinned bundled browser provider and bounded desktop gateway qualification.

- [OASiS Open FEM Agent](oasis-open-fem-agent.md): retained Linux x64 solver/gateway evidence, selected backend setup and fresh GB10 qualification limits.

- [Casys CalculiX MCP](calculix-mcp.md): recorded static solves, exact resources,
  selected-container setup and host-specific qualification limits.

- [ROSBag MCP](rosbag-mcp.md): original Robot Tracking Diagnosis data, offline
  bag inspection and measurement ownership; fresh GB10 ARM64 provider proof.

- [SteveCAD](stevecad-mcp.md): editable CAD, revision-bound measurements, returned
  images, known authoring mistakes and carefully evidenced bug reports. The
  [first-contact addendum](stevecad-mcp-first-contact.md) records account gates and
  separates the new synthetic research from CAD qualification.
- [KiCad MCP](kicad-mcp.md): native CM5 IO Board mounting references, container
  paths, backend result checks and observed mechanical-export limitations.
- [Blender MCP](blender-mcp.md): actual STEP-derived geometry import, native
  presentation renders, safe-mode operators and selected-host capability limits.
- [AgentCAD MCP](agentcad-mcp.md): actual standard STEP measurement/export,
  separate written-mesh validation and connected native rendering handoff.
- [FreeCAD MCP](freecad-mcp.md): historical box/export qualification and isolated
  ARM64 solid-construction qualification, with explicit platform and scope limits.
- [OASiS MCP](oasis-mcp.md): isolated scikit-fem backend readiness, actual
  Poisson field output, independent checks and explicit engineering limits.
- [Generic shell/file MCP](mcp-shell-server.md): scoped transfer, transient
  credential handling, connected input envelopes and explicit result checks.
- [ROSBag MCP](rosbag-mcp.md): historical offline known-message retrieval,
  exact bag/clock conventions, pinned SDK and unverified native-platform limits.
- [Setup recipes](../mcp-server-setup-recipes.md): installation and qualification
  guidance for previously attempted providers. These remain the existing owner
  of setup instructions; do not duplicate or silently supersede them.

## Required contents for a provider guide

1. Provider/server identity, official documentation, observed version, date and
   environment; separate native, container and live-service qualifications.
2. The engineering jobs actually proved, prerequisites and capability limits.
3. A minimal successful sequence, exact schemas or discovery steps, units,
   coordinate conventions and artifact handoff. Link real input/output evidence.
4. Resource/revision identities, freshness checks, validation methods and what
   tool success does and does not establish.
5. Known mistakes and bounded recovery. Distinguish explicit no-effect errors
   from uncertain submissions; reconcile an existing handle before retrying.
6. Credential redaction, download handling and external-action authority.
7. Bug triage and the supported reporting route; known report IDs and status.
8. Unverified capabilities and the next smallest useful qualification.

Use labels such as **verified**, **documented**, **proposed** and **unverified**.
Do not turn a vendor-specific observation into generic runtime policy or claim
that a mock proves the live provider. Keep provider protocols external to Wright.
Update the chronological [problem log](../testing-problem-log.md) when useful;
the guide is the reusable account of what worked.

## Bug-report evidence

Before reporting, compare the current documented contract with the exact request
and observed response. Exclude our invalid code, wrong units, coordinates,
authentication, unsupported schemas, stale revisions and missing prerequisites.
Use a small owned reproduction when safe and necessary; do not duplicate an
uncertain mutation. A suspicion remains a draft until the evidence supports it.

A useful report contains: concise symptom; expected and observed behavior;
minimal source and steps; provider/client/platform versions and observation time;
exact resource/revision/build identifiers; relevant redacted requests, responses,
errors and screenshots; reproducibility and impact; and a bounded workaround if
known. Inspect the reporting payload for confidential source and credentials.
Record the submitted report ID and acceptance state. A queued accepted report is
not permission to submit a duplicate. Feature requests are separate from bugs.
