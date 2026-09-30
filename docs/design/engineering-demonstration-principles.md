# Wright engineering demonstration principles

**Decision recorded:** 21 September 2026.

**Authority:** the user's explicit clarification of Wright's purpose and agreement
to retain that clarification for future work.

## The purpose we must demonstrate

The [workflow platform vision](workflow-platform-vision.md) records the broader
product direction. The examples below demonstrate meaningful connected work;
they do not prescribe a required workflow structure. Manufacturing is an early
reference, and other workflows can use different arrangements and outcomes.
Vendor implementation belongs in independent integrations. Preserve the
distinction between demonstrating those tools and making their implementation
part of Wright.

**Wright enables an engineer to apply multiple existing engineering tools through
an extended, connected process to accomplish an overall engineering job. The
demonstration of those tools through MCP servers is fundamental, not incidental.**

An isolated image-to-CAD, text-to-CAD, or AI-prepared solver job illustrates one
capability. Wright's demonstrations must show the larger process: how several
capabilities work together, how their actual outputs move between stages, and
what useful engineering outcome the combined process achieves.

The user's illustrative chain is:

> Image or concept → CAD design → FEA strength assessment → manufacturing drawing.

Each stage makes a distinct engineering contribution. The analysis uses the
actual design, and the manufacturing deliverable must correspond to the reviewed
design revision. When assessment requires a change, retain the connection between
the revised design, its reassessment, and downstream deliverables. This example
expresses the intended pattern; it is not a claim that a particular integration
has already been qualified.

## What makes a strong example

A first-time engineering user should be able to answer:

1. **What overall job am I accomplishing, and why does it matter?** Describe a
   recognizable design, analysis, testing, or manufacturing-preparation need.
2. **Which existing engineering tools do the substantive work?** Name the
   applications/capabilities and the MCP servers that expose them. Explain each
   tool's engineering contribution, not just its transport or API details.
3. **What passes from one tool to the next?** Identify the actual geometry,
   model, mesh, loads, results, parameters, or other engineering information the
   next stage consumes. A written claim that a previous stage succeeded is not
   an artifact handoff.
4. **How does each stage advance the job?** Show necessary transformations,
   assessments, choices, and any appropriate revision or human review. Several
   independent tool demonstrations placed next to each other are not a chain.
5. **What useful result can I inspect and use?** Make the resulting design,
   analysis, drawing, manufacturing package, or supported engineering decision
   easy to find and understand. Intermediate inputs and outputs should also be
   readily inspectable.
6. **Why is the connected process useful?** Explain the benefit of coordinating
   the tools and carrying engineering information across them, rather than
   merely showing that each tool can run in isolation.

Do not impose an arbitrary number of nodes or servers. Multiple tools and
meaningful engineering dependencies matter; count alone does not. Not every
example needs CAD, FEA, a drawing, a fully autonomous loop, or a proven physical
root cause. It does need an overall engineering purpose and a substantive chain
of existing tool capabilities serving that purpose.

## What does not satisfy this purpose by itself

- Splitting one calculation or analysis into many workflow blocks.
- Padding a process with format conversion, file inspection, logging, checks,
  approvals, or report writing. These can be necessary supporting steps, but do
  not replace the substantive engineering chain.
- Counting MCP calls or wrapping a custom script in an MCP server and treating
  that alone as demonstration of multiple existing engineering applications.
  Custom integration and calculations are allowed; they must not silently
  substitute for the tool capabilities the example claims to demonstrate.
- Producing many valid files, a polished report, or a green execution status
  without demonstrating the connected engineering work.
- Adding a plausible story, a new title, or an acceptance threshold to an example
  whose underlying tool chain still does not advance a larger engineering job.
- Adding tools merely to lengthen the chain or showcase a catalog entry without
  an engineering reason for its participation.

A conclusion that more evidence is needed can be legitimate engineering. It is
not automatically a compelling end-to-end product demonstration. Assess what
the connected tools actually accomplish before making that claim.

## Show the tools without making the user read software internals

The earlier request for engineer-friendly language did **not** mean hiding or
de-emphasizing the engineering tools. Show which engineering application is
performing each operation, what it receives, what it produces, and how its result
affects the next stage.

Keep raw JSON, GUIDs, digests, connection plumbing, campaign-runner details, and
similar diagnostics out of the default engineering explanation. Retain technical
details on demand. Tool capabilities and meaningful handoffs belong in the main
story; implementation noise does not.

A tailored [process UI](process-apps.md) can make this work easier to carry out
and inspect. Its working view and the flowchart must refer to the same accepted
process, exact outputs, decisions, and evidence. Demonstrate the useful user
journey as well as substantive tool contributions. A polished generated interface
does not replace engineering evidence or establish unrestricted process support.

## What we learned from the Robot example

The current floor-seam example performs real tool calls and useful analysis:
prepare and inspect motion recordings, calculate deviations, produce plots, and
write an evidence-linked diagnosis. Its supplied analysis procedure does much
of the substantive numerical work.

However, it mainly expands one motion-analysis activity into several steps and
ends with a recommendation for another experiment. It does not strongly show
several existing engineering applications contributing different capabilities
to an extended engineering solution. It is therefore a weak demonstration of
Wright's central value in its current form, even if its files and calculations
pass their applicable checks.

It may still be valuable as an analysis example or runtime regression test.
Neither improved labels and plots nor a more persuasive explanation makes it a
strong multi-tool demonstration without evaluating the underlying process.
The earlier [Robot engineering brief](../workflows/mobile-cart-tracking-engineering-brief.md)
explains the analysis but is not evidence of product-demonstration suitability.

## Apply this to the existing 30 examples without wholesale replacement

The user asked to align the existing examples, **not completely rewrite all 30**.
Preserve useful scenarios, tools, data, working stages, and retained evidence.
When reviewing an example, identify its engineering objective, existing tools,
actual handoffs, and final deliverable before proposing changes.

Use the smallest justified adjustment:

- Clarify the presentation when a meaningful tool chain already exists.
- Propose a focused connection or stage change when a specific missing handoff
  prevents an otherwise useful chain from accomplishing its objective.
- Identify a narrow technical test honestly when it lacks demonstration value;
  do not disguise it as a flagship example or automatically replace it.

Material changes to the engineering assignment or requirements need explicit
agreement. Do not invent requirements, rewrite frozen evidence, or launch a
blanket redesign under the label of alignment.

## Keep product suitability separate from campaign correctness

`30/30/30/30` records datasets, actual runs, complete output sets, and validated
outputs under the campaign's defined scope. It does **not**, on its own, prove
that all 30 examples are compelling demonstrations of Wright.

Preserve the existing counters, baselines, run records, review authority, and
validation rules. Describe demonstration suitability separately. A valid
technical test can be a weak product demonstration; a compelling proposed
process is not a verified execution.

For future example reviews, record at least: **engineering objective; existing
tools and MCP servers; ordered substantive stages; actual artifact handoffs;
engineering outcome; demonstration gap and smallest proposed adjustment**.
Do not mark cases as reviewed or qualified without inspecting them.

This decision records product direction. It does not start or stop a runner,
activate a goal, approve engineering results, authorize a redesign of all cases,
or change permissions for physical actions, publication, push, or merge.
